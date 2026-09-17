# 백엔드 구현 플레이북

언어·프레임워크 무관. 구체적 문법이 아니라 **구조와 판단**을 다룬다.

## 목차

1. [계층별 구현 지침](#1-계층별-구현-지침)
2. [의존성 주입](#2-의존성-주입)
3. [트랜잭션 경계](#3-트랜잭션-경계)
4. [에러 처리](#4-에러-처리)
5. [로깅과 관측](#5-로깅과-관측)
6. [동시성](#6-동시성)
7. [테스트 작성](#7-테스트-작성)

---

## 1. 계층별 구현 지침

### Domain

```
src/domain/
├── user/
│   ├── user.py          엔티티
│   ├── email.py         값 객체
│   ├── password.py      값 객체
│   └── errors.py        도메인 예외
```

- **import 상단에 프레임워크·DB·HTTP가 보이면 잘못된 것이다.** 언어 표준
  라이브러리와 다른 도메인 모듈만 허용된다
- 값 객체는 생성자에서 검증하고 불변으로 만든다. 검증을 통과한 인스턴스는
  이후 모든 곳에서 유효함이 보증된다
- 엔티티는 setter를 열지 않는다. `order.cancel(reason)`처럼 **의미 있는
  도메인 메서드**로만 상태를 바꾼다
- 상태 전이는 **전이 맵 상수**로 선언하고 메서드에서 검증한다.
  `architecture-guard`의 A7이 이 상수와 코드를 대조한다

```python
STATE_TRANSITIONS = {
    "draft": ["placed"], "placed": ["paid", "cancelled"],
    "paid": ["shipped", "refunded"], "shipped": [],
}

def _transition(self, to: str) -> "Order":
    if to not in STATE_TRANSITIONS[self.status]:
        raise InvalidTransition(self.status, to)
    return replace(self, status=to)      # 새 인스턴스 반환
```

### Application

```
src/application/
├── auth/
│   ├── login_usecase.py
│   └── ports.py          인터페이스 선언
```

- 포트는 **유스케이스 관점**으로 설계한다. `findByEmailAndStatusAndCreatedAfter`
  같은 구현 편의 인터페이스는 만들지 않는다
- 시각·난수·ID 생성을 포트로 선언한다 (`Clock`, `IdGenerator`, `PasswordHasher`)
- 유스케이스는 하나의 공개 메서드를 갖는다 (`execute`). 여러 개면 유스케이스가
  여럿인 것이다
- 결과는 성공/실패를 타입으로 구분한다. 예외로 흐름을 제어하지 않는 편이
  호출자가 처리를 빠뜨리지 않는다

### Adapter

- 컨트롤러는 **얇게** — 요청 파싱 → 유스케이스 호출 → 응답 변환. 비즈니스 로직 금지
- 리포지토리 구현은 포트 인터페이스를 만족한다. 인터페이스에 없는 메서드를
  추가하지 않는다
- **매퍼를 반드시 별도 모듈로 둔다.** DB 컬럼명 ↔ 도메인 필드명 변환은 여기서만.
  `architecture-guard` A9가 이것을 검증한다

### Infrastructure

- DI 컨테이너 조립, 설정 로딩, 프레임워크 부트스트랩
- **여기서만 구체 타입이 인터페이스에 바인딩된다**

---

## 2. 의존성 주입

프레임워크 DI 컨테이너가 있어도 **생성자 주입을 기본**으로 한다.
필드 주입·서비스 로케이터는 의존을 숨겨 테스트를 어렵게 만든다.

```python
class LoginUseCase:
    def __init__(self, users: UserRepository, sessions: SessionRepository,
                 clock: Clock, hasher: PasswordHasher):
        ...
```

의존이 5개를 넘으면 **유스케이스가 너무 많은 일을 한다는 신호**다. 분해를 검토한다.

---

## 3. 트랜잭션 경계

- **트랜잭션 경계는 Application 계층에 둔다.** 도메인은 트랜잭션을 모른다
- **하나의 트랜잭션 = 하나의 애그리게이트 변경**이 기본. 여러 애그리게이트를
  한 트랜잭션에 묶어야 한다면 애그리게이트 경계 설계가 틀렸을 가능성이 크다
- 트랜잭션 안에서 외부 호출(HTTP, 메시지 발행)을 하지 않는다. 커밋 지연과
  부분 실패를 만든다. 발행은 커밋 후 또는 아웃박스 패턴으로
- 읽기 전용 작업에 쓰기 트랜잭션을 열지 않는다

---

## 4. 에러 처리

### 계층별 에러 타입

| 계층 | 에러 성격 | 예 |
|------|----------|-----|
| Domain | 불변식·규칙 위반 | `InvalidTransition`, `InvalidEmail` |
| Application | 유스케이스 실패 | `UserNotFound`, `AuthenticationFailed` |
| Adapter | 외부 시스템 실패 | `RepositoryUnavailable` |

**도메인 예외를 HTTP 상태 코드로 직접 매핑하지 않는다.** 매핑은 Adapter의
전용 계층에서 한다 — 도메인이 HTTP를 알게 되면 의존성 규칙 위반이다.

### 규칙

- 에러를 삼키지 않는다. `except: pass`는 금지
- 잡았으면 변환하거나 로깅하고 전파한다
- 에러 메시지에 내부 구조(테이블명, 파일 경로, 스택)를 노출하지 않는다
- 원인 예외를 체이닝하여 보존한다 (`raise X from e`)

---

## 5. 로깅과 관측

| 항목 | 기준 |
|------|------|
| 형식 | 구조화 로그(JSON). 문자열 연결 금지 |
| 상관 ID | 요청마다 부여하고 전 계층에 전파 |
| 레벨 | ERROR=조치 필요, WARN=이상하지만 처리됨, INFO=업무 이벤트, DEBUG=개발용 |
| 금지 | 비밀번호·토큰·개인정보·카드번호. **마스킹은 로깅 지점이 아니라 값 객체에서** |
| 도메인 계층 | 로깅하지 않는다 (순수성 유지). 필요하면 이벤트를 반환하고 셸이 기록 |

---

## 6. 동시성

- **공유 가변 상태를 만들지 않는 것이 최선의 동시성 대책이다.** 순수성 원칙이
  여기서도 보상한다
- 낙관적 락(버전 컬럼)을 기본으로 한다. 비관적 락은 경합이 실측된 경우에만
- 재시도를 도입하려면 **멱등성이 전제**다. 비멱등 연산의 재시도는 중복 처리를 낳는다
- 외부 호출에는 타임아웃을 반드시 건다. 무한 대기는 스레드·커넥션 고갈로 이어진다

---

## 7. 테스트 작성

| 대상 | 방식 | 요구 |
|------|------|------|
| 값 객체 | 단위 | 유효/무효 입력, 동등성 |
| 엔티티 | 단위 | 불변식 위반 시 예외, **허용/금지 전이 모두** |
| 유스케이스 | 단위 | 성공 + 모든 에러 경로. **인메모리 Fake 포트** |
| 리포지토리 구현 | 통합 | 실제 DB(컨테이너)로 저장·조회·삭제 왕복 |
| 컨트롤러 | 계약 | 요청 → 응답 shape이 **API 계약과 일치** |
| 매퍼 | 단위 | 컬럼명 ↔ 필드명 **왕복** 변환 |

### Fake vs Mock

포트 테스트에는 **인메모리 Fake**를 쓴다.

```python
class InMemoryUserRepository(UserRepository):
    def __init__(self): self._items = {}
    def save(self, u): self._items[u.id] = u
    def findById(self, id): return self._items.get(id)
```

Mock의 호출 검증(`verify(repo).save(any())`)은 구현에 결합되어 리팩터링을 방해한다.
"저장했는지"가 아니라 "저장 후 조회하면 나오는지"를 검증하는 편이 견고하다.

### 시각·난수 고정

```python
def test_만료된_세션은_조회되지_않는다():
    clock = FixedClock(at="2026-08-14T12:00:00Z")
    usecase = GetSessionUseCase(sessions=fake_repo, clock=clock)
    ...
```

`datetime.now()`를 직접 호출하는 코드는 테스트할 수 없다. 이것이 시각을
포트로 주입하는 실질적 이유다.
