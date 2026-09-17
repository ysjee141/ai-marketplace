---
name: architecture-guard
description: "아키텍처 원칙을 실행 가능한 검증 테스트로 구현하는 절차. 계층 의존 규칙, 순환 의존, 도메인 순수성, 상태 전이 정합성을 CI에서 자동 검사한다. '아키텍처 검증 테스트 추가', '의존성 규칙 검사', 'ArchUnit/dependency-cruiser/import-linter 설정' 요청 시 사용. 다음 표현에도 반드시 사용: '도메인이 DB import 못 하게 막아줘', '계층 위반 잡아줘', '이 방향 의존 금지하고 싶어', '규칙으로 강제하고 싶어', '순환 의존 검사', '아무도 못 어기게'. 규칙 확장·예외 allowlist 추가 요청에도 사용. 제외: 계층 구조를 처음 설계하는 것은 architecture-design."
---

먼저 [공통 실행 규약](../../harness/runtime.md)을 읽고 플러그인 자산 경로와 프로젝트 운영 프로필을 적용한다.

# Architecture Guard — 아키텍처 검증 테스트

## 목적

**문서로만 존재하는 원칙은 반드시 침식된다.** 원칙을 실행 가능한 테스트로 바꿔
CI에서 위반을 즉시 실패시킨다.

## 원칙

- 검증 테스트는 **일반 테스트 스위트와 함께 실행**된다. 별도 수동 실행 도구가 아니다.
- **가장 먼저 실행한다.** 구조가 깨진 상태에서 나머지 테스트 실행은 의미가 없다.
- 위반은 **파일 단위로 나열**한다. "위반 3건"이 아니라 어느 파일이 무엇을 어겼는지.
- 승인된 예외는 **명시적 allowlist**로 코드에 남긴다. 주석으로 무시하지 않는다 —
  allowlist에 있으면 나중에 원복 여부를 추적할 수 있다.

## 규칙 목록

`harness/principles/architecture.md` 7절과 대응한다.

| # | 규칙 | 필수 | 검증 방법 |
|---|------|------|----------|
| A1 | Domain이 Application/Adapter/Infra를 import하지 않는다 | ✔ | import 그래프 |
| A2 | Application이 Infra 구체 타입을 import하지 않는다 | ✔ | import 그래프 |
| A3 | Domain에 프레임워크 어노테이션/데코레이터가 없다 | ✔ | 소스 패턴 검색 |
| A4 | 계층 간 순환 의존이 없다 | ✔ | 사이클 검출 |
| A5 | 공개 유스케이스마다 대응 테스트가 존재한다 | | 파일 매핑 |
| A6 | Domain 테스트가 I/O 없이 실행된다 | | 금지 모듈 로드 검사 |
| A7 | 상태 변경이 전이 맵에 정의된 것만 수행한다 | | 전이 맵 ↔ 호출부 대조 |
| A8 | API 응답 타입과 소비 타입이 일치한다 | | 계약 스키마 대조 |
| A9 | 네이밍 변환이 지정 매퍼에서만 일어난다 | | 변환 함수 호출 위치 |

기본 선택은 A1~A4이며 실제 검증 대상은 유효 설정의 architecture_rules다.
프로젝트에 없는 계층·요소는 미적용 사유를 기록하고 프로젝트 추가 규칙을 함께 검증한다.

## 도구 선택

전용 도구가 있으면 쓰고, 없으면 직접 작성한다.

| 언어 | 도구 |
|------|------|
| Java/Kotlin | ArchUnit |
| TypeScript/JS | dependency-cruiser, eslint-plugin-boundaries |
| Python | import-linter, pytest-archon |
| Go | go-arch-lint, depguard |
| C#/.NET | NetArchTest |
| Rust | cargo-modules + 커스텀 |

**전용 도구가 없거나 도입 비용이 크면 직접 작성한다.** import 그래프 파싱은
30줄 내외면 충분하고, 외부 의존을 줄이는 이점이 있으며, 프로젝트 고유 규칙을
자유롭게 추가할 수 있다.

## 직접 작성 패턴

### A1/A2 — 계층 의존 검증

```python
# tests/architecture/test_layer_dependency.py
LAYER_RULES = {
    "src/domain":      [],                                   # 아무것도 import 못 함
    "src/application": ["src.domain"],
    "src/adapter":     ["src.domain", "src.application"],
    "src/infra":       ["src.domain", "src.application", "src.adapter"],
}

ALLOWLIST = {
    # ADR-0007로 승인된 예외. 2026-12 재검토 예정
    # "src/domain/legacy_bridge.py": ["src.infra.legacy"],
}

def test_계층_의존_규칙():
    violations = []
    for layer, allowed in LAYER_RULES.items():
        for path in source_files(layer):
            for imported in internal_imports(path):
                if imported in ALLOWLIST.get(path, []):
                    continue
                if not any(imported.startswith(a) for a in allowed):
                    violations.append(f"{path} → {imported}")
    assert not violations, "의존성 규칙 위반:\n" + "\n".join(violations)
```

핵심은 **위반 목록을 전부 출력**하는 것이다. 첫 번째에서 멈추면 수정을
여러 라운드에 나눠 하게 된다.

### A3 — 도메인 순수성

```python
FORBIDDEN_IN_DOMAIN = [
    "@app.route", "@Entity", "@Column", "@Injectable",
    "import requests", "import sqlalchemy", "from django",
]

def test_도메인에_프레임워크_침투가_없다():
    violations = [
        f"{p}:{n} — {pat}"
        for p in source_files("src/domain")
        for n, line in enumerate(read_lines(p), 1)
        for pat in FORBIDDEN_IN_DOMAIN
        if pat in line
    ]
    assert not violations, "도메인 순수성 위반:\n" + "\n".join(violations)
```

### A4 — 순환 의존

```python
def test_순환_의존이_없다():
    graph = build_import_graph("src/")
    cycles = find_cycles(graph)          # DFS 또는 Tarjan
    assert not cycles, "순환 의존:\n" + "\n".join(" → ".join(c) for c in cycles)
```

### A7 — 상태 전이 정합성

가장 잡기 어려운 결함을 잡는 규칙이다. 전이 맵을 **코드 상수로 두는 것**이 전제다.

```python
STATE_TRANSITIONS = {           # src/domain/order/transitions.py
    "draft":   ["placed"],
    "placed":  ["paid", "cancelled"],
    "paid":    ["shipped", "refunded"],
    "shipped": [],
}

def test_모든_상태_전이가_맵에_정의되어_있다():
    # 코드에서 status 갱신 호출부를 수집하여 (from, to) 쌍을 추출
    actual = extract_status_transitions("src/")
    undefined = [t for t in actual if t[1] not in STATE_TRANSITIONS.get(t[0], [])]
    assert not undefined, f"무단 전이: {undefined}"

def test_죽은_전이가_없다():
    actual = set(extract_status_transitions("src/"))
    declared = {(f, t) for f, ts in STATE_TRANSITIONS.items() for t in ts}
    dead = declared - actual
    assert not dead, f"코드에서 실행되지 않는 전이: {dead}"
```

**죽은 전이 검사가 특히 중요하다.** 설계에 정의했으나 구현하지 않은 전이는
"영원히 그 상태에 머무는" 버그를 만든다.

## 예외 처리 절차

원칙 위반이 불가피할 때:

1. **ADR을 먼저 작성한다** — 무엇을, 왜, 되돌리는 조건
2. allowlist에 항목을 추가하고 **ADR 번호와 재검토 시점을 주석으로** 남긴다
3. 테스트를 무시(`skip`, `ignore` 주석)하지 않는다 — 추적이 불가능해진다

```python
ALLOWLIST = {
    # ADR-0007: 레거시 인증 시스템 연동 브리지. 2026-12 마이그레이션 후 제거
    "src/domain/legacy_bridge.py": ["src.infra.legacy"],
}
```

## 도입 절차

### 신규 프로젝트

설계 단계에서 선정한 규칙(A1~A4 + 추가분)을 **첫 구현 Task와 함께** 도입한다.
별도 Task로 잡아 나중에 하면 이미 위반이 쌓인다.

### 기존 프로젝트 (위반이 이미 존재)

전면 도입은 좌절로 끝난다. 다음 순서로 진행한다:

1. 검증 테스트를 작성하고 **현재 위반을 전부 allowlist에 넣는다** (기준선 고정)
2. 테스트가 통과하는 상태로 CI에 넣는다 — **새 위반이 추가되지 않게 막는 것이
   1차 목표**다
3. allowlist 항목을 점진적으로 제거하는 Task를 만든다
4. allowlist 크기를 리뷰에서 추적한다 (늘어나면 후퇴)

## CI 통합

- **테스트 실행 순서에서 가장 앞**에 둔다
- 실패 시 non-zero 종료로 파이프라인을 중단시킨다
- 위반 목록을 전부 출력한다

## 완료 판정

- [ ] A1~A4가 테스트로 구현되었다
- [ ] 설계서에서 선정한 추가 규칙이 구현되었다
- [ ] 위반 시 파일 단위 목록이 출력된다
- [ ] 승인된 예외가 allowlist에 ADR 번호와 함께 기록되었다
- [ ] 테스트가 CI에서 가장 먼저 실행된다
- [ ] 기존 프로젝트라면 기준선이 고정되어 새 위반이 차단된다
