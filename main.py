import sys
import logging
import argparse
from rss_scheduler import crawl_rss_feeds, start_scheduler, send_kakao_message
from kakao import refresh_access_token

# ---------------------------------------------------------------------------
# 로깅 설정 (콘솔 및 파일 저장)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("rss_crawler.log", encoding="utf-8")
    ]
)

def main():
    parser = argparse.ArgumentParser(description="AX News RSS Resource Scheduler")
    
    parser.add_argument(
        "--now",
        action="store_true",
        help="스케줄러 대기 없이 즉시 1회 크롤링을 실행합니다."
    )

    parser.add_argument(
        "--send-kakao",
        action="store_true",
        help="카카오톡 메시지를 전송합니다."
    )

    args = parser.parse_args()

    if args.now:
        logging.info("⚡ [--now] 옵션 감지: 즉시 수집 작업을 실행합니다.")
        crawl_rss_feeds()
    elif args.send_kakao:
        logging.info("⚡ [--send-kakao] 옵션 감지: 카카오톡 메시지를 전송합니다.")
        # Implement Kakao message sending logic here
        # send_kakao_message(access_token, title, description, button_url):
        a = "601ec6e08e4bbd251ceb318881a9a01d"
        b = "kcLgDOL63ofCUOngJI6hu_zPwrZi3G2tAAAAAgoNH9EAAAGgO1eTkIa1Lb_-w10F"

        # 올바른 예시
        # refresh_token = "DB나 설정에 있는_리프레시_토큰"
        # access_token, _ = refresh_access_token(a) # 1. 리프레시 토큰으로 액세스 토큰 획득

        token = refresh_access_token(a,b)

        if 'refresh_token' in token:
            print(f"refresh_token : {token.refresh_token}")
            print(f"refresh_token : {token.refresh_token}")
            print(f"refresh_token : {token.refresh_token}")

        send_kakao_message(token.access_token, "오늘의 맞춤 뉴스 요약", "오늘 수집된 맞춤 뉴스 다이제스트를 확인하세요. \n\n http://localhost:8000", "http://localhost:8000")
    else:
        start_scheduler()

if __name__ == "__main__":
    main()