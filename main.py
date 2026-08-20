import os
from fastapi import FastAPI
import psycopg2

app = FastAPI()

# Supabase DB 연결 테스트용 루트 경로
@app.get("/")
def read_root():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return {"status": "ok", "db_status": "DATABASE_URL이 설정되지 않았습니다."}
    
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        return {"status": "ok", "db_status": "Supabase DB 연결 성공!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}