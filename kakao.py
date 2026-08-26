import urllib.parse
import webbrowser
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

class KakaoAuthHandler(BaseHTTPRequestHandler):
  authorization_code = None

  print("KakaoAuthHandeler")
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


#def get_authorization_code(rest_api_key):
#    port = 8000
#    redirect_uri = f"http://localhost:{port}"
#
#    # 1. 카카오 인증 URL 생성 (talk_message 권한 포함)
#    auth_url = (
#        f"https://kauth.kakao.com/oauth/authorize?"
#        f"client_id={rest_api_key}&"
#        f"redirect_uri={redirect_uri}&"
#        f"response_type=code&"
#        f"scope=talk_message"
#    )
#
#    print("🌐 브라우저를 열어 카카오 로그인을 진행합니다...")
#    # 2. 브라우저 자동으로 열기
#    webbrowser.open(auth_url)
#
#    # 3. 로컬 서버를 잠깐 띄워 리다이렉트 요청 대기
#    server_address = ("localhost", port)
#    httpd = HTTPServer(server_address, KakaoAuthHandler)
#
#    print(f"🔗 리다이렉트된 인가 코드를 기다리는 중... (http://localhost:{port})")
#
#    # 코드가 들어올 때까지 딱 1번 요청을 처리
#    while KakaoAuthHandler.authorization_code is None:
#        print("Handle_re")
#        httpd.handle_request()
#
#    print(f"✅ 인가 코드 획득 성공: {KakaoAuthHandler.authorization_code}")
#    return KakaoAuthHandler.authorization_code

def refresh_access_token(rest_api_key, refresh_token):
    url = "https://kauth.kakao.com/oauth/token"
    
    # 요청에 담을 데이터 설정
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
        "client_secret": "2FrSzZJZWdY76qPVFD8nrM64IMfebYvp"
    }

    print(url, data)
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        token_info = response.json()
        print("✅ Access Token 갱신 성공!")
        print(f"새로운 Access Token: {token_info.get('access_token')}")
        
        # 만약 응답에 새로운 refresh_token도 함께 내려왔다면 (보통 만료 기간이 임박했을 때 재발급됨)
        if 'refresh_token' in token_info:
            print(f"🔄 Refresh Token도 새로 발급되었습니다: {token_info.get('refresh_token')}")
            
        return token_info
    else:
        print(f"❌ 갱신 실패: {response.status_code}")
        print(response.json())
        return None
