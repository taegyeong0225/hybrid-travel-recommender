import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 환경 감지
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_mode = os.getenv("ENV", "local")

# 로컬 실행 시 .env.local, Docker 실행 시 .env.docker 로드
if env_mode == "docker":
    load_dotenv(os.path.join(BASE_DIR, ".env.docker"))
else:
    load_dotenv(os.path.join(BASE_DIR, ".env.local"))

# 환경 변수 로드
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

if env_mode == "local" and "://user:password@db:" in SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("db", "127.0.0.1")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()