# 하네스 개요

기획부터 배포까지 개발 전 주기를 통제하는 **도구 중립 개발 파이프라인 하네스**.

## 설계 의도

| 목표 | 수단 |
|------|------|
| 아키텍처 원칙을 코드까지 관철 | `principles/` + 실행 가능한 검증 테스트 |
| 토큰 예산에 맞춘 실행 | 실행 모드 3종 (`execution-modes.md`) |
| 코딩 에이전트 종류와 무관 | 도구 중립 SOT + 얇은 어댑터 |
| 결함의 하위 전파 차단 | 단계별 리뷰 게이트 + 근원 단계로 롤백 |
| 세션 단절 복구 | `_workspace/walkthrough.md` + `state.json` |
| 경계면 런타임 장애 예방 | 계약 확정 + 양쪽 동시 읽기 QA |
| 하네스 자체의 진화 | 실행마다 개선 도출 → 사용자 승인 → 반영 |

## 구조

```
harness/                         ★ 도구 중립 SOT
├── README.md                    이 파일
├── config.yml                   실행 모드·품질 기준 설정
├── pipeline.md                  단계·게이트·롤백 정의
├── execution-modes.md           skill / balanced / agent 모드 정의
├── principles/
│   ├── architecture.md          Clean Architecture, SOLID, 순수성
│   ├── ddd.md                   DDD 적용 수준 판정
│   ├── testing.md               테스트 전략, E2E silent, 커버리지
│   ├── documentation.md         /docs 규약, 승격 절차
│   └── workspace.md             /_workspace 규약, 세션 복구
├── adapters/
│   ├── claude-code.md           Claude Code 운영 (레퍼런스 구현)
│   └── generic-agent.md         범용 에이전트 운영
├── entrypoints/                 ★ 대상 저장소용 진입점 템플릿 (배포됨)
│   ├── CLAUDE.md                Claude Code 진입점 — 파이프라인 운영 규약
│   └── AGENTS.md                범용 도구 진입점 — 요청→스킬 라우팅 표
└── bin/
    ├── install.sh               대상 저장소에 설치
    └── verify.sh                구조 검증

.claude/agents/                  역할 정의 17종 (일반 마크다운)
.claude/skills/                  절차 지식 14종 (일반 마크다운)
docs/template/                   문서 템플릿 12종
CLAUDE.md / AGENTS.md            하네스 저장소 자신의 진입점 — 배포되지 않음
```

**루트 `CLAUDE.md`·`AGENTS.md`와 `entrypoints/`의 동명 파일은 역할이 다르다.**
루트는 "하네스를 어떻게 수정하는가", `entrypoints/`는 "파이프라인을 어떻게
운영하는가"를 담는다. 루트 문서를 대상 저장소에 복사하면 "여기서 애플리케이션을
개발하지 않는다" 같은 하네스 전용 지시가 대상 저장소 에이전트에게 전달되어
개발 작업 자체를 막는다.

**`.claude/` 디렉토리 이름은 Claude Code 관례를 따르지만, 안의 파일은
frontmatter가 붙은 일반 마크다운이다.** 어떤 도구에서든 그대로 읽힌다.

## 실행 모드

**동일한 파이프라인·게이트·산출물을 세 모드로 돌린다.** 모드는 "무엇을 하는가"가
아니라 **"누가 수행하는가"** 만 바꾼다.

| 모드 | 위임 범위 | 서브에이전트 | 적합 |
|------|----------|-------------|------|
| `skill` | 없음 — 메인 세션이 역할 순차 전환 | 0 | 토큰 절약, 소규모 변경, 서브에이전트 미지원 도구 |
| `balanced` | 게이트 리뷰 + 통합 QA만 | 3~7 | **기본** — 판정 독립성만 확보 |
| `agent` | 분석·구현은 팀, 나머지는 서브 | 12~25 | Task 15개 이상, 영역 3개 이상 |

`harness/config.yml`의 `execution_mode`가 기본값이고 사용자 지시가 우선한다.
03 계획(WBS) 완료 시 규모를 근거로 상향/하향을 **제안**한다(자동 전환하지 않음).

**모드를 낮춰서 게이트를 건너뛰거나 체크리스트를 줄이는 것은 허용되지 않는다.**
토큰이 부족하면 모드를 낮추거나 범위를 줄이되 기준은 유지한다.

상세·모드별 품질 보정 절차: `execution-modes.md`

## 파이프라인

```
01 기획 → G1 → 02 분석 → G2 → 03 계획 → G3 → 04 설계 → G4
       → 05 구현 + 06 테스트 → G5 → 07 배포 → G6 최종 → 승격 → 하네스 개선
```

게이트에서 반려되면 **결함이 발생한 단계**로 롤백한다 (직전 단계가 아닐 수 있다).
같은 게이트 3회 반려 시 자동 재작업을 중단하고 사용자에게 보고한다.

상세: `pipeline.md`

## 구성 요소

### 에이전트 17종

| 계열 | 에이전트 |
|------|---------|
| 기획 | planner-interviewer |
| 분석 | research-analyst, codebase-analyst |
| 계획 | tech-spec-writer, wbs-planner |
| 설계 | architect |
| 구현 | backend-engineer, frontend-web-engineer, frontend-app-engineer, frontend-desktop-engineer, database-engineer, network-engineer |
| 검증 | test-engineer, qa-inspector |
| 리뷰 | doc-reviewer, code-reviewer |
| 배포 | devops-engineer |

### 스킬 14종

`sdlc-orchestrator`(진입점) · `requirements-interview` · `research-analysis` ·
`codebase-analysis` · `tech-spec-authoring` · `wbs-cpm-planning` ·
`architecture-design` · `architecture-guard` · `implementation-playbook`(+6 reference) ·
`test-execution` · `integration-qa` · `review-gate` · `cicd-setup`(+3 reference) ·
`harness-docs`

## 설치

대상 저장소에 하네스를 복사한다.

```bash
harness/bin/install.sh /path/to/target-repo
```

설치되는 것: `harness/`, `.claude/agents/`, `.claude/skills/`, `docs/template/`,
`docs/` 하위 디렉토리, 도구별 진입 파일, `.gitignore` 항목.

### 도구별 진입 파일

| 대상 저장소의 파일 | 도구 | 원본 | 역할 |
|------|------|------|------|
| `AGENTS.md` | Codex CLI, Cursor(최신), Jules 등 | `harness/entrypoints/AGENTS.md` | **정본** — 요청→스킬 라우팅 표 포함 |
| `CLAUDE.md` | Claude Code | `harness/entrypoints/CLAUDE.md` | 트리거 규칙 + 변경 이력 |
| `GEMINI.md` | Gemini CLI | install.sh가 생성 | `AGENTS.md` 포인터 |
| `.cursor/rules/harness.mdc` | Cursor (규칙 방식) | install.sh가 생성 | 포인터 + `alwaysApply: true` |
| `.github/copilot-instructions.md` | GitHub Copilot | install.sh가 생성 | 포인터 |
| `CONVENTIONS.md` | Aider | install.sh가 생성 | 포인터 |

1차 진입 파일(`AGENTS.md`, `CLAUDE.md`)은 **하네스 저장소 루트가 아니라
`harness/entrypoints/`에서 복사된다.** `CLAUDE.md`의 `{{INSTALL_DATE}}`는
설치 날짜로 치환된다.

2차 진입 파일은 **내용을 복제하지 않고 `AGENTS.md`를 가리킨다.**
복제하면 두 벌이 되어 반드시 어긋나기 때문이다.

**범용 도구에는 스킬 자동 트리거가 없다.** `AGENTS.md`의 "요청 → 스킬 라우팅"
표가 Claude Code의 `description` 트리거를 대신한다.

기존 파일은 덮어쓰지 않는다. 진입 파일이 이미 있으면 "수동 병합 필요"로 보고하고,
그 외 파일이 다르면 `.harness-new` 접미사로 저장한다.

## 검증

```bash
harness/bin/verify.sh
```

검증 항목: 에이전트·스킬 frontmatter 유효성, 참조 경로 존재, 커맨드 미생성,
SKILL.md 500줄 제한, 진입점 존재.

## 불변 규칙

1. 모든 코드에 테스트가 존재한다 (같은 PR 안에)
2. E2E는 silent(headless)로만 실행한다
3. 실행하지 않은 것을 실행했다고 보고하지 않는다
4. `_workspace/`는 커밋되지 않는다 — 지속 참조가 필요하면 사용자 승인 후 승격
5. `walkthrough.md`를 단계·게이트마다 갱신한다
6. ADR 승인 없이 설계로 넘어가지 않는다
7. 게이트 3회 반려 시 자동 재작업을 중단하고 사용자에게 보고한다

## 하네스 진화

작업 완료 시 오케스트레이터가 **프로세스 자체의 개선점**을 도출하여 사용자에게
제시한다. 승인된 개선은 즉시 반영하고 `CLAUDE.md` 변경 이력에 기록한다.

수집 신호: 게이트 반복 반려 · 스킬 미사용 · 사용자 지적 반복 ·
산출물 형식 불일치 · 단계 지연 · 오케스트레이터 우회
