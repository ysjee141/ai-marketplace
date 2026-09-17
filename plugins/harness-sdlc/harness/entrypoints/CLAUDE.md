# Harness 운영 안내 (Claude Code)

프로젝트에서 `harness-init`으로 운영 프로필을 설정한다.
스킬과 역할은 설치된 harness-sdlc 플러그인에서 사용한다.

공통 규약은 [runtime.md](../runtime.md), 요청별 스킬은
[운영 라우팅](AGENTS.md)을 따른다. 이 안내 전체를 프로젝트에 복사하지 않는다.
프로젝트 CLAUDE.md에는 init이 기존 내용을 유지하며 짧은 안내 블록만 추가한다.

Claude 플러그인 스킬은 `/harness-sdlc:harness-init`처럼 명시 호출할 수 있다.
에이전트는 `harness-sdlc:{role}`로 탐색한다. 팀·서브에이전트 기능이
현재 세션에 있는지 확인하고, 미지원이면 순차 역할 수행으로 대체한다.
