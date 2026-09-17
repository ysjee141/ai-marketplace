<!-- harness-source-repo -->
# CLAUDE.md

이 저장소는 **개발 파이프라인 하네스 그 자체**를 구축·보관하는 곳이다.
여기서 애플리케이션을 개발하지 않는다. 하네스는 다른 저장소에 설치되어 사용된다.

> **이 파일은 대상 저장소로 배포되지 않는다.**
> 공통 실행 규약은 `harness/runtime.md`, 요청 라우팅 참고 자료는
> `harness/entrypoints/AGENTS.md`다. 프로젝트 안내 블록은 init이 생성한다.

## 작업 방식

하네스 자체 수정은 `AGENTS.md`의 소스 개발 규약을 따른다.
프로젝트 운영은 설치된 플러그인의 `harness-init`에서 시작한다.

수정 후 반드시 `harness/bin/verify.sh`를 실행하고, 아래 변경 이력에 기록한다.

## 구조

| 경로 | 역할 |
|------|------|
| `harness/defaults.json` | 실행 모드·품질 기준 설정 |
| `harness/` | 도구 중립 SOT — 원칙, 파이프라인·실행모드 정의, 어댑터, 스크립트 |
| `harness/entrypoints/` | 운영 안내·요청 라우팅 참고 문서 |
| `harness/bin/` | `project.py`(프로필), `verify.sh`(검증), `install.sh`(전환 안내만) |
| `agents/` | 에이전트 정의 17종 |
| `skills/` | 스킬 15종 (init·오케스트레이터 포함) |
| `docs/template/` | 문서 템플릿 12종 |
| `CLAUDE.md` / `AGENTS.md` | **이 저장소 전용** 진입점 — 배포 대상 아님 |

## 진입점 규약

진입 문서는 두 종류이며 **역할이 다르다. 섞지 않는다.**

| 파일 | 대상 | 내용 |
|------|------|------|
| 루트 `CLAUDE.md` / `AGENTS.md` | 하네스 저장소 자신 | 하네스를 어떻게 수정하는가 |
| `harness/entrypoints/CLAUDE.md` / `AGENTS.md` | 설치된 저장소 | 파이프라인을 어떻게 운영하는가 |

마켓플레이스 설치가 기본이다. init은 `.harness/`와 짧은 프로젝트 안내만 생성한다.
공통 자산과 루트 소스 지침은 프로젝트에 복사하지 않는다.
`harness/entrypoints/`는 운영 라우팅 참고 자료다.

## 변경 이력

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-09-17 | 마켓플레이스 직접 사용·init 인터뷰·프로젝트 프로필·설정 병합·업데이트 보존·회귀 검증 도입. 복사 설치는 전환 안내로 대체. G6 순서와 CI 예제 보완 | 매니페스트, skills, agents, harness, tests, README | 이중 설치·깨진 경로·설정 중복을 제거하고 프로젝트별 운영 규칙을 보존 |
| 2026-08-14 | 초기 구성 — 에이전트 17종, 스킬 14종, 템플릿 12종, 원칙 5종 | 전체 | - |
| 2026-08-14 | 실행 모드 3종(skill/balanced/agent) 도입 + `defaults.json` 추가 | `harness/execution-modes.md`, `harness/defaults.json`, `sdlc-orchestrator`, `workspace.md` | 플랜별 토큰 예산에 맞춰 서브에이전트 사용량을 조절할 필요 |
| 2026-08-14 | 스킬 description 7종 수정 — 부정 조건·증상 어휘 추가 | `review-gate`, `wbs-cpm-planning`, `harness-docs`, `integration-qa`, `architecture-guard`, `test-execution`, `architecture-design` | 트리거 검증에서 빌트인 code-review 충돌 및 경계 모호 6건 검출 |
| 2026-08-14 | AGENTS.md에 "요청 → 스킬 라우팅" 표 추가 | `AGENTS.md`, `verify.sh` | 범용 도구에는 description 자동 트리거가 없어 스킬에 도달할 경로가 없었음 |
| 2026-08-14 | install.sh가 도구별 진입 파일 4종 생성 | `install.sh`, `generic-agent.md`, `harness/README.md` | 문서는 GEMINI.md·Cursor·Copilot·Aider 진입점을 약속했으나 스크립트가 생성하지 않아 해당 도구에서 하네스가 로드되지 않았음 |
| 2026-08-14 | 진입점 문서를 배포용/저장소용으로 분리 — `harness/entrypoints/` 신설 | `harness/entrypoints/{CLAUDE,AGENTS}.md`, 루트 `CLAUDE.md`·`AGENTS.md`, `install.sh`, `verify.sh`, `harness/README.md` | install.sh가 하네스 개발용 루트 문서를 대상 저장소에 그대로 복사해, 대상 저장소 에이전트가 "여기서 애플리케이션을 개발하지 않는다"로 인식하고 개발 요청을 거부함 |
