# 작업 공간 규약

`/_workspace/`는 **진행 중 상태의 단일 진실 공급원**이다.
LLM 세션이 끊겨도 여기만 읽으면 작업을 이어갈 수 있어야 한다.

## 목차

1. [디렉토리 구조](#1-디렉토리-구조)
2. [walkthrough.md — 복구의 핵심](#2-walkthroughmd--복구의-핵심)
3. [단계별 산출물 규약](#3-단계별-산출물-규약)
4. [세션 복구 절차](#4-세션-복구-절차)
5. [보존과 정리](#5-보존과-정리)

---

## 1. 디렉토리 구조

작업 단위(slug)마다 폴더를 분리하여 기록을 보존한다.

```
_workspace/
├── walkthrough.md              ★ 전체 작업의 진행 현황 (복구 진입점)
└── {slug}/                     작업 단위 폴더 (예: user-auth/)
    ├── state.json              기계 판독 상태 (단계·게이트·재시도 횟수)
    ├── 00_input/               사용자 입력 원문, 첨부 자료
    ├── 01_planning/            기획 — 인터뷰 로그, PRD 초안
    ├── 02_analysis/            분석 — 기획분석·개발분석 결과, 리스크
    ├── 03_plan/                계획 — Tech Spec 초안, ADR 초안, WBS, CPM, Task
    ├── 04_design/              설계 — 설계서 초안, 다이어그램, 경계면 계약
    ├── 05_implement/           구현 — 모듈별 구현 노트, 경계면 확정본
    ├── 06_test/                테스트 — 실행 로그, 커버리지 원본 데이터
    ├── 07_review/              리뷰 — 게이트별 리뷰 결과, 반려 사유
    ├── 08_deploy/              배포 — CI/CD 구성 초안
    └── 99_gate/                게이트 판정 기록 (통과/반려 이력)
```

**파일 명명:** `{순번}_{에이전트}_{산출물}.{확장자}`
예: `02_codebase-analyst_risk-assessment.md`

숫자 접두사가 있으므로 파일 목록만 봐도 진행 순서가 드러난다.

## 2. walkthrough.md — 복구의 핵심

`_workspace/walkthrough.md`는 **모든 작업 단위를 가로지르는 단일 진행 기록**이다.
새 세션이 시작되면 오케스트레이터가 가장 먼저 이 파일을 읽는다.

### 필수 구조

```markdown
# Walkthrough

> 이 파일은 세션 단절 시 작업 재개의 진입점이다.
> 각 단계 시작·종료 시 반드시 갱신한다.

## 현재 작업

| 항목 | 값 |
|------|-----|
| slug | user-auth |
| 실행 모드 | balanced (config) |
| 단계 | 04_design |
| 상태 | in_progress |
| 담당 | architect |
| 마지막 갱신 | 2026-08-14 14:32 |
| 다음 행동 | 도메인 모델 다이어그램 완성 후 설계 리뷰 게이트 진입 |

## 진행 로그

| 시각 | 단계 | 이벤트 | 행위자 | 산출물 / 비고 |
|------|------|--------|--------|-------------|
| 2026-08-14 09:10 | 01_planning | 시작 | planner-interviewer | - |
| 2026-08-14 10:05 | 01_planning | 완료 | planner-interviewer | `01_planning/prd-draft.md` |
| 2026-08-14 10:07 | gate:planning | 통과 | doc-reviewer | `99_gate/gate-planning-r1.md` |
| 2026-08-14 10:20 | 02_analysis | 시작 | research-analyst, codebase-analyst | - |
| 2026-08-14 11:40 | 02_analysis | 완료 | 〃 | `02_analysis/*.md` |
| 2026-08-14 11:45 | gate:analysis | **반려** | doc-reviewer | 사유: 외부 인증 연동 리스크 누락 |
| 2026-08-14 12:30 | 02_analysis | 재작업 완료 | codebase-analyst | 리스크 3건 추가 |
| 2026-08-14 12:35 | gate:analysis | 통과 | doc-reviewer | `99_gate/gate-analysis-r2.md` |

## 미결정 사항

| # | 내용 | 결정 필요 시점 | 상태 |
|---|------|--------------|------|
| 1 | 세션 저장소를 Redis로 할지 DB로 할지 | 설계 완료 전 | ADR-0003 작성 중 |

## 승격 이력

| 시각 | 원본 | 승격 경로 | 승인 |
|------|------|----------|------|
| 2026-08-14 10:10 | `01_planning/prd-draft.md` | `docs/prd/prd-user-auth.md` | 사용자 승인 |
```

### 갱신 시점

**다음 순간마다 예외 없이 갱신한다:**

1. 단계 시작 직전
2. 단계 완료 직후
3. 리뷰 게이트 판정 직후 (통과/반려 모두)
4. 사용자 결정이 필요한 항목 발생 시
5. 승격 승인 직후
6. 에러로 작업이 중단될 때 — **중단 사유와 재개 지점을 기록**

> 갱신을 미루면 세션이 끊긴 순간의 상태가 유실된다.
> "나중에 한 번에 정리"는 이 파일의 목적을 무효화한다.

## 3. 단계별 산출물 규약

### state.json

`_workspace/{slug}/state.json` — 오케스트레이터가 기계적으로 읽는 상태.

```json
{
  "slug": "user-auth",
  "created": "2026-08-14T09:10:00+09:00",
  "updated": "2026-08-14T14:32:00+09:00",
  "execution_mode": "balanced",
  "mode_source": "config",
  "current_stage": "04_design",
  "stage_status": "in_progress",
  "ddd_level": 2,
  "stages": {
    "01_planning": { "status": "passed", "gate_attempts": 1 },
    "02_analysis": { "status": "passed", "gate_attempts": 2 },
    "03_plan":     { "status": "passed", "gate_attempts": 1 },
    "04_design":   { "status": "in_progress", "gate_attempts": 0 }
  },
  "tasks": { "total": 12, "done": 0 },
  "open_decisions": ["ADR-0003"]
}
```

`stage_status`: `pending` | `in_progress` | `in_review` | `rejected` | `passed`
`execution_mode`: `skill` | `balanced` | `agent` — 이 작업의 실행 모드 (`harness/execution-modes.md`)
`mode_source`: `config` | `user` | `auto-suggested` — 모드가 결정된 경로

**walkthrough.md와 state.json은 항상 함께 갱신한다.** 전자는 사람용 서사,
후자는 오케스트레이터용 상태다. 불일치가 발견되면 walkthrough.md를 정본으로 삼는다.

### 산출물 자기 기술

각 산출물 파일 상단에 최소 정보를 남긴다. 다른 에이전트가 컨텍스트 없이
파일만 읽고도 신뢰도를 판단할 수 있어야 한다.

```markdown
<!-- stage: 02_analysis | agent: codebase-analyst | slug: user-auth
     input: 01_planning/prd-draft.md | updated: 2026-08-14 11:40 -->
```

## 4. 세션 복구 절차

새 세션에서 오케스트레이터가 수행하는 순서:

1. `_workspace/walkthrough.md` 존재 확인
   - **없음** → 신규 작업. 초기 실행으로 진행
2. `walkthrough.md`의 "현재 작업" 표에서 slug·단계·상태·다음 행동을 읽는다
3. `_workspace/{slug}/state.json`으로 기계 상태를 교차 확인한다
4. 해당 단계 디렉토리의 산출물 목록을 확인하여 **실제 완료 지점**을 판정한다
   - walkthrough가 "완료"라 해도 산출물 파일이 없으면 미완료로 간주한다
5. 사용자에게 재개 지점을 보고하고 확인받는다:

```markdown
이전 작업을 발견했습니다.

- 작업: user-auth
- 마지막 단계: 04_design (진행 중)
- 다음 행동: 도메인 모델 다이어그램 완성 후 설계 리뷰 게이트 진입
- 미결정: ADR-0003 (세션 저장소 선택)

이어서 진행할까요? (이어서 / 이 단계부터 다시 / 새 작업)
```

6. "이어서" 선택 시 해당 단계 에이전트에게 기존 산출물 경로를 포함하여 재호출한다

## 5. 보존과 정리

- `_workspace/`는 `.gitignore` 대상이므로 **삭제하지 않는다.** 커밋되지 않아도
  로컬에서 사후 검증·감사 추적의 근거가 된다
- 동일 slug로 **새 실행**을 시작할 때는 기존 폴더를 삭제하지 않고
  `_workspace/{slug}_{YYYYMMDD_HHMMSS}/`로 이동한 뒤 새로 만든다
- 작업 완료 후에도 유지한다. 정리는 사용자가 명시적으로 요청할 때만 수행한다
- 승격되지 않은 내용은 언젠가 사라질 수 있음을 전제로, **판단의 근거가 되는 것은
  반드시 승격한다** (`documentation.md` 5절)
