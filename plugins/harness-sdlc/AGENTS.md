<!-- harness-source-repo -->
# AGENTS.md

이 저장소는 **개발 파이프라인 하네스의 소스**다.
여기서 애플리케이션을 개발하지 않는다. 하네스는 다른 저장소에 설치되어 사용된다.

Claude Code를 쓴다면 `CLAUDE.md`를 대신 참조한다.

> **이 파일은 대상 저장소로 배포되지 않는다.**
> 설치되는 진입점은 `harness/entrypoints/AGENTS.md`(정본, 요청→스킬 라우팅 표 포함)와
> `harness/entrypoints/CLAUDE.md`다. 파이프라인 운영 규약을 바꾸려면 그쪽을 고친다.

## 진입점 규약

진입 문서는 두 종류이며 **역할이 다르다. 섞지 않는다.**

| 파일 | 대상 | 내용 |
|------|------|------|
| 루트 `AGENTS.md` / `CLAUDE.md` | 하네스 저장소 자신 | 하네스를 어떻게 수정하는가 |
| `harness/entrypoints/AGENTS.md` / `CLAUDE.md` | 설치된 저장소 | 파이프라인을 어떻게 운영하는가 |

`harness/bin/install.sh`는 **`harness/entrypoints/`만 배포한다.** 루트 문서를
대상 저장소에 복사하면 하네스 전용 지시가 대상 저장소의 에이전트에게 전달되어
개발 작업 자체를 막는다.

## 하네스를 수정할 때

| 무엇을 바꾸는가 | 어디를 고치는가 |
|----------------|----------------|
| 파이프라인 단계·게이트·롤백 | `harness/pipeline.md` |
| 실행 모드 정의 | `harness/execution-modes.md` |
| 기본 모드·커버리지 기준·게이트 임계 | `harness/config.yml` |
| 설계·테스트·문서·워크스페이스 원칙 | `harness/principles/*.md` |
| 도구별 운영 방식 | `harness/adapters/*.md` |
| 역할 정의 | `.claude/agents/{name}.md` |
| 절차 지식 | `.claude/skills/{name}/SKILL.md` |
| 문서 템플릿 | `docs/template/*.md` |
| **대상 저장소가 읽을 운영 규약·라우팅 표** | `harness/entrypoints/{AGENTS,CLAUDE}.md` |
| 설치 동작 | `harness/bin/install.sh` |
| 검증 항목 | `harness/bin/verify.sh` |

## 수정 절차

1. 무엇을 왜 바꾸는지 먼저 확정한다. 근거 없는 구조 변경은 하지 않는다.
2. 해당 파일을 수정한다. **같은 내용을 두 파일에 복제하지 않는다** —
   두 벌이 되면 반드시 어긋난다. 포인터로 참조한다.
3. 스킬을 추가·삭제했다면 `harness/entrypoints/AGENTS.md`의 라우팅 표를 갱신한다.
   범용 도구에는 자동 트리거가 없어 이 표가 유일한 경로다.
4. `harness/bin/verify.sh`를 실행하여 구조를 검증한다.
5. `CLAUDE.md`의 변경 이력에 날짜·변경 내용·대상·사유를 기록한다.

## 설치·검증

```bash
harness/bin/install.sh /path/to/target-repo   # 대상 저장소에 설치
harness/bin/verify.sh                          # 구조 검증 (소스·설치 저장소 모두)
```

`verify.sh`는 루트 문서의 `<!-- harness-source-repo -->` 마커로 소스 저장소와
설치된 저장소를 구분하고, 진입점 검증 대상을 각각에 맞게 전환한다.

## 개요

하네스 자체의 설계 의도·구성 요소·파이프라인 요약은 `harness/README.md`.
