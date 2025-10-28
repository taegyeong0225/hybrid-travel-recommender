# 🚀 TripMate Web Project  
> **FastAPI + React + PostgreSQL + Redis + Docker** 기반 여행 추천 웹서비스  

---

## 📁 Project Structure

```
tripmate/
 ┣ backend/               # FastAPI 서버
 ┣ frontend/              # React 클라이언트
 ┣ db/                    # 초기 SQL 스크립트 및 설정
 ┣ docker-compose.yml     # 전체 서비스 통합 관리
 ┣ Makefile               # 개발/배포 자동화 명령어
 ┗ README.md
```

---

## ⚙️ 1. Environment Setup

### 🧩 Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 💻 Frontend
```bash
cd frontend
npm install
```

---

## 🧰 2. Environment Variables (.env)

### 🔹 `backend/.env`
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/tripmate
REDIS_URL=redis://redis:6379
CORS_ORIGINS=http://localhost:5173
```

### 🔹 `frontend/.env`
```bash
VITE_API_URL=http://localhost:8000
```

---

## 🚀 3. Run Project (Local Mode)

### 🔹 실행 명령
```bash
make dev
```

### 🔹 내부 동작
- FastAPI backend → http://localhost:8000  
- React frontend → http://localhost:5173  

> `make dev` 명령은 `run-backend`와 `run-frontend`를 동시에 실행합니다.  
> 브라우저에서 프론트엔드를 열면 자동으로 API와 연동됩니다.

---

## 🐳 4. Run with Docker (Deployment Mode)

### 🔹 빌드 및 실행
```bash
make up
```

### 🔹 내부 동작
- FastAPI backend  
- React frontend  
- PostgreSQL  
- Redis  

> 최초 실행 시 시간이 다소 걸릴 수 있습니다.  
> 빌드 후 브라우저에서 `http://localhost:5173` 접속해 확인하세요.

---

## 🧹 5. Stop Containers

Makefile에 아래 명령어가 추가되어 있다면 종료할 때 이렇게 입력합니다 👇

```bash
make down
```

> 또는 수동으로 종료하려면:
> ```bash
> cd backend
> docker compose down
> ```

---

## 🔍 6. Check Status

```bash
docker ps
```

| Service | Port | Description |
|----------|------|-------------|
| FastAPI | 8000 | Backend API |
| React | 5173 | Frontend UI |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |

---

## ⚡ 7. Common Issues

| 문제 | 원인 | 해결 |
|------|------|------|
| `psycopg2.OperationalError` | DB 연결 실패 | 컨테이너 실행 대기 후 재시도 |
| `CORS` 에러 | Frontend API 주소 불일치 | `.env`에서 `VITE_API_URL` 수정 |
| `ModuleNotFoundError` | 패키지 누락 | `pip install -r requirements.txt` 실행 |
| 포트 충돌 | 기존 프로세스 점유 | `sudo lsof -i :8000` → `kill -9 PID` |

---

## 🧠 8. Makefile 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `make dev` | 로컬 개발환경 (FastAPI + React) 동시 실행 |
| `make run-backend` | 백엔드 단독 실행 |
| `make run-frontend` | 프론트엔드 단독 실행 |
| `make up` | Docker Compose 빌드 및 실행 |
| `make down` | Docker Compose 종료 |

---

💡 *Tip:*  
개발 중 `venv` 활성화는 **항상 backend 디렉토리 내에서만** 해주세요.  
FastAPI와 React 둘 다 `.env` 설정을 정확히 맞춰야 API 연동이 정상 동작합니다.

---

[9주차 Redis 캐싱 로직 설정](./docs/9주차.md)
