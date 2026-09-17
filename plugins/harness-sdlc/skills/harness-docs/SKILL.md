---
name: harness-docs
description: "하네스 문서 규약과 작업 상태 기록 절차. /docs 배치 규칙, 템플릿 사용, /_workspace 구조, walkthrough·state.json 갱신, 문서 승격을 다룬다. '문서 어디에 둘까', '이 문서 승격해줘', 'walkthrough 갱신해줘', '진행 상황 기록해줘', '지금 어디까지 했지' 요청 시 사용. 모든 파이프라인 단계에서 공용으로 참조. 제외: 중단된 작업을 실제로 이어서 진행하는 것은 sdlc-orchestrator의 역할이다. 이 스킬은 상태 조회·기록만 담당한다. 파일명 변경 같은 단순 파일 조작도 제외."
---

# Harness Docs — 문서 규약 및 작업 상태 관리

모든 에이전트가 공용으로 참조하는 문서·상태 관리 절차.
상세 규범은 `harness/principles/documentation.md`, `harness/principles/workspace.md`.

## 두 저장소의 구분

| | `/docs/` | `/_workspace/` |
|---|---------|---------------|
| 성격 | 참조용 자산 | 작업 로그 |
| 커밋 | 된다 | **안 된다** (`.gitignore`) |
| 수명 | 영구 | 작업 기간 |
| 형식 | 템플릿 준수, 정제됨 | 자유, 과정 포함 |
| 독자 | 미래의 사람·AI | 현재 진행 중인 에이전트 |

**`/_workspace/`의 내용은 커밋되지 않는다.** 따라서 이후에도 참조해야 하는 것은
반드시 승격해야 한다. 승격을 빠뜨리면 판단 근거가 유실된다.

## 문서 배치

```
docs/
├── template/    문서 템플릿 (작성 시 반드시 참조)
├── prd/         PRD, 용어 정의, 사용자 스토리
├── plan/        Tech Spec, WBS, Task
│   └── adr/     ADR 개별 파일
├── design/      설계서, 도메인 모델, 다이어그램, API 계약, 용어집
├── implement/   구현 노트, 경계면 계약 확정본
├── test/        테스트 계획, 테스트 리포트
├── review/      단계별 리뷰 결과, 최종 리뷰
└── report/      진행·완료 보고, 하네스 개선 제안
```

### 명명

```
{종류}-{slug}.md              일반 문서
ADR-{NNNN}-{slug}.md          ADR (4자리, 저장소 전역 증가)
```

- **slug는 작업 단위 전체가 공유한다.** `prd-user-auth.md` ↔ `design-user-auth.md`
- **파일명에 날짜를 넣지 않는다.** 갱신마다 참조 링크가 깨진다. 날짜는 frontmatter에
- 예외: `test-report.md`는 slug 없이 단일 파일, 매번 덮어쓴다

### frontmatter (필수)

```yaml
---
title: 사용자 인증 설계서
slug: user-auth
stage: design           # prd | plan | design | implement | test | review | report
status: draft           # draft | reviewed | approved | superseded
version: 1.2
created: 2026-08-14
updated: 2026-08-16
authors: [architect]
related:
  - docs/prd/prd-user-auth.md
---
```

### 덮어쓰기 vs 누적

| 문서 | 정책 |
|------|------|
| `test/test-report.md` | **덮어쓰기** — 최신 결과만 의미 있음 |
| `report/` 진행 보고 | **덮어쓰기** |
| PRD, Tech Spec, 설계서 | **버전 증가 후 갱신** |
| ADR | **불변** — 뒤집을 때는 새 ADR + 이전 것을 `superseded`로 |
| 리뷰 결과 | **누적** — 게이트 이력이 감사 근거 |

## 작업 공간 기록

```
_workspace/
├── walkthrough.md              ★ 복구 진입점
└── {slug}/
    ├── state.json              기계 판독 상태
    ├── 00_input/ 01_planning/ 02_analysis/ 03_plan/ 04_design/
    ├── 05_implement/ 06_test/ 07_review/ 08_deploy/ 99_gate/
```

**파일 명명:** `{순번}_{에이전트}_{산출물}.{확장자}`
예: `02_codebase-analyst_impact.md`

### 산출물 자기 기술

각 파일 상단에 한 줄을 남긴다. 다른 에이전트가 컨텍스트 없이 파일만 읽고도
신뢰도를 판단할 수 있어야 한다.

```markdown
<!-- stage: 02_analysis | agent: codebase-analyst | slug: user-auth
     input: 01_planning/prd-draft.md | updated: 2026-08-14 11:40 -->
```

## walkthrough.md 갱신

**세션이 끊겨도 이어서 할 수 있게 하는 것이 유일한 목적이다.**

### 갱신 시점 (예외 없음)

1. 단계 시작 직전
2. 단계 완료 직후
3. 게이트 판정 직후 (통과·반려 모두)
4. 사용자 결정이 필요한 항목 발생 시
5. 승격 승인 직후
6. **에러로 중단될 때 — 중단 사유와 재개 지점**

> "나중에 한 번에 정리"는 이 파일의 목적을 무효화한다.
> 갱신을 미루면 세션이 끊긴 순간의 상태가 정확히 유실된다.

### 필수 구조

```markdown
# Walkthrough

## 현재 작업

| 항목 | 값 |
|------|-----|
| slug | user-auth |
| 단계 | 04_design |
| 상태 | in_progress |
| 담당 | architect |
| 마지막 갱신 | 2026-08-14 14:32 |
| 다음 행동 | 도메인 모델 다이어그램 완성 후 G4 진입 |

## 진행 로그

| 시각 | 단계 | 이벤트 | 행위자 | 산출물 / 비고 |
|------|------|--------|--------|-------------|
| 2026-08-14 10:05 | 01_planning | 완료 | planner-interviewer | `01_planning/prd-draft.md` |
| 2026-08-14 11:45 | gate:analysis | **반려** | doc-reviewer | 외부 인증 연동 리스크 누락 |

## 미결정 사항

| # | 내용 | 결정 필요 시점 | 상태 |
|---|------|--------------|------|
| 1 | 세션 저장소 Redis vs DB | 설계 완료 전 | ADR-0003 작성 중 |

## 승격 이력

| 시각 | 원본 | 승격 경로 | 승인 |
|------|------|----------|------|
| 2026-08-14 10:10 | `01_planning/prd-draft.md` | `docs/prd/prd-user-auth.md` | 사용자 승인 |
```

### state.json

`walkthrough.md`(사람용 서사)와 **항상 함께** 갱신한다.

```json
{
  "slug": "user-auth",
  "updated": "2026-08-14T14:32:00+09:00",
  "execution_mode": "balanced",
  "mode_source": "config",
  "current_stage": "04_design",
  "stage_status": "in_progress",
  "ddd_level": 2,
  "stages": {
    "01_planning": { "status": "passed", "gate_attempts": 1 },
    "02_analysis": { "status": "passed", "gate_attempts": 2 },
    "04_design":   { "status": "in_progress", "gate_attempts": 0 }
  },
  "tasks": { "total": 12, "done": 0 },
  "open_decisions": ["ADR-0003"]
}
```

`stage_status`: `pending` | `in_progress` | `in_review` | `rejected` | `passed`

**불일치 시 walkthrough.md를 정본으로 삼는다.**

## 세션 복구

1. `_workspace/walkthrough.md` 존재 확인 — 없으면 신규 작업
2. "현재 작업" 표에서 slug·단계·상태·다음 행동을 읽는다
3. `state.json`으로 교차 확인
4. **해당 단계 디렉토리의 산출물 파일로 실제 완료 지점을 판정한다**
   — walkthrough가 "완료"라 해도 파일이 없으면 미완료다
5. 사용자에게 재개 지점을 보고하고 확인받는다

```markdown
이전 작업을 발견했습니다.

- 작업: user-auth
- 마지막 단계: 04_design (진행 중)
- 다음 행동: 도메인 모델 다이어그램 완성 후 G4 진입
- 미결정: ADR-0003 (세션 저장소 선택)

이어서 진행할까요? (이어서 / 이 단계부터 다시 / 새 작업)
```

## 승격 절차

### 판정

| 승격한다 | 승격하지 않는다 |
|---------|---------------|
| 향후 구현·운영의 근거가 되는 결정 | 중간 탐색 로그, 시행착오 |
| 외부가 참조할 계약·스펙 | 에이전트 간 임시 메모 |
| 재현이 어려운 분석 결과 | 재실행하면 다시 얻는 산출물 |
| 리뷰에서 승인된 산출물 | 반려된 초안 |

### 절차

1. 단계 종료 시 승격 후보를 선별한다
2. **사용자에게 제시하고 승인을 받는다 — 자동 승격 금지**
3. 승인된 문서를 **템플릿 형식으로 재작성**하여 배치한다
   (원문 복사가 아니다. 작업 로그와 참조 자산은 형식과 밀도가 다르다)
4. `walkthrough.md`의 승격 이력에 기록한다

### 제시 형식

```markdown
## 승격 후보 (기획 단계)

| # | 원본 | 제안 경로 | 사유 |
|---|------|----------|------|
| 1 | `_workspace/user-auth/01_planning/prd-draft.md` | `docs/prd/prd-user-auth.md` | 이후 모든 단계의 기준 문서 |
| 2 | `_workspace/user-auth/01_planning/interview-log.md` | (승격 안 함) | 재현 가능한 대화 로그 |

승격을 진행할까요? (번호로 선택 / 전체 / 없음)
```

## 보존

- `_workspace/`를 **삭제하지 않는다.** 커밋되지 않아도 로컬 감사 추적의 근거다
- 같은 slug로 새 실행 시 기존을 `_workspace/{slug}_{YYYYMMDD_HHMMSS}/`로 이동
- 정리는 사용자가 명시적으로 요청할 때만

## 다이어그램

**텍스트 기반(Mermaid)만 사용한다.** AI가 파싱하고 사람이 읽어야 하며,
렌더링되지 않는 환경에서도 소스가 읽힌다.

| 용도 | 타입 |
|------|------|
| 계층·모듈 의존 | `flowchart` |
| 호출 순서 | `sequenceDiagram` |
| 상태 전이 | `stateDiagram-v2` |
| 도메인 모델 | `classDiagram` |
| DB 스키마 | `erDiagram` |
| 일정·임계 경로 | `gantt` |

규칙: 한 다이어그램에 한 관점 / 노드 15개 이하 / **바로 아래 3줄 이내 설명 필수** /
레이블은 용어집·코드 식별자와 일치.
