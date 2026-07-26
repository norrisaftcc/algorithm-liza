#!/usr/bin/env bash
#
# Push the current branch stack and open its pull requests.
#
# The environment this repository is authored in cannot reach the GitHub API —
# no credentials, no gh, and the network allowlist blocks the host. So PR bodies
# are written to docs/pr/*.md the way backlog issues are written to
# docs/backlog/*.md, and this script turns them into real pull requests from a
# machine that is logged in.
#
# The side effect is worth keeping on purpose: a PR body that lives in the
# repository is reviewable in a diff and survives the pull request being
# squashed away.
#
# Idempotent. A branch that already has an open PR is reported and skipped, so
# re-running after a partial failure is safe.
#
# Bodies are read from the working tree you run this from, not from the branch
# being opened. That is why docs/pr/001-project-setup.md can describe a branch
# that does not itself contain the file — run this from the tip of the stack.
#
# Usage:
#   ./scripts/open-prs.sh --dry-run     # show what would happen
#   ./scripts/open-prs.sh
#
# Run ./scripts/seed-issues.sh first. This script resolves the ISSUE_<n>
# placeholders in the PR bodies against the issues that script created, and will
# refuse to open a PR whose placeholder it cannot resolve.

set -euo pipefail

cd "$(dirname "$0")/.."

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

# branch|base|body-file|title — order matters, a stacked PR needs its base to
# exist. The title is written out rather than taken from the last commit
# subject, because the last commit on a branch is often the smallest thing on
# it and makes a misleading title.
STACK=(
  "docs/project-setup|main|docs/pr/001-project-setup.md|docs: establish project workflow, roadmap, ADRs, and backlog"
  "feat/stub-inference-server|docs/project-setup|docs/pr/002-stub-inference-server.md|feat: fixture-driven stub inference server"
)

command -v gh >/dev/null || { echo "gh is not installed: https://cli.github.com" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh is not authenticated: run 'gh auth login'" >&2; exit 1; }

# Map ISSUE_<backlog-number> to a real issue number by matching the backlog
# file's frontmatter title against open issues. Empty if no match.
resolve_issue() {
  local n="$1" title
  local file
  file=$(ls "docs/backlog/${n}-"*.md 2>/dev/null | head -1) || true
  [[ -n "$file" ]] || return 0
  # Same extraction seed-issues.sh uses, so the titles compare equal.
  title=$(awk -F': ' '/^title:/ { sub(/^title: */, ""); gsub(/^"|"$/, ""); print; exit }' "$file")
  [[ -n "$title" ]] || return 0
  gh issue list --state all --limit 200 --json number,title \
    --jq ".[] | select(.title == \"${title}\") | .number" | head -1
}

# Substitute every ISSUE_<n> placeholder. Fails loudly rather than opening a PR
# with a dangling "Closes ISSUE_18" in it.
render_body() {
  local body
  body=$(cat "$1")
  local n num
  for n in $(grep -o 'ISSUE_[0-9]\+' "$1" | sed 's/ISSUE_//' | sort -u); do
    num=$(resolve_issue "$n")
    if [[ -z "$num" ]]; then
      echo "  ! no issue found for docs/backlog/${n}-*.md" >&2
      echo "    run ./scripts/seed-issues.sh first" >&2
      return 1
    fi
    body=${body//ISSUE_${n}/\#${num}}
  done
  printf '%s\n' "$body"
}

for spec in "${STACK[@]}"; do
  IFS='|' read -r branch base body_file title <<<"$spec"

  git show-ref --verify --quiet "refs/heads/${branch}" || {
    echo "skip ${branch}: no such local branch"
    continue
  }
  [[ -f "$body_file" ]] || { echo "skip ${branch}: missing ${body_file}" >&2; continue; }

  existing=$(gh pr list --head "$branch" --state open --json number --jq '.[0].number' 2>/dev/null || true)
  if [[ -n "$existing" ]]; then
    echo "skip ${branch}: PR #${existing} is already open"
    continue
  fi

  if (( DRY_RUN )); then
    echo "would push ${branch} and open: ${title}"
    echo "  base ${base}, body ${body_file}"
    render_body "$body_file" >/dev/null && echo "  body renders, all issue links resolve"
    continue
  fi

  echo "pushing ${branch}"
  git push -u origin "$branch"

  echo "opening PR: ${title}"
  render_body "$body_file" | gh pr create \
    --base "$base" --head "$branch" --title "$title" --body-file -
done

if (( DRY_RUN )); then
  echo
  echo "dry run only, nothing pushed. Re-run without --dry-run."
fi
