import requests

def test_kakao_token():
    url = "https://kauth.kakao.com/oauth/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": "601ec6e08e4bbd251ceb318881a9a01d",
        "client_secret": "2FrSzZJZWdY76qPVFD8nrM64IMfebYvp", # 보안 설정 사용 시 필수
        "redirect_uri": "https://localhost",
        "code": "bT_-KGc4v6ws3gh3csFunJaAQ3KuHS4BFq-_Png3x-szCr4HXNxBSAAAAAQKDRlTAAABoDJ-lWPmTYKY7N6ACw"               # 새로 발급받은 코드 입력
    }
    
    response = requests.post(url, data=data)
    print(f"응답 코드: {response.status_code}")
    print(f"응답 내용: {response.text}")

if __name__ == "__main__":
    test_kakao_token()