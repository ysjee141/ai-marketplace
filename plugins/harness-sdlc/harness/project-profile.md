# 프로젝트 프로필 형식 (schema_version 1)

프로젝트마다 `.harness/project.json` 하나를 둔다. 다음은 **초기 초안**이며,
init 인터뷰 결과로 값을 채운다. `settings`에는 기본값과 다른 결정만 저장한다.

```json
{
  "schema_version": 1,
  "status": "draft",
  "purpose": "",
  "success_criteria": [],
  "constraints": [],
  "work_types": [],
  "context_sources": [],
  "open_questions": [],
  "extensions": [],
  "settings": {}
}
```

| 필드 | 규칙 |
|---|---|
| status | draft 또는 ready. 인터뷰가 중단되면 draft로 유지 |
| purpose | 하네스를 사용하는 목적. ready에서는 비어 있으면 안 됨 |
| success_criteria | 확인 가능한 완료 기준 문자열 목록. ready에서는 하나 이상 |
| constraints | 유지할 호환성·금지 범위·기한 등 |
| work_types | feature, bugfix, refactor, docs, cicd 중 하나 이상(ready) |
| context_sources | 판단에 사용한 프로젝트 상대 경로·문서 URL. 비밀값 저장 금지 |
| open_questions | 다음 운영을 막는 미결정 질문. ready에서는 비어 있어야 함 |
| extensions | `.harness/` 안에 있는 추가 Markdown 파일의 프로젝트 상대 경로 |
| settings | `harness/defaults.json`과 동일한 키의 부분 객체. 알 수 없는 키는 오류 |

`context.md`에는 인터뷰 답변·관찰 근거·가정·결정 이유를 기록한다.
`rules.md`에는 프로젝트별 경계·게이트 추가 체크리스트·역할별 절차를 기록한다.
둘 다 Git으로 공유할 수 있는 장기 지식이다. 입력에 시크릿이 있으면 원문을 저장하지 않는다.

## 설정 제약

- execution_mode: skill / balanced / agent / ask
- coverage_thresholds: 각 값은 0~100 숫자. 하향 결정은 context.md에 근거를 남긴다.
- gate: 양의 정수. max_retries는 **연속 REJECT 횟수의 상한**(상한 도달 시 중단).
- suggest_thresholds: 양의 정수. auto_suggest_mode가 false면 모드 재제안을 생략한다.
- architecture_rules: A1~A9 중 선택. 실제 규칙 정의와 프로젝트 적합성을 함께 확인한다.
- docs.promote_requires_approval: 승인 확인 여부. true여도 이미 받은 승인은 재사용한다.
- docs.workspace_retention: keep / archive. archive는 완료한 작업을
  `_workspace/archive/{slug}-{timestamp}/`로 옮기고 walkthrough의 위치를 갱신한다. 삭제하지 않는다.
- project.ddd_level: auto / 0 / 1 / 2 / 3 (문자열)
- project.roles: 사용할 `agents/` 파일 이름(확장자 제외) 목록. 빈 목록은 작업별 선택.
- project.test_commands: architecture / unit / integration / e2e / coverage의 명령 문자열.
  빈 문자열은 미확인이다. 실행할 명령을 추측해서 채우지 않는다.
- project.ci_provider: unspecified / github-actions / gitlab-ci / jenkins / other
- project.autonomy: analysis / implementation / delivery. 선호 범위이며 외부 작업 허가는 아님.
- project.document_scope: required / full. required는 선택한 경로의 필수 산출물만,
  full은 해당 경로에서 적용 가능한 보조 문서까지 작성한다.

## 재실행·업데이트·이전 버전

`init` 보조 명령은 존재하는 파일을 덮어쓰지 않는다. 프로필 수정은 기존 값을 읽고
사용자가 바꾸려는 필드만 편집한다. 같은 입력으로 다시 init하면 파일 내용이 바뀌지 않는다.
중단된 인터뷰는 open_questions에서 재개한다. 새 작업을 위해 프로젝트 프로필을 초기화하지 않는다.

플러그인 업데이트는 `.harness/`와 `_workspace/`에 쓰지 않는다. schema_version이
지원 범위를 벗어나면 중단하고 명시적 마이그레이션을 수행한다. 임의로 버전을 낮추지 않는다.
기존 복사 설치의 `harness/config.yml`·진입 문서가 있으면 init에서 설정·수정 내역을 읽어
프로필에 이관할 후보를 제시한다. 원본은 유지하고 `.harness/` 전환 후 사용하지 않는다.
같은 이름의 로컬 스킬과 플러그인 스킬이 공존하면 플러그인 스킬을 명시해 호출한다.
