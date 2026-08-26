import sys
import logging
import argparse
from rss_scheduler import crawl_rss_feeds, start_scheduler, send_kakao_message, get_kakao_tokens
from kakao import get_authorization_code

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
        b = "601ec6e08e4bbd251ceb318881a9a01d"
        a = get_authorization_code(b)
        c = "http://localhost:8000"
        # 올바른 예시
        # refresh_token = "DB나 설정에 있는_리프레시_토큰"
        # access_token, _ = refresh_access_token(a) # 1. 리프레시 토큰으로 액세스 토큰 획득

        get_kakao_tokens(a,b,c)

    else:
        start_scheduler()

if __name__ == "__main__":
    main()