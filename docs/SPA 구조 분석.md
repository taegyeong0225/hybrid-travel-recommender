# TripMate - SPA(Single Page Application) 구조 분석

## 결론
**TripMate는 완벽한 SPA(웹앱) 구조입니다.** ✅

---

## SPA란?

Single Page Application(SPA)는 **하나의 HTML 페이지만 로드**하고, 이후 사용자 인터랙션에 따라 **페이지를 새로고침하지 않고 동적으로 컨텐츠를 변경**하는 웹 애플리케이션 구조입니다.

전통적인 MPA(Multi-Page Application)는 페이지 이동마다 서버에서 새로운 HTML을 받아오지만, SPA는 클라이언트 사이드에서 JavaScript로 페이지를 렌더링합니다.

---

## TripMate가 SPA인 근거

### 1. React 기반 프레임워크
**파일**: `frontend/package.json`

```json
{
  "dependencies": {
    "react": "^19.1.1",
    "react-dom": "^19.1.1"
  }
}
```

- React는 대표적인 SPA 구축 라이브러리
- 컴포넌트 기반으로 UI를 동적으로 렌더링

### 2. 클라이언트 사이드 라우팅
**파일**: `frontend/package.json`, `frontend/src/App.jsx`

```json
{
  "dependencies": {
    "react-router-dom": "^7.9.1"
  }
}
```

```jsx
// App.jsx
<Router>
  <Routes>
    <Route path="/" element={...} />
    <Route path="/login" element={<Login />} />
    <Route path="/signup" element={<Signup />} />
    <Route path="/mypage" element={<MyPage />} />
  </Routes>
</Router>
```

- `react-router-dom`을 사용하여 **클라이언트에서 라우팅 처리**
- `BrowserRouter`로 브라우저 히스토리 API 활용
- 페이지 전환 시 서버 요청 없이 컴포넌트만 교체

### 3. Vite 번들러 사용
**파일**: `frontend/package.json`

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.0.4",
    "vite": "^7.1.9"
  }
}
```

- Vite는 모던 SPA를 위한 빌드 도구
- 모든 JavaScript를 하나의 번들로 만들어 단일 HTML에서 실행
- 빠른 HMR(Hot Module Replacement)로 개발 효율성 향상

### 4. Link 컴포넌트를 통한 네비게이션
**파일**: `frontend/src/App.jsx`

```jsx
<ul className="nav-links">
  <li><Link to="/">Home</Link></li>
  {currentUser && <li><Link to="/mypage">마이페이지</Link></li>}
</ul>
```

- `<Link>` 컴포넌트는 **페이지 새로고침 없이** URL만 변경
- 전통적인 `<a>` 태그와 달리 서버에 요청하지 않음

### 5. 상태 관리가 클라이언트에서 이루어짐
**파일**: `frontend/src/App.jsx`

```jsx
const [result, setResult] = useState(null);
const [loading, setLoading] = useState(false);
const [currentUser, setCurrentUser] = useState(null);
```

- React의 `useState`, `useEffect`로 클라이언트 상태 관리
- 로그인 정보를 `localStorage`에 저장하고 클라이언트에서 관리

### 6. API 통신은 비동기로 처리
**파일**: `frontend/src/App.jsx:78-91`

```jsx
const fetchRecommendations = async () => {
  setLoading(true);
  try {
    const response = await fetch("http://localhost:8000/recommend", { method: "POST" })
    if (!response.ok) throw new Error("Request failed");
    const data = await response.json();
    setResult(data);
  } catch (error) {
    console.error("Error fetching recommendation:", error);
    setResult({ error: "추천 요청 실패" });
  } finally {
    setLoading(false);
  }
};
```

- `fetch` API를 사용해 백엔드와 비동기 통신
- 데이터만 받아와서 클라이언트에서 렌더링
- **페이지 전체를 다시 로드하지 않음**

---

## SPA의 장점 (TripMate에 적용)

### 1. 빠른 사용자 경험
- 페이지 전환 시 새로고침이 없어 부드러운 UX
- 로그인/로그아웃 후에도 페이지 깜빡임 없음

### 2. 효율적인 리소스 사용
- 최초 1회만 HTML/CSS/JS 로드
- 이후엔 필요한 데이터만 JSON으로 교환

### 3. 프론트엔드/백엔드 분리
- React(프론트) + FastAPI(백엔드)로 완전히 분리된 구조
- 각각 독립적으로 개발/배포 가능

### 4. 모바일 앱처럼 동작
- 앱과 유사한 매끄러운 화면 전환
- PWA(Progressive Web App)로 확장 가능

---

## 구조 요약

```
TripMate SPA 구조
├── 프론트엔드 (React + Vite)
│   ├── 단일 HTML 페이지 (index.html)
│   ├── 클라이언트 라우팅 (react-router-dom)
│   ├── 컴포넌트 기반 UI
│   └── 상태 관리 (React Hooks)
│
└── 백엔드 (FastAPI)
    ├── RESTful API 제공
    ├── JSON 데이터 응답
    └── /api, /recommend 등 엔드포인트
```

---

## 결론

TripMate는 다음 요소들로 인해 **명확한 SPA 구조**입니다:

1. ✅ React 기반 컴포넌트 렌더링
2. ✅ 클라이언트 사이드 라우팅 (react-router-dom)
3. ✅ Vite 번들러로 단일 페이지 빌드
4. ✅ 페이지 새로고침 없는 네비게이션
5. ✅ 비동기 API 통신으로 데이터만 교환
6. ✅ 클라이언트에서 상태 관리

전통적인 서버 렌더링(SSR) 방식이 아닌, **완전한 클라이언트 사이드 렌더링(CSR) 기반의 웹앱(SPA)**입니다.
