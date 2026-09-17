# Personal AI Marketplace

Claude Code와 Codex에서 재사용할 AI agent skill을 GitHub로 관리하기 위한 최소 마켓플레이스입니다.

## 구조

```text
.
├── .agents/plugins/marketplace.json       # Codex marketplace
├── .claude-plugin/marketplace.json        # Claude Code marketplace
└── plugins/
    ├── documents/                         # 기술 문서 플러그인
    └── harness-sdlc/                      # 프로젝트 인터뷰·SDLC 운영
```

각 플러그인의 `skills/`는 Claude Code와 Codex에서 함께 사용할 수 있습니다.

## 설치

### Claude Code

저장소를 GitHub에 올린 뒤 아래 명령에서 `<owner>/<repo>`를 실제 값으로 바꿉니다.

```text
/plugin marketplace add <owner>/<repo>
/plugin install documents@personal-agent-marketplace
/plugin install harness-sdlc@personal-agent-marketplace
```

### Codex

각 기기에서 저장소를 clone한 다음 로컬 marketplace를 등록합니다.

```bash
codex plugin marketplace add /path/to/ai-marketplace
codex plugin add documents@personal-agent-marketplace
codex plugin add harness-sdlc@personal-agent-marketplace
```

`documents` skill은 Codex의 skill 선택/호출 대상으로 사용할 수 있습니다.

`harness-sdlc`는 설치 후 대상 프로젝트의 새 대화에서
“harness-init으로 이 프로젝트의 하네스를 설정해줘”라고 요청합니다.
별도의 셸 설치 없이 프로젝트 목적·제약·완료 기준을 인터뷰하고 `.harness/`에
운영 프로필을 만듭니다. 공통 스킬은 플러그인에서 읽습니다.
상세 운영·검증 방법은 [Harness README](plugins/harness-sdlc/README.md)를 참고합니다.

## 새 항목 추가

1. 공통 skill은 `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`에 추가합니다.
2. 새 플러그인은 두 marketplace 파일의 `plugins` 배열에 각각 등록합니다.
3. 플러그인 버전을 변경하고 각 제품에서 다시 설치/업데이트합니다.

아직 특정 vendor에 종속되지 않은 기능은 `skills/`에 두는 것을 기본 원칙으로 삼습니다. MCP, agent, hook, 앱 연결은 필요해질 때 플러그인별로 추가합니다.

## 참고 문서

- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
