# Jenkins

선언적 파이프라인(Declarative Pipeline)을 기본으로 한다.
스크립티드 파이프라인은 필요한 경우에만 `script {}` 블록으로 국소 사용한다.

## Jenkinsfile 골격

```groovy
pipeline {
  agent { docker { image 'node:20' } }      // latest 금지

  options {
    timeout(time: 20, unit: 'MINUTES')
    disableConcurrentBuilds()                // 동시 실행 방지
    buildDiscarder(logRotator(numToKeepStr: '30'))
    timestamps()
  }

  environment {
    CI = 'true'
  }

  stages {
    stage('정적 검사') {
      steps {
        sh 'npm ci'
        sh 'npm run lint'
        sh 'npm run typecheck'
      }
    }

    stage('아키텍처 검증') {              // 테스트보다 먼저
      steps { sh 'npm run test:arch' }
    }

    stage('테스트') {
      parallel {
        stage('단위') {
          steps { sh 'npm run test:unit -- --coverage' }
        }
        stage('통합') {
          steps { sh 'npm run test:integration' }
        }
        stage('E2E') {
          steps { sh 'npx playwright test' }   // config에서 headless: true
        }
      }
    }
  }

  post {
    always {
      junit testResults: 'test-results/**/*.xml', allowEmptyResults: false
      archiveArtifacts artifacts: 'coverage/**', allowEmptyArchive: true
    }
    cleanup { cleanWs() }                   // 워크스페이스 정리
  }
}
```

## 요점

| 항목 | 설정 |
|------|------|
| 동시 실행 | `disableConcurrentBuilds()` |
| 타임아웃 | `options { timeout(...) }` 필수 |
| 빌드 보존 | `buildDiscarder` — 디스크 고갈 방지 |
| 테스트 리포트 | `junit` 스텝. `allowEmptyResults: false`로 테스트 0건을 실패 처리 |
| 워크스페이스 | `cleanWs()` — Jenkins는 워크스페이스가 남아 이전 빌드가 오염시킨다 |
| 병렬 | `parallel` 블록. 단, 아키텍처 검증은 병렬에 넣지 않는다 |

**`allowEmptyResults: false`가 중요하다.** 테스트가 0건인데 성공으로
표시되는 것을 막는다.

## 수동 승인 게이트

```groovy
    stage('프로덕션 배포 승인') {
      when { branch 'main' }
      options { timeout(time: 24, unit: 'HOURS') }
      input {
        message '프로덕션에 배포합니까?'
        ok '배포'
        submitter 'release-managers'          // 승인 가능 그룹 제한
        parameters {
          string(name: 'RELEASE_NOTE', defaultValue: '', description: '릴리스 노트')
        }
      }
      steps { echo "승인자: ${env.BUILD_USER ?: 'unknown'}" }
    }
```

| 항목 | 의미 |
|------|------|
| `submitter` | 승인 가능한 사용자·그룹 제한. **없으면 누구나 승인 가능** |
| `timeout` | 승인 대기 무한 방지. 이그제큐터 점유를 막는다 |
| `input` 블록 위치 | `stage` 레벨에 두면 이그제큐터를 점유하지 않는다 |

**`input`을 `steps` 안에 두면 승인 대기 중 이그제큐터를 점유한다.**
`stage` 레벨의 `input` 지시자를 쓴다.

## 배포 스테이지

```groovy
    stage('배포') {
      when { branch 'main' }
      environment {
        DEPLOY_TOKEN = credentials('prod-deploy-token')
      }
      steps {
        lock(resource: 'production-deploy') {   // 배포 직렬화
          sh './scripts/deploy.sh production'
        }
      }
      post {
        failure { sh './scripts/rollback.sh' }
      }
    }
```

`lock`은 Lockable Resources 플러그인이 필요하다. 여러 파이프라인이 같은
환경에 배포할 때 충돌을 막는다.

## 시크릿

| 규칙 | 설명 |
|------|------|
| 저장 | Jenkins Credentials (폴더·전역 스코프) |
| 참조 | `credentials('id')` 또는 `withCredentials` 블록 |
| 자동 변수 | `X = credentials('id')`는 `X_USR`, `X_PSW`도 생성 |
| 마스킹 | 로그에서 자동 마스킹. 단 가공된 값은 마스킹되지 않는다 |
| 폴더 스코프 | 프로덕션 자격증명은 폴더로 격리하여 접근 제한 |

```groovy
withCredentials([usernamePassword(credentialsId: 'registry',
                                  usernameVariable: 'U', passwordVariable: 'P')]) {
  sh 'echo "$P" | docker login -u "$U" --password-stdin'
}
```

**`sh "... ${SECRET} ..."` (큰따옴표 보간)을 쓰지 않는다.**
Groovy가 먼저 치환하여 값이 프로세스 목록·로그에 노출된다.
작은따옴표 + 환경 변수 참조를 쓴다.

## 주의사항

| 함정 | 대응 |
|------|------|
| 워크스페이스 오염 | `cleanWs()` 또는 `deleteDir()` |
| `input`이 이그제큐터 점유 | `stage` 레벨 `input` 지시자 사용 |
| 큰따옴표 보간으로 시크릿 노출 | 작은따옴표 + `$VAR` |
| 플러그인 버전 미고정 | 재현성 저하. 버전을 관리 대상으로 |
| 에이전트 환경 불일치 | Docker 에이전트로 환경 고정 |
| 스크립티드 남용 | 선언적으로 표현 가능하면 선언적으로 |
| `catchError` 오용 | 실패를 숨긴다. 게이트 우회로 쓰지 않는다 |

## 에이전트 선택

| 방식 | 적합 |
|------|------|
| `agent { docker { image } }` | 환경 고정이 필요한 대부분의 경우 (권장) |
| `agent { label 'linux' }` | 특정 하드웨어·도구가 필요할 때 |
| `agent none` + 스테이지별 지정 | 스테이지마다 다른 환경이 필요할 때 |

`agent any`는 환경이 빌드마다 달라져 재현성을 해친다. 피한다.
