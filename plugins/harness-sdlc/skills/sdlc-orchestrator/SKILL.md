---
name: sdlc-orchestrator
description: "Harness로 기능 개발·버그 수정·리팩터링의 단계, 검증, 상태 기록을 운영한다. 파이프라인 실행, 이어서 진행, 재실행, 이전 결과 업데이트·수정·보완에 사용한다. 하네스 자체의 최초 설정·운영 규칙 변경은 harness-init을 사용한다. 단순 설명·조회 요청을 개발 작업으로 확대하지 않는다."
---

먼저 [공통 실행 규약](../../harness/runtime.md)을 읽고 플러그인 자산 경로와 프로젝트 운영 프로필을 적용한다.

# SDLC Orchestrator

## 0. 프로젝트 컨텍스트

1. 사용자가 지정한 프로젝트 루트를 확인한다. 플러그인 디렉터리에 산출물을 만들지 않는다.
2. `.harness/project.json`이 없거나 draft면 `harness-init`으로 설정·인터뷰를 재개한다.
   프로젝트 운영 목적을 설정하는 과정이며 개별 기능 PRD 인터뷰와 구분한다.
3. ready 프로필, context.md, rules.md와 extensions를 읽는다.
4. `_workspace/walkthrough.md`와 해당 slug의 state.json을 확인한다.
   사용자가 재개를 요청했으면 실제 산출물 존재를 확인한 뒤 재개 지점을 보고하고 진행한다.
   여러 작업 중 대상이 불명확할 때만 선택을 묻는다.
5. 새 작업은 새 slug를 사용한다. 같은 slug로 처음부터 요청하면 기존 작업 폴더를
   timestamp를 붙여 보존한다. 파일을 삭제하거나 기존 작업 상태를 초기화하지 않는다.

## 1. 설정과 실행 범위

신규 작업은 runtime.md의 resolve 절차로 유효 설정을 만들고
`_workspace/{slug}/effective-config.json`에 저장한다.
기존 작업은 저장된 설정으로 재개한다. 스냅샷이 없는 이전 작업은 기존 기록과
프로필을 비교해 설정을 구성하고 그 한계를 기록한다.

- 모드 우선순위: 사용자 명시 지시 > 작업 설정 > 프로젝트 settings > 기본값.
- `ask`는 사용자가 아직 정하지 않은 경우에만 모드를 묻는다.
- `skill`: 메인이 역할을 순차 수행하고 별도 검토 단계에서 파일 기반 체크리스트로 리뷰.
- `balanced`: 생성·구현은 메인, 게이트와 통합 QA는 가능한 경우 별도 에이전트에 위임.
- `agent`: 독립적인 분석·구현은 병렬, 의존 단계는 순차로 위임.
- 실제 위임 기능·권한이 없으면 skill 방식으로 수행한다. 요청 모드와 실제 모드,
  전환 근거를 state.json에 기록한다. 호스트 기본 모델·동시 실행 한도를 따른다.
- `project.roles`는 우선 사용할 역할이다. 추가 역할이 필요하면 이유를 기록한다.
- `project.autonomy`와 실제 요청 범위가 분석까지만이면 구현·배포로 확대하지 않는다.

## 2. 작업 준비

목적·현재 요청을 바탕으로 실행 경로를 선택하고 보고한다.

| 작업 | 기본 경로 |
|---|---|
| feature | 01 → G1 → 02 → G2 → 03 → G3 → 04 → G4 → 05 → 06 → G5 → 선택적 07 → G6 |
| bugfix | 02 개발분석 → 05 → 06 → G5 |
| refactor | 02 → 04 → G4 → 05 → 06 → G5 |
| docs | 02 → G2 |
| cicd | 07 → 설정 검증 → 적용 가능한 최종 리뷰 |

이미 사용자가 선택한 경로나 범위는 재승인받지 않는다. 영향이 큰 범위 변경은 먼저 제시한다.
코드 변경에는 구현 테스트·실행 결과·G5가 필요하다. 적용하지 않는 단계·게이트는
state.json에 skipped와 사유를 남긴다. 문서 작업에 코드 게이트를 강제하지 않는다.
`project.document_scope`에 따라 선택한 경로의 필수 문서 또는 적용 가능한 보조 문서를 만든다.

`_workspace/{slug}/00_input/`에 필요한 입력을 저장하고 state.json·walkthrough를 초기화한다.
시크릿은 입력 원문·인터뷰 로그에 저장하지 않는다.

## 3. 단계 실행

각 단계는 역할 파일 `agents/{role}.md`와 해당 스킬을 읽어 수행한다.
자산 경로는 플러그인 루트, 표의 산출물은 프로젝트 `_workspace/{slug}/` 기준이다.

| 단계 | 역할 / 스킬 | 산출물 | 다음 검증 |
|---|---|---|---|
| 01 | planner-interviewer / requirements-interview | 01_planning/prd-draft.md | G1 |
| 02 | research-analyst / research-analysis, codebase-analyst / codebase-analysis | 02_analysis/*.md | G2 |
| 03 | tech-spec-writer / tech-spec-authoring → wbs-planner / wbs-cpm-planning | 03_plan/tech-spec.md, adr/, wbs.md, tasks.md | G3 |
| 04 | architect / architecture-design, architecture-guard | 04_design/design.md, api-contract.md, 적용 시 glossary.md | G4 |
| 05 | 필요한 구현 역할 / implementation-playbook | 코드·테스트, 05_implement/impl-notes-*.md | 모듈별 QA |
| 06 | test-engineer / test-execution | 06_test/test-report.md, raw/, 프로젝트 docs/test/test-report.md 최신 사본 | G5 |
| 07 | devops-engineer / cicd-setup | CI/CD 설정, 08_deploy/cicd-notes.md | G6(전체 경로) |

### 분석과 계획

- 병렬 분석은 발견을 공유하고, 순차 분석은 두 파일을 대조한 교차 검토를
  02_analysis/_cross-review.md에 기록한다. 버그 분석에서 불필요한 외부 조사를 강제하지 않는다.
- ADR 결정은 사용자의 기존 지시·위임 범위를 반영한다. 새 선택이 필요한 항목만 묻는다.
- WBS 후 auto_suggest_mode가 true이면 suggest_thresholds의 조건으로 모드 변경을 제안한다.
  상향은 조건 중 하나, 하향은 조건 모두 충족할 때 제안한다. 동의 없이 비용을 늘리지 않는다.

### 설계와 구현

- project.ddd_level이 auto면 DDD 원칙에 따라 판정한다. 값이 있으면 그 결정과 근거를 따른다.
- architecture_rules의 적용 여부와 프로젝트 추가 검증 규칙을 확정한다.
  프로젝트에 없는 계층·요소는 해당 없음으로 기록한다.
- Task 의존 관계를 지킨다. 순차 실행에서는 경계면 공유 Task를 연속 배치한다.
- 구현 시 해당 영역 references만 읽는다. 역할별 파일 소유 범위를 나눠 충돌을 줄인다.
- 계약 변경은 05_implement/_messages.md에 기록하고 생산자·소비자 양쪽에 전달한다.
- 각 모듈 완성 직후 qa-inspector / integration-qa로 경계면을 검증한다.
- 테스트는 확인된 명령으로 실행한다. 미실행은 INCOMPLETE이며 PASS로 처리하지 않는다.

### 배포

배포 조건이 없으면 07을 skipped로 기록한다.
CI 구성 요청과 실제 환경 배포 요청을 구분한다. profile의 delivery는 배포 허가가 아니다.

## 4. 게이트와 롤백

`skills/review-gate/SKILL.md`와 해당 리뷰어 체크리스트를 사용한다.
판정 전에 작업의 effective-config.json과 프로젝트 추가 규칙을 전달한다.

| 게이트 | 리뷰어 |
|---|---|
| G1~G4 | doc-reviewer (G4는 아키텍처 체크 포함) |
| G5 | code-reviewer + qa-inspector 결과 |
| G6 | doc-reviewer + code-reviewer |

여러 리뷰어의 출력은 `99_gate/{gate}-{reviewer}-r{N}.md`로 분리한다.
오케스트레이터가 결과를 합쳐 `99_gate/gate-{stage}-r{N}.md`에 최종 판정을 남긴다.
중복 지적은 하나로 계산하고 원본 리뷰 링크를 남긴다.

- BLOCKER/MAJOR 기준은 유효 설정의 gate.blocker_rejects / major_rejects를 사용한다.
- 필수 검증이 미실행이면 통과시키지 않는다. INCOMPLETE 이유와 재개 조건을 기록한다.
- REJECT는 결함 발생 단계로 롤백한다. 이후 단계·게이트는 pending으로 무효화한다.
  예전 파일의 존재만으로 완료 판정을 복원하지 않는다.
- gate.max_retries만큼 연속 REJECT하면 자동 재작업을 중단하고 원인·선택지를 보고한다.
  gate_attempts(전체 라운드)와 consecutive_rejects(연속 반려)를 구분하며 PASS 시 후자를 0으로 한다.
- 리뷰어가 실패하면 누락을 통과로 간주하지 않는다. 재시도 또는 허용된 순차 검토로 대체하고 기록한다.

G6는 전 단계 추적성, 최신 코드의 검증 근거, **승격 후보의 내용**을 확인한다.
아직 docs에 복사하지 않은 것을 반려 사유로 삼지 않는다.

## 5. 승격과 완료

1. harness-docs로 승격 후보를 정리한다. docs.promote_requires_approval이 true면
   기존 승인을 확인하고 부족한 범위만 묻는다.
2. 승인된 범위의 문서를 공통 템플릿으로 정리해 프로젝트 docs에 배치한다.
3. 대상 경로·내용·승격 기록을 확인한다. 실패하면 완료하지 않고 재개 지점을 기록한다.
4. 코드 변경 작업은 `docs/report/completion-{slug}.md`에 결과·검증·미해결 사항을 작성한다.
   단독 분석·문서 요청은 요청된 산출물로 마무리한다.
5. 프로세스 개선은 프로젝트 전용이면 .harness/rules.md와 context.md에,
   공통 개선이면 제안으로 남긴다. 플러그인 캐시를 직접 수정하지 않는다.
6. state.json을 completed로 갱신한다. docs.workspace_retention에 따라 keep 또는
   archive하고 walkthrough에 최종 위치를 기록한다. 삭제하지 않는다.

## 상태와 복구

상태 형식은 `harness/principles/workspace.md`를 따른다.
단계 시작·완료, 판정, 사용자 결정, 승격, 오류 중단마다 파일을 갱신한다.
위임 시 프로젝트 루트·slug·입출력 파일·유효 설정·추가 규칙·역할 범위를 전달한다.
파일이 없거나 검증 대상 코드가 바뀌었으면 관련 검증을 무효화하고 필요한 범위만 다시 수행한다.

| 상황 | 대응 |
|---|---|
| init 인터뷰 미완료 | draft와 open_questions를 보존하고 필요한 답변 대기 |
| 프로필 스키마 미지원 | 원본 보존, 명시적 마이그레이션 필요 보고 |
| 산출물·검증 근거 누락 | 해당 단계를 미완료로 유지 |
| 사용자가 작업 범위 변경 | 영향받는 단계·설정을 갱신하고 사유 기록 |
| 서브에이전트 실패 | 제한된 재시도 후 대체 수행 또는 중단 사유 보고 |
| 도구·환경 부재 | 미실행과 한계를 명시하고 가능한 독립 작업 수행 |
