# Python 베이스 이미지
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 과학 라이브러리 빌드용 OS 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# requirements 복사 후 의존성 설치
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 의존성 설치 후 애플리케이션 코드 복사
# COPY . /app

# 전체 복사가 아니라, 필요한 폴더만 선택 복사
COPY app/ ./
COPY .env.docker ./

# utills 폴더 복사 추가
COPY app/utills ./app/utills

# 포트 노출 및 기본 명령어 설정
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]