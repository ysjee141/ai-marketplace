# 하네스 개요

공통 절차는 플러그인이 제공하고 프로젝트별 보완은 `.harness/`에 보관한다.
마켓플레이스 설치 → harness-init 인터뷰 → 프로젝트 프로필 → 작업 실행 순서다.

| 자산 (플러그인 루트 기준) | 역할 |
|---|---|
| `harness/runtime.md` | 자산·프로젝트 경로, 설정 우선순위, 호스트 기능, 업데이트 규약 |
| `harness/defaults.json` | 실행 모드·품질 기준의 단일 기본값 |
| `harness/project-profile.md` | 프로젝트 프로필과 설정 제약 |
| `harness/pipeline.md` | 단계·게이트·롤백 |
| `harness/execution-modes.md` | skill / balanced / agent 수행 방식 |
| `harness/principles/` | 아키텍처·DDD·테스트·문서·작업 상태 규약 |
| `harness/adapters/` | 호스트별 수행 방법 |
| `harness/entrypoints/` | 운영 안내·요청 라우팅 참고 문서 |
| `harness/bin/project.py` | 프로젝트 초안 생성·검증·설정 병합 |
| `harness/bin/verify.sh` | 패키지 검증 |
| `skills/` | init 포함 15개 스킬 |
| `agents/` | 17개 역할 |
| `docs/template/` | 산출물 템플릿 |

모든 스킬과 역할은 runtime.md를 먼저 읽는다. 패키지 루트의 AGENTS.md·CLAUDE.md는
하네스 소스 개발용이며 대상 프로젝트에 복사하지 않는다.
프로젝트 진입 파일에는 init이 짧은 안내 블록만 추가할 수 있다.

## 운영

1. init에서 프로젝트 목적·완료 기준·제약·주 작업 유형을 파악한다.
2. 공통 기본값에 프로젝트와 작업별 설정을 적용하고 유효 설정을 기록한다.
3. 선택한 경로의 단계·게이트를 수행하고 결함이 발생한 단계로 롤백한다.
4. G6에서 승격 후보를 검토하고, 문서 반영을 확인한 뒤 완료한다.
5. 프로젝트별 개선은 `.harness/`에 남긴다. 공통 개선은 플러그인 소스 변경으로 관리한다.

실행 모드는 누가 수행하는지를 바꾸며 검증 결과를 조작하거나 미실행을 통과로
보고하는 근거가 되지 않는다. 불필요한 단계와 문서의 범위는 프로젝트·작업 목적에 맞춰 선택한다.

## 검증

```bash
bash harness/bin/verify.sh
bash harness/bin/verify.sh --project /path/to/project
python3 -m unittest discover -s tests -v
```

대상 프로젝트의 기존 커맨드·에이전트는 검사하거나 수정하지 않는다.
복사 설치는 지원하지 않는다. 기존 `harness/bin/install.sh`는 전환 안내만 출력한다.
