#!/usr/bin/env bash
# Create GitHub issues from the markdown files in docs/backlog/.
#
# Each backlog file carries YAML frontmatter with `title` and `labels`; the
# body below the frontmatter becomes the issue body. Labels are created if they
# do not already exist.
#
# Idempotent: an issue whose title already exists (open or closed) is skipped,
# so re-running after adding a backlog file only creates the new one.
#
# Requires the GitHub CLI, authenticated: https://cli.github.com
#
#   ./scripts/seed-issues.sh            # create issues
#   ./scripts/seed-issues.sh --dry-run  # print what would be created

set -euo pipefail

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKLOG="$REPO_ROOT/docs/backlog"

command -v gh >/dev/null || { echo "gh not found: https://cli.github.com" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "gh is not authenticated; run: gh auth login" >&2; exit 1; }

# Titles that already exist, so a re-run does not duplicate them.
existing="$(gh issue list --state all --limit 500 --json title --jq '.[].title')"

# Labels used anywhere in the backlog, created up front. Colours are grouped by
# prefix so the issue list is scannable at a glance.
label_colour() {
  case "$1" in
    type:feat)  echo "1d76db" ;;
    type:fix)   echo "d73a4a" ;;
    type:docs)  echo "0075ca" ;;
    type:test)  echo "5319e7" ;;
    type:chore) echo "cfd3d7" ;;
    type:spike) echo "fbca04" ;;
    milestone:*) echo "006b75" ;;
    area:*)     echo "c2e0c6" ;;
    *)          echo "ededed" ;;
  esac
}

created=0
skipped=0

for file in "$BACKLOG"/*.md; do
  [[ -e "$file" ]] || continue

  title="$(awk -F': ' '/^title:/ { sub(/^title: */, ""); gsub(/^"|"$/, ""); print; exit }' "$file")"
  labels="$(awk '/^labels:/ { sub(/^labels: */, ""); gsub(/[][" ]/, ""); print; exit }' "$file")"
  body="$(awk 'BEGIN { n = 0 } /^---$/ { n++; next } n >= 2' "$file")"

  if [[ -z "$title" ]]; then
    echo "skip  $(basename "$file") — no title in frontmatter" >&2
    continue
  fi

  if grep -Fxq "$title" <<<"$existing"; then
    echo "exists  $title"
    skipped=$((skipped + 1))
    continue
  fi

  if (( DRY_RUN )); then
    echo "would create  [$labels] $title"
    continue
  fi

  IFS=',' read -ra label_list <<<"$labels"
  label_args=()
  for label in "${label_list[@]}"; do
    [[ -n "$label" ]] || continue
    gh label create "$label" --color "$(label_colour "$label")" >/dev/null 2>&1 || true
    label_args+=(--label "$label")
  done

  gh issue create --title "$title" --body "$body" "${label_args[@]}" >/dev/null
  echo "created  $title"
  created=$((created + 1))
done

echo
echo "created $created, already present $skipped"
