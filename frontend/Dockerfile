# 1단계: Vite 앱 빌드
FROM node:20-alpine as builder

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 설치 (package.json과 lock 파일만 복사하여 캐시 활용)
COPY package*.json ./
RUN npm install

# 앱 전체 복사 및 빌드
COPY . .
RUN npm run build

# 2단계: Nginx로 정적 파일 서빙
FROM nginx:stable-alpine

# 사용자 정의 nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드 결과물을 nginx의 기본 루트 경로로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 파일 권한 설정 (모든 사용자 읽기 가능)
RUN chmod -R 755 /usr/share/nginx/html

# Nginx 기본 포트 노출
EXPOSE 80

# 컨테이너 시작 시 nginx 실행
CMD ["nginx", "-g", "daemon off;"]