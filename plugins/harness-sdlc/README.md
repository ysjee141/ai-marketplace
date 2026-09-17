# Harness SDLC

마켓플레이스에서 설치하고 프로젝트에서 `harness-init`으로 설정하는 개발 하네스다.
목적·완료 기준·제약을 인터뷰하고, 프로젝트 운영 프로필에 맞춰
기획→분석→계획→설계→구현→테스트→리뷰→배포를 수행한다.

## 시작하기

1. 이 저장소의 마켓플레이스에서 `harness-sdlc` 플러그인을 설치한다.
2. 대상 프로젝트의 새 대화에서 **“harness-init으로 이 프로젝트의 하네스를 설정해줘”**라고 요청한다.
   Claude Code에서는 `/harness-sdlc:harness-init`으로 명시 호출할 수 있다.
3. 기존 코드·문서를 조사한 뒤 필요한 질문에 답한다.
4. 생성된 `.harness/`의 목적·운영 규칙을 확인하고 작업을 요청한다.

별도 셸 설치가 필요하지 않다. `install.sh`는 이전 사용자에게 전환 방법만 안내하며
프로젝트에 파일을 복사하지 않는다. init의 파일 생성·검증용 Python 보조 도구는
에이전트가 호출할 수 있으며 Python이 없어도 스킬의 문서 절차로 설정할 수 있다.

## 저장 위치

| 위치 | 내용 | 업데이트 |
|---|---|---|
| 플러그인의 `skills/`, `agents/`, `harness/`, `docs/template/` | 공통 절차·역할·기본값·템플릿 | 마켓플레이스 업데이트 |
| 프로젝트의 `.harness/` | 인터뷰, 프로젝트 설정, 추가 규칙 | init 또는 운영 규칙 변경 요청 |
| 프로젝트의 `_workspace/{slug}/` | 작업 상태·유효 설정 스냅샷·로그 | 단계별 기록 |
| 프로젝트의 `docs/` | 확정된 산출물 | 승격 절차 |

스킬 15개와 역할 17개를 제공한다. 패키지와 프로젝트의 경로 기준은
[harness/runtime.md](harness/runtime.md), 설정 형식은
[harness/project-profile.md](harness/project-profile.md)를 따른다.
프로젝트 규칙을 위해 플러그인 캐시를 수정하지 않는다.

## 재개·재설정·업데이트

- init 재실행: 기존 파일과 답변을 보존하고 미결정 또는 변경 요청만 처리한다.
- 작업 재개: 기존 작업의 상태와 `effective-config.json`을 사용한다.
- 플러그인 업데이트: `.harness/`를 유지한다. 호환되지 않는 프로필은 명시적으로 이관한다.
- 예전 셸 설치: 기존 설정·추가 지침을 읽어 `.harness/`로 이관한다. 원본은 자동 삭제하지 않는다.
  로컬에 남은 동일 이름 스킬과 혼동하지 않도록 플러그인 스킬을 명시해 호출한다.

## 개발 검증

Python 보조 도구에는 Python 3.10 이상이 필요하며 외부 패키지는 필요 없다.

```bash
bash harness/bin/verify.sh
python3 -m unittest discover -s tests -v
python3 harness/bin/project.py check /path/to/project --ready
```

마켓플레이스 등록 방법은 저장소 루트 README를 참고한다.
