<!-- harness-source-repo -->
# CLAUDE.md

이 저장소는 **개발 파이프라인 하네스 그 자체**를 구축·보관하는 곳이다.
여기서 애플리케이션을 개발하지 않는다. 하네스는 다른 저장소에 설치되어 사용된다.

> **이 파일은 대상 저장소로 배포되지 않는다.**
> 설치되는 진입점은 `harness/entrypoints/CLAUDE.md`와
> `harness/entrypoints/AGENTS.md`다. 파이프라인 운영 규약(트리거·실행 모드·
> 불변 규칙·라우팅 표)을 바꾸려면 **그쪽을 고쳐야 한다.**

## 작업 방식

하네스 자체를 수정하는 요청(에이전트·스킬 추가, 원칙 변경, 템플릿 수정)은
`harness:harness` 스킬을 사용하라. 파이프라인 실행이 아니다.

수정 후 반드시 `harness/bin/verify.sh`를 실행하고, 아래 변경 이력에 기록한다.

## 구조

| 경로 | 역할 |
|------|------|
| `harness/config.yml` | 실행 모드·품질 기준 설정 |
| `harness/` | 도구 중립 SOT — 원칙, 파이프라인·실행모드 정의, 어댑터, 스크립트 |
| `harness/entrypoints/` | **대상 저장소용 진입점 템플릿** (`CLAUDE.md`, `AGENTS.md`) |
| `harness/bin/` | `install.sh`(설치), `verify.sh`(구조 검증) |
| `.claude/agents/` | 에이전트 정의 17종 |
| `.claude/skills/` | 스킬 14종 (오케스트레이터 포함) |
| `docs/template/` | 문서 템플릿 12종 |
| `CLAUDE.md` / `AGENTS.md` | **이 저장소 전용** 진입점 — 배포 대상 아님 |

## 진입점 규약

진입 문서는 두 종류이며 **역할이 다르다. 섞지 않는다.**

| 파일 | 대상 | 내용 |
|------|------|------|
| 루트 `CLAUDE.md` / `AGENTS.md` | 하네스 저장소 자신 | 하네스를 어떻게 수정하는가 |
| `harness/entrypoints/CLAUDE.md` / `AGENTS.md` | 설치된 저장소 | 파이프라인을 어떻게 운영하는가 |

`install.sh`는 **`harness/entrypoints/`만 배포한다.** 루트 문서를 대상 저장소에
복사하면 "여기서 애플리케이션을 개발하지 않는다" 같은 하네스 전용 지시가
대상 저장소의 에이전트에게 전달되어 개발 작업 자체를 막는다.

`entrypoints/CLAUDE.md`의 `{{INSTALL_DATE}}`는 설치 시점 날짜로 치환된다.

## 변경 이력

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-08-14 | 초기 구성 — 에이전트 17종, 스킬 14종, 템플릿 12종, 원칙 5종 | 전체 | - |
| 2026-08-14 | 실행 모드 3종(skill/balanced/agent) 도입 + `config.yml` 추가 | `harness/execution-modes.md`, `harness/config.yml`, `sdlc-orchestrator`, `workspace.md` | 플랜별 토큰 예산에 맞춰 서브에이전트 사용량을 조절할 필요 |
| 2026-08-14 | 스킬 description 7종 수정 — 부정 조건·증상 어휘 추가 | `review-gate`, `wbs-cpm-planning`, `harness-docs`, `integration-qa`, `architecture-guard`, `test-execution`, `architecture-design` | 트리거 검증에서 빌트인 code-review 충돌 및 경계 모호 6건 검출 |
| 2026-08-14 | AGENTS.md에 "요청 → 스킬 라우팅" 표 추가 | `AGENTS.md`, `verify.sh` | 범용 도구에는 description 자동 트리거가 없어 스킬에 도달할 경로가 없었음 |
| 2026-08-14 | install.sh가 도구별 진입 파일 4종 생성 | `install.sh`, `generic-agent.md`, `harness/README.md` | 문서는 GEMINI.md·Cursor·Copilot·Aider 진입점을 약속했으나 스크립트가 생성하지 않아 해당 도구에서 하네스가 로드되지 않았음 |
| 2026-08-14 | 진입점 문서를 배포용/저장소용으로 분리 — `harness/entrypoints/` 신설 | `harness/entrypoints/{CLAUDE,AGENTS}.md`, 루트 `CLAUDE.md`·`AGENTS.md`, `install.sh`, `verify.sh`, `harness/README.md` | install.sh가 하네스 개발용 루트 문서를 대상 저장소에 그대로 복사해, 대상 저장소 에이전트가 "여기서 애플리케이션을 개발하지 않는다"로 인식하고 개발 요청을 거부함 |
