# Python 베이스 이미지
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# apt 최적화: --no-install-recommends, 한 RUN으로 묶기
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gfortran && \
    rm -rf /var/lib/apt/lists/*

# requirements 복사 후 의존성 설치
COPY ./requirements.txt ./

# pip 캐시 마운트 사용 (BuildKit 필요)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# 의존성 설치 후 애플리케이션 코드 복사
COPY . /app

# 포트 노출 및 기본 명령어 설정
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]