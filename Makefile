# ================================
# TripMate Development Automation
# ================================

BACKEND_DIR = backend
FRONTEND_DIR = frontend

# 백엔드 실행 명령
run-backend:
	cd $(BACKEND_DIR) && export ENV=local && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 실행 명령
run-frontend:
	cd $(FRONTEND_DIR) && npm run dev

# 로컬 개발용
dev:
	@echo "🚀 Starting TripMate Dev Environment (Local)..."
	@echo "   ▶ FastAPI Backend (port 8000)"
	@echo "   ▶ React Frontend (port 5173)"
	@echo ""
	@$(MAKE) -j2 run-backend run-frontend

# Docker 배포용
up:
	@echo "📦 Starting TripMate via Docker Compose..."
	@cd $(BACKEND_DIR) && export ENV=docker && docker compose up --build