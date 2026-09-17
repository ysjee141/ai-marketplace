#!/usr/bin/env bash
# 하네스를 대상 저장소에 설치한다.
# 기존 파일은 덮어쓰지 않는다 — 충돌 시 .harness-new 접미사로 저장하고 보고한다.
#
# 사용법: harness/bin/install.sh /path/to/target-repo

set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "사용법: $0 <대상 저장소 경로>" >&2
  exit 1
fi

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ ! -d "$TARGET" ]]; then
  echo "오류: 대상 경로가 존재하지 않습니다: $TARGET" >&2
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"

if [[ "$SRC" == "$TARGET" ]]; then
  echo "오류: 대상이 하네스 저장소 자신입니다." >&2
  exit 1
fi

CONFLICTS=()
MERGE_NEEDED=()

# 파일 하나를 설치한다. 이미 있고 내용이 다르면 .harness-new 로 저장한다.
install_file() {
  install_file_to "$1" "$1"
}

# 소스 경로와 대상 저장소 경로가 다를 때 파일을 설치한다.
install_file_to() {
  local src_rel="$1" dst_rel="$2"
  local src="$SRC/$src_rel" dst="$TARGET/$dst_rel"
  [[ -f "$src" ]] || return 0
  mkdir -p "$(dirname "$dst")"
  if [[ -f "$dst" ]]; then
    if cmp -s "$src" "$dst"; then
      return 0
    fi
    cp "$src" "$dst.harness-new"
    CONFLICTS+=("$dst_rel")
  else
    cp "$src" "$dst"
  fi
}

# 디렉토리 하위 파일을 재귀 설치한다.
install_tree() {
  install_tree_to "$1" "$1"
}

# 플러그인 표준 경로를 대상 저장소의 원래 하네스 경로로 배포한다.
install_tree_to() {
  local src_rel="$1" dst_rel="$2"
  [[ -d "$SRC/$src_rel" ]] || return 0
  local f
  while IFS= read -r -d '' f; do
    local src_file="${f#$SRC/}"
    local relative_file="${src_file#$src_rel/}"
    install_file_to "$src_file" "$dst_rel/$relative_file"
  done < <(find "$SRC/$src_rel" -type f -print0)
}

echo "하네스 설치: $SRC → $TARGET"
echo

echo "  harness/ (원칙·파이프라인·어댑터)"
install_tree "harness"

echo "  .claude/agents/ (역할 정의)"
install_tree_to "agents" ".claude/agents"

echo "  .claude/skills/ (절차 지식)"
install_tree_to "skills" ".claude/skills"

echo "  docs/template/ (문서 템플릿)"
install_tree "docs/template"

echo "  docs/ 하위 디렉토리"
for d in prd plan plan/adr design implement test review report; do
  mkdir -p "$TARGET/docs/$d"
  [[ -e "$TARGET/docs/$d/.gitkeep" ]] || touch "$TARGET/docs/$d/.gitkeep"
done

# 1차 진입점은 harness/entrypoints/ 의 배포용 템플릿에서 가져온다.
# 하네스 저장소 루트의 CLAUDE.md·AGENTS.md를 복사하지 않는 이유:
# 그 문서는 "여기서 애플리케이션을 개발하지 않는다" 같은 하네스 개발 전용
# 지시를 담고 있어, 대상 저장소에 들어가면 개발 작업 자체를 막는다.
echo "  1차 진입점 (없을 때만 생성)"
INSTALL_DATE="$(date +%F)"
for f in CLAUDE.md AGENTS.md; do
  entry_src="$SRC/harness/entrypoints/$f"
  if [[ ! -f "$entry_src" ]]; then
    echo "오류: 배포용 진입점 템플릿이 없습니다: harness/entrypoints/$f" >&2
    exit 1
  fi
  if [[ -f "$TARGET/$f" ]]; then
    echo "    - $f 이미 존재 — 건너뜀. 하네스 섹션을 수동으로 병합하십시오."
    echo "      템플릿: harness/entrypoints/$f"
    MERGE_NEEDED+=("$f")
  else
    sed "s/{{INSTALL_DATE}}/$INSTALL_DATE/g" "$entry_src" > "$TARGET/$f"
    echo "    + $f"
  fi
done

# 도구별 2차 진입점.
# AGENTS.md를 자동으로 읽지 않는 도구를 위해 얇은 포인터를 배치한다.
# 내용을 복제하지 않는 이유: 두 벌이 되면 반드시 어긋난다.
echo "  도구별 진입점 (없을 때만 생성)"
write_pointer() {
  local rel="$1" tool="$2"
  local dst="$TARGET/$rel"
  if [[ -f "$dst" ]]; then
    echo "    - $rel 이미 존재 — 건너뜀"
    MERGE_NEEDED+=("$rel")
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  # Cursor 규칙 파일은 frontmatter의 alwaysApply가 있어야 상시 적용된다
  if [[ "$rel" == *.mdc ]]; then
    cat > "$dst" <<'MDC'
---
description: 개발 파이프라인 하네스 — 모든 개발 작업에 적용
globs:
alwaysApply: true
---
MDC
  else
    : > "$dst"
  fi
  cat >> "$dst" <<EOF
# 개발 파이프라인 하네스 ($tool)

이 저장소는 기획→분석→계획→설계→구현→테스트→리뷰→배포를 통제하는
하네스를 사용한다.

**\`AGENTS.md\`를 읽고 그 지침을 따르라.** 이 파일은 포인터일 뿐이며,
실제 규약·라우팅 표·역할 정의는 전부 \`AGENTS.md\`와 그것이 가리키는
\`harness/\`, \`.claude/agents/\`, \`.claude/skills/\`에 있다.

작업을 시작하기 전에 \`_workspace/walkthrough.md\`가 있는지 먼저 확인하라.
있으면 진행 중인 작업이 있으므로 덮어쓰지 말고 재개 여부를 사용자에게 묻는다.
EOF
  echo "    + $rel"
}

write_pointer "GEMINI.md"                          "Gemini CLI"
write_pointer ".cursor/rules/harness.mdc"          "Cursor"
write_pointer ".github/copilot-instructions.md"    "GitHub Copilot"
write_pointer "CONVENTIONS.md"                     "Aider"

echo "  .gitignore 항목"
GITIGNORE="$TARGET/.gitignore"
touch "$GITIGNORE"
for pat in "/_workspace/" "/_workspace_*/"; do
  if ! grep -qxF "$pat" "$GITIGNORE" 2>/dev/null; then
    printf '%s\n' "$pat" >> "$GITIGNORE"
    echo "    + $pat"
  fi
done

chmod +x "$TARGET/harness/bin/"*.sh 2>/dev/null || true

echo
if (( ${#MERGE_NEEDED[@]} > 0 )); then
  echo "수동 병합 필요 ${#MERGE_NEEDED[@]}건: 기존 진입 파일이 있어 생성하지 않았습니다."
  printf '  %s\n' "${MERGE_NEEDED[@]}"
  echo "  → 각 파일에 \"AGENTS.md를 읽고 따르라\"는 한 줄을 추가하십시오."
  echo
fi

if (( ${#CONFLICTS[@]} > 0 )); then
  echo "충돌 ${#CONFLICTS[@]}건: 기존 파일을 유지하고 .harness-new 로 저장했습니다."
  printf '  %s\n' "${CONFLICTS[@]}"
  echo
  echo "차이를 확인한 뒤 병합하십시오:  diff <파일> <파일>.harness-new"
else
  echo "충돌 없음."
fi

echo
echo "설치 완료. 다음을 실행하여 검증하십시오:"
echo "  cd $TARGET && harness/bin/verify.sh"
