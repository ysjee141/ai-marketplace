# Harness 운영 안내

이 문서는 플러그인 안의 라우팅 참고 자료다. 프로젝트에 통째로 복사하지 않는다.
프로젝트 진입 파일의 짧은 안내는 harness-init이 생성한다.
먼저 [공통 실행 규약](../runtime.md)을 읽는다.

## 시작과 재개

- 처음 사용하거나 운영 목적을 바꿀 때: `harness-init`.
- ready 프로필이 있으면 `.harness/project.json`, context.md, rules.md를 읽고 사용한다.
- 진행 중 작업은 `_workspace/walkthrough.md`, state.json, effective-config.json에서 재개한다.
- 사용자가 이미 재개를 요청했다면 재개 여부를 다시 묻지 않는다.
- 호스트가 스킬 자동 탐색을 지원하면 설치된 플러그인의 스킬을 사용한다.
  미지원 도구는 아래 표와 사용자가 제공한 패키지 위치로 스킬 파일을 읽는다.

## 요청 → 스킬 라우팅

| 요청 | 스킬 |
|---|---|
| 하네스 초기화 / 운영 목적·규칙 설정·변경 | `harness-init` |
| 기능 개발 / 버그 수정 / 리팩터링 / 이어서 진행 | `sdlc-orchestrator` |
| PRD / 개별 기능 요구사항 | `requirements-interview` |
| 가능성 조사 / 사례 / 외부 근거 | `research-analysis` |
| 기존 구조 / 영향 범위 / 리스크 | `codebase-analysis` |
| Tech Spec / ADR / 기술 결정 | `tech-spec-authoring` |
| WBS / 작업 분해 / 일정·임계 경로 | `wbs-cpm-planning` |
| 설계 / 아키텍처 / 도메인 모델 | `architecture-design` |
| 의존 규칙 / 순환 의존 검사 | `architecture-guard` |
| 구현 / API / 화면 / 스키마 | `implementation-playbook` |
| 테스트 실행 / 커버리지 / 테스트 리포트 | `test-execution` |
| 연동·경계면 정합성 검사 | `integration-qa` |
| 단계별 산출물의 통과·반려 판정 | `review-gate` |
| CI/CD 구성 | `cicd-setup` |
| 문서 승격 / 상태 조회·기록 | `harness-docs` |

스킬 파일은 플러그인 `skills/{name}/SKILL.md`, 역할은 `agents/{role}.md`.
단계·역할 매핑은 `harness/pipeline.md`를 따른다.
개념 설명이나 일반 질의를 파이프라인 실행으로 확대하지 않는다.

## 운영 원칙

검증 결과는 실행 근거로 보고하고, 미실행을 통과로 처리하지 않는다.
프로젝트 프로필은 실행 범위를 넘어서는 외부 작업의 허가가 아니다.
생성자와 검토자를 가능한 범위에서 분리하며, 위임 불가 시 별도 검토 단계에서
파일·체크리스트를 근거로 검토한다. 같은 세션의 검토를 독립 검증이라고 주장하지 않는다.
