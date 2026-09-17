# GitHub Actions

## 워크플로 골격

```yaml
name: CI
on:
  push: { branches: [main] }
  pull_request:

concurrency:                          # 같은 브랜치 중복 실행 취소
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:                          # 최소 권한. 기본값에 의존하지 않는다
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version-file: .nvmrc
          cache: npm                  # 잠금 파일 해시 기반 캐시

      - run: npm ci

      - name: 정적 검사
        run: npm run lint && npm run typecheck

      - name: 아키텍처 검증          # 가장 먼저. 구조가 깨졌으면 여기서 중단
        run: npm run test:arch

      - name: 단위 테스트
        run: npm run test:unit -- --coverage

      - name: 통합 테스트
        run: npm run test:integration

      - name: E2E (headless)
        run: npx playwright test      # config에서 headless: true

      - name: 리포트 업로드
        if: always()                  # 실패해도 수집
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: |
            test-results/
            coverage/
          retention-days: 7
```

## 요점

| 항목 | 설정 |
|------|------|
| 동시 실행 제어 | `concurrency` + `cancel-in-progress` |
| 권한 | `permissions`를 명시. 기본 `write-all`에 의존하지 않는다 |
| 액션 버전 | 태그 고정(`@v4`). 보안이 중요하면 커밋 SHA 고정 |
| 캐시 | `setup-*`의 `cache` 옵션이 잠금 파일 해시를 자동 사용 |
| 타임아웃 | `timeout-minutes` 필수 |
| 리포트 수집 | `if: always()` — 실패 시에도 아티팩트 필요 |

## 서비스 컨테이너 (통합 테스트용 DB)

```yaml
    services:
      postgres:
        image: postgres:16                    # latest 금지
        env: { POSTGRES_PASSWORD: postgres }
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-retries 5
        ports: ["5432:5432"]
```

헬스체크 없이 쓰면 DB가 준비되기 전에 테스트가 시작되어 불안정해진다.

## E2E 브라우저

```yaml
      - run: npx playwright install --with-deps chromium
```

필요한 브라우저만 설치한다. 전체 설치는 느리다.

## 배포 (환경 보호 + 수동 승인)

```yaml
  deploy-prod:
    needs: verify
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production                # 리포지토리 설정에서 필수 리뷰어 지정
      url: https://example.com
    concurrency:
      group: deploy-production        # 배포는 직렬화. cancel-in-progress 금지
    steps:
      - uses: actions/checkout@v4
      - name: 배포
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: ./scripts/deploy.sh
```

**수동 승인은 `environment`의 보호 규칙(required reviewers)으로 구현한다.**
워크플로 파일만으로는 승인 게이트를 만들 수 없다 — 리포지토리 설정이 필요하며,
이 사실을 cicd-notes에 기재한다.

**배포 잡에는 `cancel-in-progress`를 쓰지 않는다.** 배포 중 취소는 불완전한
상태를 남긴다.

## 시크릿

| 규칙 | 설명 |
|------|------|
| 참조 | `${{ secrets.NAME }}` |
| 포크 PR | `pull_request` 트리거에서는 시크릿이 전달되지 않는다 (의도된 동작) |
| `pull_request_target` | 시크릿에 접근 가능하지만 **포크 코드를 체크아웃하면 유출된다.** 사용 금지 |
| 환경 시크릿 | `environment`에 묶어 프로덕션 시크릿을 분리 |
| 마스킹 | 자동 마스킹되지만 가공된 값(base64 등)은 마스킹되지 않는다 |

## OIDC (권장)

장수명 클라우드 자격증명을 시크릿에 넣는 대신 OIDC로 단기 토큰을 발급받는다.

```yaml
    permissions:
      id-token: write
      contents: read
```

자격증명 유출 위험을 근본적으로 제거하므로, 클라우드 배포 시 우선 검토한다.

## 주의사항

| 함정 | 대응 |
|------|------|
| `${{ }}`를 `run:` 안에 직접 넣기 | 셸 인젝션 위험. `env:`로 전달 후 참조 |
| `pull_request_target` + 포크 체크아웃 | 시크릿 유출. 사용하지 않는다 |
| `actions/checkout` 기본 fetch-depth 1 | 태그·이력이 필요하면 `fetch-depth: 0` |
| 매트릭스 남용 | 조합이 곱해져 러너 시간이 폭증한다 |
| `continue-on-error` | 실패를 숨긴다. 게이트 우회로 쓰지 않는다 |
