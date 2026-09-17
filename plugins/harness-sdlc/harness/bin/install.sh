#!/usr/bin/env bash
# Compatibility notice only; never writes into the target repository.
set -euo pipefail
echo '복사 설치는 더 이상 사용하지 않습니다.' >&2
echo '마켓플레이스에서 harness-sdlc를 설치한 뒤 대상 프로젝트에서 harness-init 스킬을 실행하십시오.' >&2
echo '기존 복사 설치 파일은 유지되며, init 인터뷰에서 프로젝트 설정을 .harness/로 이관합니다.' >&2
exit 1
