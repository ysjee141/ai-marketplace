# Claude Code 어댑터

Claude Code에서 이 하네스를 운영하는 방법. 멀티 에이전트 기능을 활용한
최적 구성이며, 하네스의 **레퍼런스 구현**이다.

## 1. 파일 매핑

| 하네스 자산 | Claude Code 위치 | 성격 |
|------------|-----------------|------|
| 원칙·파이프라인 | `harness/principles/`, `harness/pipeline.md` | 도구 중립 SOT. 그대로 사용 |
| 역할 정의 | `.claude/agents/*.md` | Claude Code 네이티브 |
| 절차 지식 | `.claude/skills/*/SKILL.md` | Claude Code 네이티브 |
| 진입점 | `CLAUDE.md` | 트리거 규칙 + 변경 이력만 |
| 문서 템플릿 | `docs/template/` | 도구 중립 |

에이전트·스킬 파일은 하네스 본문을 중복 기술하지 않는다.
원칙이 필요하면 `Read`로 `harness/principles/*.md`를 로드한다 —
progressive disclosure로 컨텍스트를 아낀다.

## 2. 실행 모드

Claude Code는 세 모드를 모두 지원한다 (`harness/execution-modes.md`).
아래 표는 **`agent` 모드**의 구성이다. `skill`·`balanced` 모드의 수행 주체는
`execution-modes.md` 2절 표를 따른다.

| 단계 | `agent` 모드 위임 | 근거 |
|------|------------------|------|
| 01 기획 | **메인 세션 직접** | 사용자와의 대화가 본질. 서브 에이전트는 사용자에게 질문할 수 없다 |
| 02 분석 | **에이전트 팀** | 기획분석·개발분석이 서로의 발견으로 방향을 수정한다 |
| 03 계획 | **서브 에이전트** (순차 2개) | tech-spec → wbs 강한 순차 의존. 팀 통신 이득 없음 |
| 04 설계 | **서브 에이전트** (단일) | 단일 전문가 작업 |
| 05 구현 | **에이전트 팀** | 경계면 계약 조율이 품질의 핵심. QA가 실시간으로 결함을 반환 |
| 06 테스트 | **서브 에이전트** (단일) | 독립 실행·보고 |
| 게이트 | **서브 에이전트** | 독립 판정. 생성자와 분리되어야 편향이 없다 |
| 07 배포 | **서브 에이전트** (단일) | 단일 전문가 작업 |

> 세션당 팀은 하나만 활성화된다. 02 분석 팀은 `TeamDelete`로 정리한 뒤
> 05 구현 팀을 새로 만든다. 산출물은 `_workspace/`에 남으므로 단절이 없다.

## 3. 팀 구성 규약

### 02 분석 팀

```
TeamCreate(
  team_name: "analysis-team",
  members: [
    { name: "research-analyst",  agent_type: "research-analyst",  model: "opus",
      prompt: "PRD: _workspace/{slug}/01_planning/prd-draft.md 를 읽고 기획분석 수행." },
    { name: "codebase-analyst",  agent_type: "codebase-analyst",  model: "opus",
      prompt: "동일 PRD 기준 개발분석·리스크 평가 수행." }
  ]
)
```

**통신 규칙:** `codebase-analyst`가 기술 제약을 발견하면 즉시
`research-analyst`에게 `SendMessage`로 전달한다 (요구사항 실현 가능성에 영향).
반대로 `research-analyst`가 경쟁 제품·표준을 발견하면 구현 난이도 재평가를 요청한다.

### 05 구현 팀

Task 목록에서 **실제 필요한 영역만** 팀원으로 구성한다.
백엔드만 있는 프로젝트에 프론트 에이전트를 넣지 않는다.

```
TeamCreate(
  team_name: "impl-team",
  members: [ /* 필요 영역 에이전트 + network-engineer + qa-inspector */ ]
)
TaskCreate(tasks: [ /* 03_plan/tasks.md 의 Task를 그대로 등록, depends_on 반영 */ ])
```

**팀원 수 상한 6명.** 초과하면 Task를 묶어 담당을 통합한다
(조율 오버헤드가 이득을 상쇄한다).

**통신 규칙:**
- `network-engineer`가 API 계약을 확정하면 생산자·소비자 **양쪽**에 브로드캐스트
- `qa-inspector`는 결함 발견 시 관련된 **모든** 에이전트에게 파일:라인과
  수정 방법을 함께 보낸다
- 다른 팀원의 산출물이 필요하면 리더를 거치지 말고 직접 `SendMessage`로 요청

## 4. 모델·타입 선택

모든 에이전트는 `model: "opus"`를 사용한다.

| 에이전트 | subagent_type | 근거 |
|---------|--------------|------|
| 분석·리뷰 계열 | 커스텀 (`Explore` 기반 성격) | 코드 변경 방지가 바람직하나, 검증 스크립트 실행이 필요하므로 커스텀 유지 |
| `qa-inspector` | 커스텀 (general-purpose 성격) | Grep·스크립트 실행 필요. `Explore`로는 검증 불가 |
| 구현 계열 | 커스텀 | 파일 수정 필요 |

## 5. 스킬 트리거

오케스트레이터 스킬(`sdlc-orchestrator`)이 진입점이다.
개별 스킬은 오케스트레이터가 각 에이전트 프롬프트에서 명시적으로 지시하거나,
사용자가 직접 호출한다.

| 사용자 발화 | 트리거 |
|-----------|--------|
| "이 기능 만들어줘", "개발 시작", "파이프라인 돌려줘" | `sdlc-orchestrator` |
| "PRD 써줘", "요구사항 정리하자" | `requirements-interview` |
| "설계해줘", "아키텍처 잡아줘" | `architecture-design` |
| "테스트 돌리고 리포트 줘" | `test-execution` |
| "리뷰해줘" | `review-gate` |
| "CI 구축해줘" | `cicd-setup` |

## 6. 권한·훅 고려사항

- E2E 테스트는 headless로만 실행한다 (`harness/principles/testing.md` 3절).
  브라우저 창을 띄우는 명령은 실행하지 않는다
- 배포 관련 명령(`deploy`, `push --force`, 프로덕션 마이그레이션)은
  **사용자 승인 없이 실행하지 않는다**
- `_workspace/`는 `.gitignore` 대상이다. 커밋 시 포함되지 않음을 전제로
  승격 절차를 따른다
