---
name: harness-init
description: "프로젝트에서 Harness를 처음 사용하거나 운영 목적·규칙을 변경할 때, 기존 저장소를 조사하고 인터뷰하여 프로젝트 운영 프로필을 만든다. '하네스 초기화', 'harness init', '이 프로젝트에 하네스 설정', '하네스 운영 방식 바꿔줘'에 사용. 개별 기능 PRD 작성은 requirements-interview, 진행 중 작업 재개는 sdlc-orchestrator를 사용한다."
---

# Harness Init

먼저 [실행 컨텍스트](../../harness/runtime.md)와
[프로필 형식](../../harness/project-profile.md)을 읽는다.
이 스킬 안에서는 프로필 부재를 이유로 자신을 재호출하지 않는다.

## 목표

마켓플레이스 설치 후 이 프로젝트의 **목적·완료 기준·제약·운영 규칙**을 정한다.
사용자는 별도의 설치 셸을 실행하지 않는다. 플러그인 자산을 프로젝트로 복사하지 않는다.
공통 절차 위에 프로젝트 설정과 필요한 추가 지침만 만든다.

## 1. 먼저 확인한다

- 대상 프로젝트 루트를 확정한다. 대화나 작업 환경에서 명확하면 재질문하지 않는다.
- `.harness/project.json`, 기존 AGENTS.md·CLAUDE.md, README, 기술 스택,
  테스트 명령, CI, 설계 문서·ADR을 필요한 범위에서 읽는다.
- ready 프로필이 있고 변경 요청이 없으면 설정을 검증하고 바로 사용한다.
- draft이면 기존 답변을 유지하고 open_questions의 미결정만 이어서 묻는다.
- 기존 복사 설치가 있으면 config와 사용자 변경 규칙을 이관한다. 원본 삭제는 init의 범위가 아니다.

## 2. 모르는 것만 인터뷰한다

한 번에 핵심 질문 1~3개를 묶는다. 기술 선택을 묻기 전에 목적·성공 기준을 확인한다.

| 영역 | 질문 예 | 반영 위치 |
|---|---|---|
| 목적 | 어떤 시스템에서 어떤 작업을 반복해서 처리할 것인가? | purpose, work_types |
| 성공 | 무엇을 확인하면 작업이 완료됐다고 볼 수 있는가? | success_criteria, rules.md |
| 제약 | 호환성·변경 금지 영역·업무 규칙·일정 제약은? | constraints, context.md |
| 운영 | 분석만 / 구현까지 / 전달까지 중 주 범위는? 리뷰 위임 선호는? | project.autonomy, execution_mode |
| 검증 | 기존 테스트와 CI 중 무엇이 완료 판정의 기준인가? | test_commands, coverage_thresholds, gate |
| 설계·문서 | 필요한 DDD 수준·역할·추가 체크리스트·문서 범위는? | ddd_level, roles, document_scope, extensions |

프로젝트에서 확인되는 값은 근거와 함께 제시한다. 사용자가 위임한 결정은 직접 정하고
이유를 기록한다. 이번 기능의 상세 요구사항 인터뷰를 여기서 반복하지 않는다.
답변 대기·세션 중단 시 지금까지의 답변과 남은 질문을 draft 프로필과 context.md에 저장한다.

## 3. 프로젝트 프로필을 만든다

Python 3.10 이상이면 보조 도구로 빈 초안을 만들 수 있다:

```text
python3 <plugin-root>/harness/bin/project.py init <project-root> --link
```

이 명령은 `.harness/project.json`, `context.md`, `rules.md`를 없을 때만 만들고,
`--link`는 기존 AGENTS.md·CLAUDE.md를 유지하며 짧은 하네스 안내 블록만 추가한다.
사용자가 진입 파일 수정을 원하지 않으면 --link를 생략한다. 다른 도구의 지침 파일은
실제로 사용하는 경우에만 동일한 짧은 안내를 병합한다. Python이 없으면 같은 파일을
프로필 형식대로 직접 작성하되 기계 검증을 미실행으로 보고한다.

- 인터뷰 답변을 project.json에 반영하고 settings에는 기본값과 다른 결정만 둔다.
- context.md에 관찰·답변·선택 이유·가정을, rules.md에 추가 운영 지침을 작성한다.
- 큰 프로젝트별 절차는 `.harness/` 하위 Markdown으로 분리하고 extensions에 등록한다.
- `_workspace/`를 사용할 때 프로젝트 `.gitignore`에 `/_workspace/`를 기존 내용 보존해 추가한다.
  `.harness/`는 공유할 설정이므로 제외하지 않는다.
- 운영을 막는 미결정을 해결하고 목적·완료 기준·작업 유형이 갖춰지면 status를 ready로 바꾼다.
  사용자가 이미 결정하거나 위임한 것을 다시 확인받지 않는다.

## 4. 점검하고 인계한다

```text
python3 <plugin-root>/harness/bin/project.py check <project-root> --ready
python3 <plugin-root>/harness/bin/project.py resolve <project-root>
```

check는 형식·참조를, resolve는 유효 설정을 확인한다. 테스트 명령 자체의 성공을 뜻하지 않는다.
목적, 선택한 운영 방식, 추가 규칙, 생성·변경 파일, 미검증 사항을 짧게 보고한다.
실제 작업도 요청받았다면 sdlc-orchestrator로 이어간다. init만 요청했다면 개발을 시작하지 않는다.

재설정은 해당 필드와 근거만 변경한다. 플러그인 버전이 바뀌었다는 이유로 인터뷰나
프로필을 초기화하지 않는다. 진행 중 작업에는 기존 effective-config 스냅샷을 유지한다.
