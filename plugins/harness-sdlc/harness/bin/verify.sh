#!/usr/bin/env bash
# 하네스 구조를 검증한다.
# 사용법: harness/bin/verify.sh   (저장소 루트 또는 아무 곳에서나)

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PASS=0; FAIL=0; WARN=0
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
warn() { printf '  \033[33mWARN\033[0m %s\n' "$1"; WARN=$((WARN+1)); }

# 하네스 소스 저장소와 설치된 저장소를 구분한다.
# 두 곳의 루트 진입 문서는 역할이 다르다:
#   소스 저장소 — 하네스를 어떻게 수정하는가 (배포되지 않음)
#   설치 저장소 — 파이프라인을 어떻게 운영하는가 (entrypoints/ 에서 배포됨)
# 따라서 라우팅 표 같은 운영 규약은 각각 다른 파일에서 검증해야 한다.
if head -3 CLAUDE.md 2>/dev/null | grep -q 'harness-source-repo'; then
  REPO_KIND="소스 저장소"
  ENTRY_AGENTS="harness/entrypoints/AGENTS.md"
  AGENT_ROOT="agents"
  SKILL_ROOT="skills"
else
  REPO_KIND="설치된 저장소"
  ENTRY_AGENTS="AGENTS.md"
  AGENT_ROOT=".claude/agents"
  SKILL_ROOT=".claude/skills"
fi

echo "하네스 검증: $ROOT  ($REPO_KIND)"
echo

# ── 1. 필수 경로 ──────────────────────────────────────────────
echo "1. 필수 경로"
for p in harness/pipeline.md harness/README.md \
         harness/execution-modes.md harness/config.yml \
         harness/principles/architecture.md harness/principles/ddd.md \
         harness/principles/testing.md harness/principles/documentation.md \
         harness/principles/workspace.md \
         harness/adapters/claude-code.md harness/adapters/generic-agent.md \
         harness/entrypoints/CLAUDE.md harness/entrypoints/AGENTS.md \
         "$AGENT_ROOT" "$SKILL_ROOT" docs/template CLAUDE.md AGENTS.md; do
  [[ -e "$p" ]] && ok "$p" || bad "$p 없음"
done
echo

# ── 2. 커맨드 미생성 ──────────────────────────────────────────
echo "2. 커맨드 미생성 (하네스는 커맨드를 만들지 않는다)"
if [[ -d .claude/commands ]] && [[ -n "$(ls -A .claude/commands 2>/dev/null)" ]]; then
  bad ".claude/commands/ 에 파일이 있음"
else
  ok ".claude/commands/ 비어 있음 또는 없음"
fi
echo

# ── 3. 에이전트 frontmatter ───────────────────────────────────
echo "3. 에이전트 정의"
AGENT_COUNT=0
for f in "$AGENT_ROOT"/*.md; do
  [[ -e "$f" ]] || { bad "에이전트 파일이 하나도 없음"; break; }
  AGENT_COUNT=$((AGENT_COUNT+1))
  name="$(basename "$f" .md)"
  errs=""
  head -1 "$f" | grep -qx -- '---' || errs="$errs frontmatter시작없음"
  grep -qE "^name:[[:space:]]*${name}\$" "$f" || errs="$errs name불일치"
  grep -qE '^description:[[:space:]]*.+' "$f" || errs="$errs description없음"
  grep -qE '^model:[[:space:]]*opus\b' "$f" || errs="$errs model!=opus"
  [[ -z "$errs" ]] && ok "$name" || bad "$name —$errs"
done
echo "  → 에이전트 ${AGENT_COUNT}개"
echo

# ── 4. 스킬 frontmatter + 크기 ────────────────────────────────
echo "4. 스킬 정의"
SKILL_COUNT=0
for d in "$SKILL_ROOT"/*/; do
  [[ -d "$d" ]] || { bad "스킬 디렉토리가 하나도 없음"; break; }
  SKILL_COUNT=$((SKILL_COUNT+1))
  name="$(basename "$d")"
  f="$d/SKILL.md"
  if [[ ! -f "$f" ]]; then bad "$name — SKILL.md 없음"; continue; fi
  errs=""
  head -1 "$f" | grep -qx -- '---' || errs="$errs frontmatter시작없음"
  grep -qE "^name:[[:space:]]*${name}\$" "$f" || errs="$errs name불일치"
  grep -qE '^description:[[:space:]]*.+' "$f" || errs="$errs description없음"
  lines=$(wc -l < "$f" | tr -d ' ')
  if [[ -z "$errs" ]]; then
    if (( lines > 500 )); then
      warn "$name — SKILL.md ${lines}줄 초과 (500줄 기준, references/ 분리 검토)"
    else
      ok "$name (${lines}줄)"
    fi
  else
    bad "$name —$errs"
  fi
done
echo "  → 스킬 ${SKILL_COUNT}개"
echo

# ── 5. 후속 작업 키워드 (오케스트레이터) ──────────────────────
echo "5. 오케스트레이터 후속 작업 키워드"
ORCH="$SKILL_ROOT/sdlc-orchestrator/SKILL.md"
if [[ -f "$ORCH" ]]; then
  desc="$(awk '/^description:/{f=1} f{print} /^---$/{if(NR>1&&f)exit}' "$ORCH")"
  miss=""
  for kw in 재실행 이어서 업데이트 수정 보완; do
    grep -q -- "$kw" <<<"$desc" || miss="$miss $kw"
  done
  [[ -z "$miss" ]] && ok "후속 키워드 포함" || warn "누락된 후속 키워드:$miss"
else
  bad "$ORCH 없음"
fi
echo

# ── 6. 하네스 자산 참조 경로 ──────────────────────────────────
# 하네스 자산(harness/, .claude/, docs/template/)에 대한 참조만 검증한다.
# 플러그인 패키지에서는 .claude/ 경로가 설치 후 생성되는 배포 경로이므로
# 해당 참조를 검증 대상에서 제외한다.
# docs/{prd,plan,design,...} 하위는 파이프라인 실행 시 생성되는 산출물이므로 제외.
echo "6. 하네스 자산 참조 경로"
BROKEN=0
while IFS= read -r ref; do
  [[ -e "$ref" ]] || { bad "참조 대상 없음: $ref"; BROKEN=$((BROKEN+1)); }
done < <(
  grep -rhoE '`(harness/|\.claude/|docs/template/)[A-Za-z0-9._/-]+`' \
    "$AGENT_ROOT" "$SKILL_ROOT" harness CLAUDE.md AGENTS.md 2>/dev/null \
  | tr -d '`' \
  | if [[ "$REPO_KIND" == "소스 저장소" ]]; then
      grep -vE '^\.claude/|\{|\*|\.\.\.'
    else
      grep -vE '\{|\*|\.\.\.'
    fi \
  | sed 's:/$::' | sort -u
)
(( BROKEN == 0 )) && ok "깨진 참조 없음"
echo

# ── 6-1. 산출물 디렉토리 ──────────────────────────────────────
echo "6-1. 산출물 디렉토리"
for d in prd plan plan/adr design implement test review report; do
  [[ -d "docs/$d" ]] && ok "docs/$d/" || bad "docs/$d/ 없음"
done
echo

# ── 7. 문서 템플릿 ────────────────────────────────────────────
echo "7. 문서 템플릿"
for t in prd analysis-research analysis-codebase tech-spec adr wbs design \
         test-report review impl-notes completion-report harness-improvement; do
  [[ -f "docs/template/$t.md" ]] && ok "docs/template/$t.md" || bad "docs/template/$t.md 없음"
done
echo

# ── 8. 실행 모드 설정 ─────────────────────────────────────────
echo "8. 실행 모드"
MODE="$(grep -E '^execution_mode:' harness/config.yml 2>/dev/null | awk '{print $2}')"
case "$MODE" in
  skill|balanced|agent|ask) ok "execution_mode = $MODE" ;;
  "") bad "harness/config.yml 에 execution_mode 없음" ;;
  *)  bad "execution_mode 값이 유효하지 않음: $MODE (skill|balanced|agent|ask)" ;;
esac
for m in skill balanced agent; do
  grep -q "\`$m\`" "$SKILL_ROOT/sdlc-orchestrator/SKILL.md" \
    && ok "오케스트레이터가 $m 모드를 다룸" \
    || bad "오케스트레이터에 $m 모드 분기 없음"
done
echo

# ── 9. 범용 에이전트 라우팅 ───────────────────────────────────
# 범용 도구에는 자동 트리거가 없으므로 라우팅 표가 유일한 경로다.
# 검증 대상은 "대상 저장소가 실제로 읽게 될" AGENTS.md다.
echo "9. 범용 에이전트 라우팅 ($ENTRY_AGENTS)"
if grep -q '요청 → 스킬 라우팅' "$ENTRY_AGENTS" 2>/dev/null; then
  ok "라우팅 표 존재"
  MISSING=""
  for d in "$SKILL_ROOT"/*/; do
    n="$(basename "$d")"
    grep -q "\`$n\`" "$ENTRY_AGENTS" || MISSING="$MISSING $n"
  done
  [[ -z "$MISSING" ]] && ok "모든 스킬이 라우팅 표에 등장" \
                      || bad "라우팅 표에 누락된 스킬:$MISSING"
else
  bad "$ENTRY_AGENTS 에 '요청 → 스킬 라우팅' 표 없음 — 범용 도구가 스킬을 찾지 못함"
fi
for f in .claude/agents .claude/skills harness/pipeline.md; do
  grep -q "$f" "$ENTRY_AGENTS" || bad "$ENTRY_AGENTS 가 $f 를 가리키지 않음"
done
echo

# ── 9-1. 도구별 진입점 생성 로직 ──────────────────────────────
echo "9-1. install.sh 도구별 진입점"
for f in GEMINI.md .cursor/rules/harness.mdc .github/copilot-instructions.md CONVENTIONS.md; do
  grep -q "$f" harness/bin/install.sh && ok "$f 생성 로직 존재" \
                                      || bad "$f 생성 로직 없음"
done
echo

# ── 9-2. 진입점 배포 분리 ─────────────────────────────────────
# 하네스 개발용 루트 문서가 대상 저장소로 새어나가면, 대상 저장소의 에이전트가
# "여기서 애플리케이션을 개발하지 않는다"로 인식해 개발 요청을 거부한다.
echo "9-2. 진입점 배포 분리"
if grep -q 'entrypoints/\$f' harness/bin/install.sh; then
  ok "install.sh가 harness/entrypoints/ 에서 진입점을 배포함"
else
  bad "install.sh가 배포용 템플릿을 쓰지 않음 — 루트 문서가 대상 저장소로 유출됨"
fi
if grep -qE 'cp "\$SRC/\$f"|cp "\$SRC/(CLAUDE|AGENTS)\.md"' harness/bin/install.sh; then
  bad "install.sh가 루트 진입 문서를 그대로 복사함"
else
  ok "install.sh가 루트 진입 문서를 복사하지 않음"
fi
for f in harness/entrypoints/CLAUDE.md harness/entrypoints/AGENTS.md; do
  if grep -q 'harness-source-repo' "$f" 2>/dev/null; then
    bad "$f 에 소스 저장소 마커가 있음 — 배포용 템플릿이 아님"
  else
    ok "$f 배포용으로 분리됨"
  fi
done
if [[ "$REPO_KIND" == "소스 저장소" ]]; then
  grep -q '여기서 애플리케이션을 개발하지 않는다' harness/entrypoints/CLAUDE.md \
    && bad "배포용 CLAUDE.md에 하네스 저장소 전용 지시가 남아 있음" \
    || ok "배포용 CLAUDE.md에 하네스 전용 지시 없음"
fi
echo

# ── 10. .gitignore ────────────────────────────────────────────
echo "10. .gitignore"
if grep -qxF '/_workspace/' .gitignore 2>/dev/null; then
  ok "/_workspace/ 제외됨"
else
  bad "/_workspace/ 가 .gitignore에 없음"
fi
echo

# ── 결과 ──────────────────────────────────────────────────────
printf '결과: \033[32m통과 %d\033[0m / \033[33m경고 %d\033[0m / \033[31m실패 %d\033[0m\n' \
  "$PASS" "$WARN" "$FAIL"
(( FAIL == 0 )) || exit 1
