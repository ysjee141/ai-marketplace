# 웹 프론트엔드 구현 플레이북

프레임워크 무관(React/Vue/Svelte/Angular). 구조와 판단을 다룬다.

## 목차

1. [구조 분리](#1-구조-분리)
2. [상태 관리](#2-상태-관리)
3. [서버 데이터 연동](#3-서버-데이터-연동)
4. [라우팅](#4-라우팅)
5. [폼과 검증](#5-폼과-검증)
6. [접근성과 성능](#6-접근성과-성능)
7. [테스트](#7-테스트)
8. [E2E silent 설정](#8-e2e-silent-설정)

---

## 1. 구조 분리

컴포넌트는 **상태를 화면으로 매핑하는 얇은 층**이다. 계산·변환·검증은 밖으로 뺀다.

```
src/
├── domain/         순수 로직 — 검증, 계산, 포맷. 프레임워크 무관
├── api/            서버 통신 — 계약 타입, 클라이언트
├── hooks/          데이터·상태 훅
├── components/     표현 컴포넌트 (상태 없음)
├── features/       기능 단위 (컨테이너 + 하위 컴포넌트)
├── routes/         라우트 정의 + 경로 상수
└── shared/         공용 유틸·UI
```

**`domain/`의 코드는 프레임워크 없이 테스트된다.** 프론트엔드에서도
순수성 원칙이 그대로 적용되며, 테스트 속도 차이가 크다.

```typescript
// domain/pricing.ts — 순수. 컴포넌트 없이 테스트 가능
export function calcTotal(items: Item[], coupon?: Coupon): Money { ... }

// features/cart/CartSummary.tsx — 얇다
const total = calcTotal(items, coupon);
return <Price value={total} />;
```

---

## 2. 상태 관리

상태를 종류별로 구분한다. 전부 한 저장소에 넣으면 관리 불가능해진다.

| 종류 | 예 | 배치 |
|------|-----|------|
| 서버 상태 | 조회한 목록, 사용자 정보 | 데이터 페칭 라이브러리 (캐시·재검증 포함) |
| URL 상태 | 필터, 페이지, 탭 | 쿼리 파라미터 |
| 폼 상태 | 입력 중인 값 | 로컬 또는 폼 라이브러리 |
| UI 상태 | 모달 열림, 토글 | 컴포넌트 로컬 |
| 전역 클라이언트 상태 | 테마, 인증 토큰 | 전역 저장소 (**최소화**) |

**서버 상태를 전역 저장소에 복제하지 않는다.** 동기화 버그의 주범이다.

---

## 3. 서버 데이터 연동

### 계약 확인이 먼저다

`api-contract.md`가 정본이다. **응답 래핑 여부를 반드시 확인한다.**

```typescript
// 계약: { "data": { "items": [...], "total": 120 } }

// 틀림 — 런타임에 items.map is not a function
const items = await fetchJson<Item[]>("/api/items");

// 맞음 — 계약대로 언랩
const res = await fetchJson<{ data: { items: Item[]; total: number } }>("/api/items");
const items = res.data.items;
```

**타입 파라미터는 검증이 아니라 주장이다.** 컴파일러는 런타임 응답을 모른다.
계약과 다르면 조용히 통과했다가 실행 시 터진다. 이것이 프론트엔드에서 가장
흔한 런타임 오류다.

### 규칙

- API 호출을 컴포넌트에 직접 쓰지 않는다. `api/` + `hooks/`를 거친다
- 응답 타입은 계약 문서에서 생성하거나 수기 정의하되 **한 곳에만** 둔다
- 즉시 응답(202)과 최종 결과를 **별개 타입**으로 다룬다.
  `data.failedIndices` 같은 최종 결과 필드를 즉시 응답에서 읽지 않는다
- 에러 바디 형태를 계약대로 파싱한다. 엔드포인트마다 다르게 처리하지 않는다

### 세 가지 상태를 반드시 구현한다

**로딩·에러·빈 상태가 없는 화면은 미완성이다.** 성공 경로만 만든 화면은
실제 환경에서 반드시 깨진다.

```typescript
if (isLoading) return <Skeleton />;
if (error)     return <ErrorState error={error} onRetry={refetch} />;
if (!items.length) return <EmptyState />;
return <ItemList items={items} />;
```

---

## 4. 라우팅

**경로를 코드에 흩뿌리지 않는다.** 상수를 한 곳에 모으고 거기서만 참조한다.

```typescript
// routes/paths.ts
export const PATHS = {
  dashboard: "/dashboard",
  projectDetail: (id: string) => `/dashboard/projects/${id}`,
} as const;

// 사용
<Link to={PATHS.projectDetail(p.id)} />
```

이유: 파일 구조와 링크가 어긋나면 404가 나고, 정적 검사로 잡히지 않는다.
상수로 모으면 `qa-inspector`가 라우트 정의와 상수를 대조해 검증할 수 있다.

**라우트 그룹·접두사에 주의한다.** 파일이 `dashboard/projects/[id]`에 있는데
링크가 `/projects/{id}`면 404다 — 흔한 결함이다.

---

## 5. 폼과 검증

- **검증 규칙은 `domain/`의 순수 함수로** 두고 폼에서 호출한다.
  서버와 규칙이 다르면 사용자가 혼란스럽다 — 규칙 정의를 계약에서 가져온다
- 클라이언트 검증은 **UX용이지 보안이 아니다.** 서버 검증이 정본이다
- 제출 중 중복 제출을 막는다 (버튼 비활성 + 요청 중복 제거)
- 서버 검증 오류를 필드에 매핑한다. 계약의 `details`가 그 용도다

---

## 6. 접근성과 성능

### 접근성 (기본)

- 시맨틱 태그를 쓴다 (`button`, `nav`, `main`). `div` + onClick 금지
- 폼 입력에 레이블을 연결한다
- 키보드로 모든 조작이 가능해야 한다. 포커스 트랩과 순서를 확인한다
- 색상만으로 정보를 전달하지 않는다
- 동적 변경은 라이브 리전으로 알린다

### 성능

- **측정 후 최적화한다.** 조기 메모이제이션은 복잡도만 늘린다
- 라우트 단위 코드 분할이 가장 효과가 크다
- 목록에 안정적인 key를 쓴다. 인덱스 key는 재정렬 시 버그를 만든다
- 이미지에 크기를 지정하여 레이아웃 이동을 막는다
- N+1 호출을 만들지 않는다. 필요한 데이터는 API에 요청한다

---

## 7. 테스트

| 대상 | 방식 | 요구 |
|------|------|------|
| `domain/` 순수 로직 | 단위 | 경계값 포함. 컴포넌트 없이 |
| 표현 컴포넌트 | 렌더링 | props → 출력 |
| 컨테이너·훅 | 통합 | **로딩/에러/빈/성공 4가지 상태 각각** |
| API 클라이언트 | 계약 | 계약 예시 응답으로 파싱 검증 |
| 사용자 시나리오 | E2E | headless |

**구현 세부가 아니라 사용자 관점으로 쿼리한다.** 클래스명·컴포넌트 내부 상태가
아니라 화면에 보이는 텍스트·역할로 요소를 찾는다. 리팩터링에 견고해진다.

---

## 8. E2E silent 설정

`harness/principles/testing.md` 3절 필수 준수.

### Playwright

```typescript
// playwright.config.ts
export default defineConfig({
  use: { headless: true, trace: "retain-on-failure", video: "retain-on-failure" },
  reporter: [["json", { outputFile: "test-results/e2e.json" }], ["line"]],
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
});
```

### Cypress

`cypress run` 만 사용한다 (`cypress open` 금지).
`--reporter json`, `video: false` (실패 시에만 활성).

### 공통 규칙

| 규칙 | 이유 |
|------|------|
| 고정 `sleep` 금지 | 느리고 불안정. 조건 기반 대기만 |
| 테스트별 격리 시드 데이터 | 순서 의존 제거 |
| 실패 시에만 아티팩트 | 저장소·시간 낭비 방지 |
| non-zero 종료 | 파이프라인이 판정 가능해야 함 |
| 기계 판독 리포터 필수 | 자동 집계 |

**브라우저 실행이 불가능한 환경이면** E2E를 작성하되 실행은 건너뛰고
**미실행을 명시**한다. 실행하지 않은 것을 통과로 보고하지 않는다.
