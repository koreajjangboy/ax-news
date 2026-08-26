import logging
import os
import requests
import json
from datetime import datetime
import feedparser
from apscheduler.schedulers.blocking import BlockingScheduler
from supabase import create_client, Client

# 🔑 Supabase 연동 설정
SUPABASE_URL = "https://wafeeknfpzjzngzuphoz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhZmVla25mcHpqem5nenVwaG96Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzE5NDY1OCwiZXhwIjoyMTAyNzcwNjU4fQ.0_whvHCDMcxg5i7EtTWsBGM8RJ_2JhQBR9bbnO7h_XA"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def determine_category_id(title, summary, categories):
    """
    기사의 제목과 요약을 분석하여 제공된 categories 정의에 맞춰 category_id를 결정합니다.
    """
    text = f"{title} {summary}".lower()
    
    for cat in categories:
        if cat["name"] == "AI정책":
            if any(k in text for k in ["정책", "규제", "법안", "법률", "정부", "국회", "장관", "가이드라인", "컴플라이언스", "윤리"]):
                return cat["category_id"]

    for cat in categories:
        if cat["name"] == "도입사례":
            if any(k in text for k in ["도입", "구축", "적용", "사례", "ax", "전환", "고객사", "후기", "활용기"]):
                return cat["category_id"]

    for cat in categories:
        if cat["name"] == "생성형AI":
            if any(k in text for k in ["llm", "생성형", "챗gpt", "chatgpt", "멀티모달", "gpt", "클로드", "claude", "모델", "이미지 생성", "음성"]):
                return cat["category_id"]

    for cat in categories:
        if cat["name"] == "산업동향":
            if any(k in text for k in ["트렌드", "시장", "전망", "산업", "보고서", "분석", "동향", "투자"]):
                return cat["category_id"]

    return categories[0]["category_id"] if categories else None

def process_user_digests(today_str):
    """
    모든 사용자의 user_sources 및 subscriptions를 기준으로 
    이메일 기반 폴더에 HTML 파일을 생성하고 digests 테이블의 url에 경로를 저장합니다.
    """
    try:
        # 1. 오늘 수집된 모든 기사 조회 (조인 포함)
        articles_res = supabase.table("articles") \
            .select("article_id, source_id, category_id, original_url, title, summary, sources(name, type, reliability_score), categories(name)") \
            .gte("collected_at", f"{today_str}T00:00:00") \
            .execute()
        all_articles = articles_res.data if articles_res and articles_res.data else []
    except Exception as e:
        logging.error(f"❌ 전체 기사 조회 중 오류 발생: {str(e)}")
        return

    try:
        # 2. 전체 사용자 목록 조회 (user_id와 email 정보 함께 가져오기)
        users_res = supabase.table("users").select("user_id, email").execute()
        users = users_res.data if users_res and users_res.data else []
    except Exception as e:
        logging.error(f"❌ 사용자 목록 조회 중 오류 발생: {str(e)}")
        return

    type_priority = {"report": 1, "news": 2, "blog": 3, "sns": 4}
    os.makedirs("news", exist_ok=True)

    for user in users:
        user_id = user["user_id"]
        email = user.get("email")

        # 이메일 정보가 없는 경우 기본 폴더명으로 대체
        if not email:
            folder_name = f"user_{user_id}"
        else:
            # 파일 경로로 안전하게 쓰기 위해 이메일 내 특수문자 변환
            folder_name = email.strip().replace("@", "_at_").replace(".", "_")

        try:
            # 3. 사용자가 등록(연동)한 source_id 조회
            sources_res = supabase.table("user_sources") \
                .select("source_id") \
                .eq("user_id", user_id) \
                .execute()
            user_source_ids = {s["source_id"] for s in (sources_res.data or [])}
            
            # 4. 사용자가 활성화한 category_id 조회
            subs_res = supabase.table("subscriptions") \
                .select("category_id") \
                .eq("user_id", user_id) \
                .eq("is_active", True) \
                .execute()
            user_category_ids = {sub["category_id"] for sub in (subs_res.data or [])}
            logging.info(f"👤 사용자({email}) - 선택 소스: {user_source_ids}, 활성 카테고리: {user_category_ids}")

        except Exception as e:
            logging.error(f"❌ 사용자 ID {user_id}의 구독/소스 정보 조회 중 오류: {str(e)}")
            continue

        # 사용자의 선택 소스 또는 활성 카테고리에 맞는 기사 필터링
        filtered_articles = []
        for a in all_articles:
            s_id = a.get("source_id")
            c_id = a.get("category_id")
            if s_id in user_source_ids and c_id in user_category_ids:
                filtered_articles.append(a)

        # 정렬 순서: sources.type -> category_id (오름차순) -> reliability_score (내림차순)
        def sorting_key(x):
            source_info = x.get("sources") if isinstance(x.get("sources"), dict) else {}
            s_type = source_info.get("type", "news")
            type_order = type_priority.get(s_type, 99)
            cat_id = x.get("category_id") or 0
            reliability = source_info.get("reliability_score")
            rel_score = reliability if reliability is not None else 0
            return (type_order, cat_id, -rel_score)

        filtered_articles.sort(key=sorting_key)
        logging.info(f"📊 사용자({email}) 맞춤 기사 수: {len(filtered_articles)}")

        # 이메일 기반 폴더 및 HTML 파일 경로 설정 (예: news/user_example_com/2026-06-07.html)
        user_dir = f"news/{folder_name}"
        os.makedirs(user_dir, exist_ok=True)
        file_path = f"{user_dir}/{today_str}.html"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{today_str} 맞춤 뉴스 요약</title>
            <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 15px; color: #333333; background-color: #f8f9fa; line-height: 1.5; padding: 40px 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }}
                h1 {{ font-size: 1.6em; font-weight: 700; border-bottom: 2px solid #e9ecef; padding-bottom: 12px; margin-bottom: 20px; color: #212529; }}
                .article {{ padding: 12px 0; border-bottom: 1px solid #f1f3f5; }}
                .article:last-child {{ border-bottom: none; }}
                .meta-badges {{ margin-bottom: 5px; }}
                .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: 600; margin-right: 5px; color: #fff; }}
                .category-badge {{ background-color: #2b8a3e; }}
                .type-badge {{ background-color: #364fc7; }}
                .source-badge {{ background-color: #495057; }}
                .title {{ font-size: 1.05em; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }}
                .title a {{ color: #1c7ed6; text-decoration: none; }}
                .title a:hover {{ text-decoration: underline; }}
                .no-articles {{ text-align: center; color: #adb5bd; padding: 40px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📰 {today_str} 맞춤 뉴스 요약</h1>
        """

        if not filtered_articles:
            html_content += '<div class="no-articles"><p>조건에 맞는 신규 기사가 없습니다.</p></div>'
        else:
            for a in filtered_articles:
                source_info = a.get("sources") if isinstance(a.get("sources"), dict) else {}
                category_info = a.get("categories") if isinstance(a.get("categories"), dict) else {}

                source_name = source_info.get("name", "관련 매체")
                source_type = source_info.get("type", "unknown").upper()
                category_name = category_info.get("name", "일반")
                title_text = a.get('title', '제목 없음')
                
                html_content += f"""
                <div class="article">
                    <div class="meta-badges">
                        <span class="badge category-badge">{category_name}</span>
                        <span class="badge type-badge">{source_type}</span>
                        <span class="badge source-badge">{source_name}</span>
                    </div>
                    <div class="title"><a href="{a['original_url']}" target="_blank" title="{title_text}">{title_text}</a></div>
                </div>
                """

        html_content += """
            </div>
        </body>
        </html>
        """

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 5. digests 테이블의 url 컬럼에 파일 경로 포함 형태로 저장/업데이트
        digest_data = {
            "user_id": user_id,
            "digest_date": today_str,
            "title": f"{today_str} 맞춤 뉴스 다이제스트",
            "url": file_path  # 파일 경로 문자열을 url 컬럼에 대입
        }

        try:
            existing = supabase.table("digests") \
                .select("digest_id") \
                .eq("user_id", user_id) \
                .eq("digest_date", today_str) \
                .execute()
            
            if existing and existing.data:
                supabase.table("digests") \
                    .update({
                        "title": f"{today_str} 맞춤 뉴스 다이제스트",
                        "url": file_path
                    }) \
                    .eq("user_id", user_id) \
                    .eq("digest_date", today_str) \
                    .execute()
            else:
                supabase.table("digests").insert(digest_data).execute()
        except Exception as db_e:
            logging.error(f"❌ 사용자 ID {user_id}의 digests 테이블 저장 오류: {str(db_e)}")

        logging.info(f"📄 사용자({email}) 개인 다이제스트 생성 완료: {file_path}")

def crawl_rss_feeds():
    logging.info("🚀 [Start] RSS 피드 수집 및 DB 저장 시작")
    
    try:
        sources_res = supabase.table("sources").select("source_id, name, url").execute()
        rss_targets = sources_res.data if sources_res and sources_res.data else []
    except Exception as e:
        logging.error(f"❌ 소스 목록 조회 오류: {str(e)}")
        return

    try:
        categories_res = supabase.table("categories").select("category_id, name").eq("is_active", True).execute()
        categories = categories_res.data if categories_res and categories_res.data else []
    except Exception as e:
        logging.error(f"❌ 카테고리 목록 조회 오류: {str(e)}")
        categories = []

    saved_count = 0

    for target in rss_targets:
        source_id = target["source_id"]
        source_name = target["name"]
        url = target["url"]

        if not url: continue

        try:
            feed = feedparser.parse(url, request_headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            entries = feed.entries[:10]

            for entry in entries:
                original_url = entry.get("link", "")
                if not original_url: continue

                summary = entry.get("summary", entry.get("description", ""))
                title = entry.get("title", "제목 없음")[:500]

                category_id = determine_category_id(title, summary, categories) if categories else None

                article_data = {
                    "source_id": source_id,
                    "category_id": category_id,
                    "title": title,
                    "original_url": original_url[:1000],
                    "summary": summary,
                    "collect_status": "collected",
                }

                existing = supabase.table("articles").select("article_id").eq("original_url", original_url).execute()

                if existing and hasattr(existing, 'data') and len(existing.data) == 0:
                    response = supabase.table("articles").insert(article_data).execute()
                    if response and hasattr(response, 'data') and response.data:
                        saved_count += 1

        except Exception as e:
            logging.error(f"❌ [{source_name}] 수집 중 오류: {str(e)}")

    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # RSS 수집 직후 사용자별 맞춤 다이제스트 생성 프로세스 실행
    process_user_digests(today_str)
    
    logging.info(f"✅ 총 {saved_count}개 신규 기사 DB 저장 및 개인별 다이제스트 생성 완료\n")

def start_scheduler():
    scheduler = BlockingScheduler(timezone="Asia/Seoul")
    scheduler.add_job(crawl_rss_feeds, trigger="cron", hour=7, minute=0, id="rss_daily_job")
    logging.info("⏰ RSS 스케줄러 시작")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 스케줄러 정지")

def send_kakao_message(access_token, title, description, button_url):
    # 1. 요청 URL 및 헤더 설정
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "Authorization": f"Bearer {access_token}",  # 유효한 액세스 토큰 변수
    }

    # 2. 텍스트 템플릿 객체 정의 (curl 명령어의 --data-urlencode 내용)
    template_object = {
        "object_type": "text",
        "text": "텍스트 영역입니다. 최대 200자 표시 가능합니다.",
        "link": {
            "web_url": "https://developers.kakao.com",
            "mobile_web_url": "https://developers.kakao.com",
        },
        "button_title": "바로 확인",
    }

    # 3. form-urlencoded 형식으로 데이터 구성 (json 문자열로 변환)
    payload = {"template_object": json.dumps(template_object, ensure_ascii=False)}

    # 4. API 요청 전송 및 예외 처리
    try:
        response = requests.post(url, headers=headers, data=payload)
        res_data = response.json()

        # 성공 여부 확인 (카카오는 성공 시 보통 200 코드와 함께 result_code가 0이거나 생략됨)
        if response.status_code == 200 and (
            res_data.get("result_code") == 0 or not res_data.get("result_code")
        ):
            print("나에게 발송 성공")
        else:
            print(f"나에게 발송 실패 {res_data}")

    except Exception as error:
        print(f"나에게 발송 실패 {error}")

#def get_kakao_tokens(auth_code, rest_api_key, redirect_uri):
#
#    # 1. 사용자 인증 코드로 액세스 토큰 받기
#    url = "https://kauth.kakao.com/oauth/token"
#    data = {
#        "grant_type": "authorization_code",
#        "client_id": rest_api_key,
#        "client_secret": "2FrSzZJZWdY76qPVFD8nrM64IMfebYvp", # 보안 설정 사용 시 필수
#        "redirect_uri": redirect_uri,
#        "code": auth_code              # 새로 발급받은 코드 입력
#    }
#
#    response = requests.post(url, data=data)
#    
#    # 요청이 성공적으로 처리되었는지 확인
#    if response.status_code == 200:
#        tokens = response.json()
#        print("액세스 토큰 받기 성공:")
#        print(tokens)
#    else:
#        print(f"오류 발생: {response.status_code} - {response.text}")
#        tokens = None
#
#    # 액세스 토큰 저장
#    if tokens and "access_token" in tokens:
#        access_token = tokens["access_token"]
#    else:
#        access_token = None
#        print("액세스 토큰을 받지 못했습니다.")