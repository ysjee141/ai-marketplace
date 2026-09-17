# AGENTS.md

이 저장소는 **개발 파이프라인 하네스**를 사용한다.
Codex, Cursor, Copilot, Gemini, Aider 등 모든 코딩 에이전트가 이 파일을 진입점으로 쓴다.

Claude Code를 쓴다면 `CLAUDE.md`를 대신 참조한다.

## 먼저 읽을 것

| 상황 | 읽을 파일 |
|------|----------|
| 하네스가 어떻게 동작하는지 | `harness/pipeline.md` |
| 실행 모드(누가 수행하는가) | `harness/execution-modes.md` |
| 설정값 (모드·커버리지 기준·게이트 임계) | `harness/config.yml` |
| 멀티 에이전트 기능이 없는 도구에서 운영 | `harness/adapters/generic-agent.md` |
| 설계·구현 판단 기준 | `harness/principles/architecture.md` |
| 문서를 어디에 둘지 | `harness/principles/documentation.md` |
| 진행 상태 기록·복구 | `harness/principles/workspace.md` |

## 작업 시작 절차

1. **`_workspace/walkthrough.md`를 먼저 확인한다.**
   존재하면 진행 중인 작업이 있다. 덮어쓰지 말고 재개 여부를 사용자에게 확인한다.
2. 작업 유형에 따라 실행 경로를 정한다 (`harness/pipeline.md` 5절).
3. **실행 모드를 확인한다.** 서브에이전트를 지원하지 않는 도구는 `skill` 모드로
   동작한다 (아래 "역할 전환 규칙"이 곧 `skill` 모드다). 서브에이전트를 지원한다면
   `harness/config.yml`의 `execution_mode`를 따르고, 사용자 지시가 우선한다.
4. 각 단계마다 역할을 선언하고 해당 정의·스킬을 읽는다.

```
현재 역할: codebase-analyst
참조: .claude/agents/codebase-analyst.md, .claude/skills/codebase-analysis/SKILL.md
입력: _workspace/{slug}/01_planning/prd-draft.md
출력: _workspace/{slug}/02_analysis/02_codebase-analyst_impact.md
```

> `.claude/` 디렉토리 이름은 Claude Code 관례를 따르지만, 안의 파일은
> frontmatter가 붙은 **일반 마크다운**이다. 어떤 도구에서든 그대로 읽힌다.

## 요청 → 스킬 라우팅

Claude Code는 각 스킬의 `description`으로 자동 트리거하지만, **다른 도구에는
자동 트리거 장치가 없다.** 아래 표가 그 역할을 대신한다.
사용자 요청이 어느 행에 해당하는지 판단하고, 해당 스킬의 `SKILL.md`를 읽고 따른다.

| 이렇게 말하면 | 읽을 스킬 |
|---|---|
| 만들어줘 / 개발해줘 / 구현해줘 / 작업 시작 / **이어서 해줘** / 재실행 | `sdlc-orchestrator` (전체 파이프라인 — 아래 단계 스킬을 순서대로 부른다) |
| PRD 써줘 / 요구사항 정리하자 / 뭘 만들지 정하자 | `requirements-interview` |
| 이거 가능한지 조사해줘 / 비슷한 사례 / 근거 찾아줘 | `research-analysis` |
| 고치면 뭐가 깨져 / 어디를 수정해야 해 / 영향 범위 / 리스크 | `codebase-analysis` |
| 기술 명세 / Tech Spec / ADR / 기술 결정 정리 | `tech-spec-authoring` |
| 작업 쪼개줘 / 순서 정해줘 / 일정 / 임계 경로 / Task 나눠줘 | `wbs-cpm-planning` |
| 설계해줘 / 아키텍처 / 계층 나눠줘 / 도메인 모델 / 다이어그램 | `architecture-design` |
| 의존 규칙 강제 / 계층 위반 막아줘 / 순환 의존 검사 | `architecture-guard` |
| 코드 짜줘 / API 구현 / 화면 구현 / 스키마 만들어줘 | `implementation-playbook` (+ 영역별 `references/`) |
| 테스트 돌려줘 / 커버리지 확인 / 테스트 리포트 | `test-execution` |
| `is not a function` / `Cannot read property` / 404 / 필드명 불일치 / 빌드는 되는데 런타임에 터짐 / 연동 확인 | `integration-qa` |
| 게이트 판정 / 설계서 검토 / PRD 리뷰 / 통과시켜도 되나 | `review-gate` |
| CI 구축 / 파이프라인 / 자동 배포 | `cicd-setup` |
| 문서 어디에 둘까 / 승격해줘 / walkthrough 갱신 / 지금 어디까지 했지 | `harness-docs` |

경로는 `.claude/skills/{이름}/SKILL.md`.

**제외 조건은 각 `SKILL.md`의 frontmatter `description`에 있다.**
표만 보고 판단이 애매하면 해당 스킬의 frontmatter를 먼저 읽어라. 특히:

- 브랜치 diff·PR 코드 리뷰는 `review-gate`가 아니다 (도구 자체 리뷰 기능 사용)
- "CPM이 뭐야" 같은 **개념 질의**는 스킬을 쓰지 않고 직접 답한다
- 산출물을 워드·PDF·엑셀·웹페이지로 **변환**하는 요청은 하네스 스킬이 아니다
- 중단된 작업을 **실제로 이어서 진행**하는 것은 `sdlc-orchestrator`,
  `harness-docs`는 상태 조회·기록만 담당한다

## 단계 → 역할 → 절차 매핑

| 단계 | 역할 정의 | 절차 (스킬) |
|------|----------|-----------|
| 01 기획 | `.claude/agents/planner-interviewer.md` | `.claude/skills/requirements-interview/SKILL.md` |
| 02 기획분석 | `.claude/agents/research-analyst.md` | `.claude/skills/research-analysis/SKILL.md` |
| 02 개발분석 | `.claude/agents/codebase-analyst.md` | `.claude/skills/codebase-analysis/SKILL.md` |
| 03 계획 | `.claude/agents/tech-spec-writer.md` | `.claude/skills/tech-spec-authoring/SKILL.md` |
| 03 계획 | `.claude/agents/wbs-planner.md` | `.claude/skills/wbs-cpm-planning/SKILL.md` |
| 04 설계 | `.claude/agents/architect.md` | `.claude/skills/architecture-design/SKILL.md` |
| 05 구현 | `.claude/agents/{backend,frontend-web,frontend-app,frontend-desktop,database,network}-engineer.md` | `.claude/skills/implementation-playbook/SKILL.md` + 영역별 reference |
| 05 QA | `.claude/agents/qa-inspector.md` | `.claude/skills/integration-qa/SKILL.md` |
| 06 테스트 | `.claude/agents/test-engineer.md` | `.claude/skills/test-execution/SKILL.md` |
| 게이트 | `.claude/agents/{doc,code}-reviewer.md` | `.claude/skills/review-gate/SKILL.md` |
| 07 배포 | `.claude/agents/devops-engineer.md` | `.claude/skills/cicd-setup/SKILL.md` |
| 공통 | - | `.claude/skills/harness-docs/SKILL.md`, `.claude/skills/architecture-guard/SKILL.md` |

## 역할 전환 규칙

멀티 에이전트를 지원하지 않는 도구에서는 한 세션에서 역할을 전환한다.
그때 반드시:

1. 이전 역할의 산출물을 **파일로 저장**한다 (컨텍스트에만 두지 않는다)
2. 새 역할의 정의 파일과 스킬을 **다시 읽는다**
3. 새 역할은 이전 산출물을 **파일에서 읽어** 시작한다

파일 경유가 핵심이다. 컨텍스트로 넘기면 역할 경계가 흐려지고, 리뷰 역할이
자기 작업을 검토하는 자기 승인 편향이 발생한다.

## 리뷰 게이트 독립성

단일 에이전트가 생성과 리뷰를 모두 하면 판정이 관대해진다. 다음을 지킨다:

1. 리뷰는 **별도 턴**에서 수행한다. 생성 직후 같은 응답에서 판정하지 않는다
2. **산출물 파일만 읽고** 판정한다. 생성 과정의 추론을 참조하지 않는다
3. 체크리스트를 **항목별로 명시 판정**한다. "전반적으로 양호"는 판정이 아니다
4. **지적 사항 표를 먼저 쓰고 판정을 선언**한다

## 불변 규칙

1. **모든 코드에 테스트가 존재한다.** 같은 PR 안에.
2. **E2E는 headless로만 실행한다.** 창을 띄우는 명령을 실행하지 않는다.
3. **실행하지 않은 것을 실행했다고 보고하지 않는다.** 미실행은 미실행으로 명시한다.
4. **`_workspace/`는 커밋되지 않는다.** 지속 참조가 필요하면 사용자 승인 후 승격한다.
5. **`walkthrough.md`를 단계·게이트마다 갱신한다.**
6. **ADR 승인 없이 설계로 넘어가지 않는다.**
7. **게이트 3회 반려 시 자동 재작업을 중단하고 사용자에게 보고한다.**

## 기능이 없을 때

| 기대 기능 | 대체 |
|----------|------|
| 서브 에이전트·팀 | 역할 선언 후 순차 전환 |
| 에이전트 간 메시지 | `_workspace/{slug}/NN_stage/_messages.md` |
| 웹 검색 | 사용자에게 자료 요청. **추측으로 대체하지 않는다** |
| 파일 쓰기 | 내용을 제시하고 사용자에게 저장 요청 |

**기능이 없어서 수행하지 못한 검증은 누락으로 명시한다.**
수행한 것처럼 보고하지 않는다.
