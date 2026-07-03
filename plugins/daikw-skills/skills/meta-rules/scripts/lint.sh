#!/usr/bin/env bash
# meta-rules lint: machine-checkable validation for daikw-skills SKILL.md files.
#
# Usage:
#   lint.sh                 # lint every skill under plugins/daikw-skills/skills/*/
#   lint.sh <name-or-path>  # lint one skill only (bare name resolved under skills/)
#   lint.sh <a> <b> ...     # lint multiple skills
#
# Checks (see meta-rules/SKILL.md "scripts/lint.sh" section for the rationale):
#   1. frontmatter `name:` matches the directory name
#   2. each `allowed-tools:` entry is a known tool name (mcp__* always accepted)
#   3. references/ scripts/ assets/ paths mentioned in the body actually exist
#   4. supply-chain contradictions: curl|sh, one-shot launcher @latest, Docker :latest
#   5. description length (~1024 char guideline) and presence of a "when NOT to use" cue (warning only)
#
# Exit code: 1 if any error-level finding, 0 otherwise (warnings do not fail the run).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Known tool names as of this writing. Maintain manually as the harness's tool
# surface evolves — this list is not fetched dynamically. mcp__* is always
# accepted since MCP servers register tools at runtime.
KNOWN_TOOLS=(
  Read Write Edit Glob Grep Bash BashOutput KillShell
  WebFetch WebSearch AskUserQuestion Task Agent Artifact
  TaskCreate TaskUpdate TaskList TaskGet TaskStop TodoWrite
  NotebookEdit Skill SlashCommand ExitPlanMode
  CronCreate CronList CronDelete Monitor SendMessage
  EnterWorktree ExitWorktree
)

errors=0
warnings=0
skill_count=0

is_known_tool() {
  local tool="$1"
  case "$tool" in
    mcp__*) return 0 ;;
  esac
  local t
  for t in "${KNOWN_TOOLS[@]}"; do
    [[ "$tool" == "$t" ]] && return 0
  done
  return 1
}

strip_quotes() {
  local s="$1"
  s="${s#\"}"; s="${s%\"}"
  s="${s#\'}"; s="${s%\'}"
  printf '%s' "$s"
}

lint_skill() {
  local dir="$1"
  local skill_md="$dir/SKILL.md"
  local name_dir
  name_dir="$(basename "$dir")"

  if [[ ! -f "$skill_md" ]]; then
    echo "ERROR [$name_dir] SKILL.md not found"
    errors=$((errors + 1))
    return
  fi

  local frontmatter body
  frontmatter="$(awk 'BEGIN{c=0} /^---[[:space:]]*$/{c++; next} c==1' "$skill_md")"
  body="$(awk 'BEGIN{c=0} /^---[[:space:]]*$/{c++; next} c>=2' "$skill_md")"

  # 1. name matches directory name
  local name
  name="$(printf '%s\n' "$frontmatter" | awk -F': *' '/^name:/{print $2; exit}')"
  name="$(strip_quotes "$name")"
  if [[ -z "$name" ]]; then
    echo "ERROR [$name_dir] frontmatter missing 'name:'"
    errors=$((errors + 1))
  elif [[ "$name" != "$name_dir" ]]; then
    echo "ERROR [$name_dir] frontmatter name '$name' does not match directory name"
    errors=$((errors + 1))
  fi

  # 2. allowed-tools entries exist in the known tool list
  local in_tools=0 line tool
  while IFS= read -r line; do
    if [[ "$line" =~ ^allowed-tools: ]]; then
      in_tools=1
      continue
    fi
    if [[ $in_tools -eq 1 ]]; then
      if [[ "$line" =~ ^[A-Za-z_-]+: ]]; then
        in_tools=0
        continue
      fi
      if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*(.+)$ ]]; then
        tool="$(strip_quotes "${BASH_REMATCH[1]}")"
        if ! is_known_tool "$tool"; then
          echo "ERROR [$name_dir] allowed-tools references unknown tool: $tool"
          errors=$((errors + 1))
        fi
      fi
    fi
  done <<< "$frontmatter"

  # 3. references/ scripts/ assets/ path references in the body actually exist
  local ref
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    if [[ ! -e "$dir/$ref" ]]; then
      echo "ERROR [$name_dir] referenced path does not exist: $ref"
      errors=$((errors + 1))
    fi
  done < <(printf '%s\n' "$body" | grep -oE '(references|scripts|assets)/[A-Za-z0-9_./-]+' | sort -u)

  # 4. supply-chain contradictions (see rules/supply-chain-security.md)
  if printf '%s\n' "$body" | grep -qE 'curl[^|]*\|[[:space:]]*(sh|bash)\b'; then
    echo "ERROR [$name_dir] supply-chain: curl | sh/bash pattern detected"
    errors=$((errors + 1))
  fi
  if printf '%s\n' "$body" | grep -qE '(npx|bunx|pnpm dlx|uvx)[[:space:]]+[A-Za-z0-9@/_.-]+@latest'; then
    echo "ERROR [$name_dir] supply-chain: one-shot launcher with @latest detected"
    errors=$((errors + 1))
  fi
  if printf '%s\n' "$body" | grep -qE '\bFROM[[:space:]]+[A-Za-z0-9._/-]+:latest\b'; then
    echo "ERROR [$name_dir] supply-chain: Docker base image pinned to :latest"
    errors=$((errors + 1))
  fi

  # 5. description length and "when NOT to use" cue (warning-level only)
  local description desc_len
  description="$(printf '%s\n' "$frontmatter" | awk -F': *' '/^description:/{ $1=""; print substr($0,2); exit }')"
  desc_len=${#description}
  if [[ $desc_len -gt 1100 ]]; then
    echo "ERROR [$name_dir] description exceeds ~1024 chars (measured $desc_len chars on the raw frontmatter line)"
    errors=$((errors + 1))
  fi
  if [[ -n "$description" ]] && ! printf '%s' "$description" | grep -qE '使わない|対象外|しない場合|ではなく'; then
    echo "WARN  [$name_dir] description has no 'when NOT to use' cue (使わない/対象外/しない場合 等)"
    warnings=$((warnings + 1))
  fi
}

targets=()
if [[ $# -eq 0 ]]; then
  for d in "$SKILLS_ROOT"/*/; do
    targets+=("${d%/}")
  done
else
  for arg in "$@"; do
    if [[ -d "$arg" ]]; then
      targets+=("$arg")
    elif [[ -d "$SKILLS_ROOT/$arg" ]]; then
      targets+=("$SKILLS_ROOT/$arg")
    else
      echo "ERROR: skill not found: $arg" >&2
      exit 1
    fi
  done
fi

for t in "${targets[@]}"; do
  lint_skill "$t"
  skill_count=$((skill_count + 1))
done

echo "---"
echo "lint.sh: $errors error(s), $warnings warning(s) across $skill_count skill(s)"
[[ $errors -gt 0 ]] && exit 1
exit 0
