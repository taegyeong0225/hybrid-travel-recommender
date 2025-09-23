# React, FastAPI, PostgreSQL 프로젝트

이 프로젝트는 React 프론트엔드, FastAPI 백엔드, PostgreSQL 데이터베이스로 구성된 풀스택 애플리케이션의 기본 구조입니다.

## 프로젝트 구조

- `frontend/`: React 애플리케이션
- `backend/`: FastAPI 애플리케이션
- `docker-compose.yml`: PostgreSQL 데이터베이스 실행을 위한 Docker 설정

## 시작하기

### 1. 사전 요구사항

- [Docker](https://www.docker.com/get-started)가 설치되어 있어야 합니다.
- [Node.js](https://nodejs.org/) (npm 포함)가 설치되어 있어야 합니다.
- [Python](https://www.python.org/downloads/) (pip 포함)이 설치되어 있어야 합니다.

### 2. 데이터베이스 실행

프로젝트 루트 디렉터리에서 다음 명령어를 실행하여 PostgreSQL 데이터베이스를 시작합니다.

```bash
docker-compose up -d
```

### 3. 백엔드 실행

새 터미널을 열고 `backend` 디렉터리로 이동하여 필요한 라이브러리를 설치하고 서버를 실행합니다.

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. 프론트엔드 실행

또 다른 새 터미널을 열고 `frontend` 디렉터리로 이동하여 필요한 라이브러리를 설치하고 개발 서버를 시작합니다.

```bash
cd frontend
npm install
npm start
```

### 5. 애플리케이션 확인

웹 브라우저에서 `http://localhost:3000` 주소로 접속하면 "Message from backend: Hello from FastAPI" 메시지가 표시되는 것을 확인할 수 있습니다.
