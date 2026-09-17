# GitLab CI

## 파이프라인 골격

```yaml
stages: [verify, test, build, deploy]

default:
  image: node:20                      # latest 금지
  interruptible: true                 # 새 파이프라인 시작 시 중단 허용

.timed-job:
  timeout: 20m                       # default.timeout 대신 잡에 상속

variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

.node-cache: &node-cache
  cache:
    key:
      files: [package-lock.json]      # 잠금 파일 해시 기반
    paths: [.npm/]
    policy: pull

lint:
  extends: .timed-job
  stage: verify
  <<: *node-cache
  script:
    - npm ci
    - npm run lint
    - npm run typecheck

arch:                                 # 아키텍처 검증을 테스트보다 먼저
  extends: .timed-job
  stage: verify
  <<: *node-cache
  script:
    - npm ci
    - npm run test:arch

unit:
  extends: .timed-job
  stage: test
  needs: [arch]                       # 구조 검증 통과 후에만
  <<: *node-cache
  script:
    - npm ci
    - npm run test:unit -- --coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    when: always
    reports:
      junit: test-results/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
    expire_in: 1 week

integration:
  extends: .timed-job
  stage: test
  needs: [arch]
  services:
    - name: postgres:16
      alias: db
  variables:
    POSTGRES_PASSWORD: postgres
    DATABASE_URL: "postgres://postgres:postgres@db:5432/test"
  script:
    - npm ci
    - npm run test:integration

e2e:
  extends: .timed-job
  stage: test
  needs: [arch]
  image: mcr.microsoft.com/playwright:v1.47.0-jammy   # 버전 고정
  script:
    - npm ci
    - npx playwright test              # config에서 headless: true
  artifacts:
    when: on_failure
    paths: [test-results/]
    expire_in: 1 week
```

## 요점

| 항목 | 설정 |
|------|------|
| 중복 실행 취소 | `interruptible: true` + 프로젝트 설정의 auto-cancel |
| 캐시 키 | `key.files`에 잠금 파일 지정 — 해시 기반 |
| 잡 의존 | `needs`로 DAG 구성. 아키텍처 검증을 선행으로 |
| 리포트 | `artifacts.reports.junit` — MR 화면에 테스트 결과 표시 |
| 커버리지 | `coverage` 정규식 + cobertura 리포트 |
| 타임아웃 | 잡별 `timeout` 또는 `extends`로 상속. `default.timeout`은 사용하지 않음 |

## 배포 (환경 + 수동 승인)

```yaml
deploy:staging:
  extends: .timed-job
  stage: deploy
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  script: ./scripts/deploy.sh staging

deploy:production:
  extends: .timed-job
  stage: deploy
  environment:
    name: production
    url: https://example.com
  resource_group: production          # 배포 직렬화 — 동시 배포 방지
  interruptible: false                # 배포 중 취소 금지
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual                    # 수동 승인
      allow_failure: false
  script: ./scripts/deploy.sh production
```

| 항목 | 의미 |
|------|------|
| `when: manual` | 수동 실행 버튼. 승인 게이트 |
| `resource_group` | 같은 그룹의 잡을 직렬화. **배포에 필수** |
| `interruptible: false` | 배포 중 취소로 인한 불완전 상태 방지 |
| Protected environment | 프로젝트 설정에서 승인 가능한 사용자를 제한 |

## 롤백

```yaml
rollback:production:
  extends: .timed-job
  stage: deploy
  environment:
    name: production
    action: prepare
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
  script: ./scripts/rollback.sh $ROLLBACK_TO
```

수동 잡으로 두어 언제든 실행 가능하게 한다.
GitLab의 환경 화면에서 이전 배포로 되돌리는 기능도 함께 안내한다.

## 시크릿

| 규칙 | 설명 |
|------|------|
| 저장 | 프로젝트/그룹 CI/CD 변수 |
| **Protected** | 보호 브랜치·태그에서만 노출. 프로덕션 자격증명에 필수 |
| **Masked** | 로그 마스킹. 값 형식 제약 있음(길이·문자) |
| 파일 타입 | 인증서·키 파일은 `File` 타입 변수로 |
| 포크 MR | 보호 변수는 전달되지 않는다 |

**Protected를 켜지 않으면 아무 브랜치에서나 프로덕션 자격증명을 읽을 수 있다.**

## 주의사항

| 함정 | 대응 |
|------|------|
| `rules`와 `only/except` 혼용 | `rules`로 통일. 혼용 시 예측 불가 |
| `resource_group` 누락 | 동시 배포로 상태 충돌 |
| 캐시 `policy` 미지정 | 불필요한 업로드로 느려진다. 읽기 전용 잡은 `pull` |
| 서비스 준비 대기 없음 | DB 기동 전 테스트 시작. 대기 스크립트 추가 |
| `allow_failure: true` | 실패를 숨긴다. 게이트 우회로 쓰지 않는다 |
