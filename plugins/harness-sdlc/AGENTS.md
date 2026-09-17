<!-- harness-source-repo -->
# AGENTS.md

이 디렉터리는 개발 하네스 플러그인의 소스다. 하네스 개선을 수행하며,
검증용 프로젝트는 임시 디렉터리에 만든다.

## 수정 위치

| 변경 | 정본 |
|---|---|
| 자산·프로젝트 경로, 설정 적용 | `harness/runtime.md` |
| 프로젝트 초기화 | `skills/harness-init/SKILL.md`, `harness/project-profile.md` |
| 기본 설정 | `harness/defaults.json` |
| 단계·게이트·롤백 | `harness/pipeline.md` |
| 실행 모드 | `harness/execution-modes.md` |
| 원칙 | `harness/principles/` |
| 역할 / 스킬 | `agents/` / `skills/` |
| 문서 템플릿 | `docs/template/` |
| 운영 안내·라우팅 | `harness/entrypoints/AGENTS.md` |
| 프로필 도구 / 검증 | `harness/bin/project.py` / `harness/bin/verify.py` |

## 검증과 기록

- 스킬 추가·삭제 시 운영 라우팅 표를 갱신한다.
- 공통 내용을 복제하지 않고 정본을 참조한다.
- `bash harness/bin/verify.sh`와 관련 `tests/`를 실행한다.
- 패키지 매니페스트와 스킬 검증을 수행한다.
- `CLAUDE.md` 변경 이력에 날짜·변경·사유를 기록한다.

마켓플레이스 설치가 기본이다. 프로젝트에는 .harness 설정과 실제 산출물만 생성한다.
이 파일과 소스 루트 CLAUDE.md는 프로젝트에 배포하지 않는다.
