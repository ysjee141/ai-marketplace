# Harness SDLC

기획부터 배포까지의 개발 전 주기를 단계·게이트·산출물·롤백 규칙으로 통제하는
도구 중립 개발 파이프라인 하네스입니다.

이 플러그인은 `harness-sdlc` 저장소의 내용을 Codex와 Claude Code가 읽을 수 있는
플러그인 구조로 패키징합니다.

## 포함 내용

- `skills/`: SDLC 오케스트레이터를 포함한 14개 절차 스킬
- `agents/`: 기획·분석·설계·구현·QA·리뷰·배포 역할 17종
- `harness/`: 파이프라인, 실행 모드, 원칙, 어댑터, 설치·검증 스크립트
- `docs/template/`: PRD, 분석, Tech Spec, ADR, WBS, 설계, 테스트, 리뷰 템플릿

## 사용 방법

플러그인을 설치하면 Codex/Claude Code에서 `sdlc-orchestrator`,
`requirements-interview`, `architecture-design`, `implementation-playbook` 등
스킬을 사용할 수 있습니다. 전체 하네스 규약을 대상 저장소에 설치하려면 이
플러그인 디렉터리의 `harness/bin/install.sh`에 대상 저장소 경로를 전달하십시오.

```bash
harness/bin/install.sh /path/to/target-repo
cd /path/to/target-repo
harness/bin/verify.sh
```

기존 파일은 덮어쓰지 않고 충돌 시 `.harness-new` 파일로 보존합니다.
