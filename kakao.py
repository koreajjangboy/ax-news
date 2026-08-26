import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


class KakaoAuthHandler(BaseHTTPRequestHandler):
  authorization_code = None

  def do_GET(self):
    # 리다이렉트된 주소에서 파라미터 파싱
    parsed_path = urllib.parse.urlparse(self.path)
    query_params = urllib.parse.parse_qs(parsed_path.query)

    if "code" in query_params:
        KakaoAuthHandler.authorization_code = query_params["code"][0]

        # 브라우저에 띄워줄 성공 메시지
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        response_msg = (
            "<h2>[성공] 인가 코드가 정상적으로 발급되었습니다!</h2>"
            "<p>이 창을 닫고 터미널을 확인하세요.</p>"
        )
        self.wfile.write(response_msg.encode("utf-8"))
    else:
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b"Authorization code not found.")

  # 로그 출력을 조용하게 만듦 (선택사항)
  def log_message(self, format, *args):
    pass


def get_authorization_code(rest_api_key):
    port = 8000
    redirect_uri = f"http://localhost:{port}"

    # 1. 카카오 인증 URL 생성 (talk_message 권한 포함)
    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={rest_api_key}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=talk_message"
    )

    print("🌐 브라우저를 열어 카카오 로그인을 진행합니다...")
    # 2. 브라우저 자동으로 열기
    webbrowser.open(auth_url)

    # 3. 로컬 서버를 잠깐 띄워 리다이렉트 요청 대기
    server_address = ("localhost", port)
    httpd = HTTPServer(server_address, KakaoAuthHandler)

    print(f"🔗 리다이렉트된 인가 코드를 기다리는 중... (http://localhost:{port})")

    # 코드가 들어올 때까지 딱 1번 요청을 처리
    while KakaoAuthHandler.authorization_code is None:
        httpd.handle_request()

    print(f"✅ 인가 코드 획득 성공: {KakaoAuthHandler.authorization_code}")
    return KakaoAuthHandler.authorization_code
    

if __name__ == "__main__":
  # 본인의 REST API 키 입력
  REST_API_KEY = "601ec6e08e4bbd251ceb318881a9a01d"

  code = get_authorization_code(REST_API_KEY)
  print(f"최종 인가 코드: {code}")