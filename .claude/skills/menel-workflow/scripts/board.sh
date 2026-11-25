#!/usr/bin/env bash
# Pomocnik do tablicy GitHub Projects januszex-ai/1.
# Użycie:
#   board.sh list [Status]          – issues bieżącego repo w kolumnie (domyślnie Todo)
#   board.sh move <issue> <Status>  – przenieś issue do kolumny (np. "In Progress", "Review")
# Wymaga: gh z scope "project"  ->  gh auth refresh -s project
set -euo pipefail

OWNER="${MENEL_OWNER:-januszex-ai}"
PROJECT="${MENEL_PROJECT:-1}"
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"

lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

cmd="${1:-}"; shift || true

case "$cmd" in
  list)
    status="$(lower "${1:-Todo}")"
    gh project item-list "$PROJECT" --owner "$OWNER" --format json --limit 1000 \
      --jq ".items[]
            | select(.content.type == \"Issue\")
            | select(.content.repository == \"$REPO\")
            | select(((.status // \"\") | ascii_downcase) == \"$status\")
            | \"#\(.content.number)\t[\((.labels // []) | join(\",\"))]\t\(.assignees // [] | join(\",\"))\t\(.content.title)\""
    ;;
  move)
    issue="${1:?numer issue}"; target="$(lower "${2:?status, np. \"In Progress\"}")"

    project_id="$(gh project view "$PROJECT" --owner "$OWNER" --format json --jq .id)"
    field_id="$(gh project field-list "$PROJECT" --owner "$OWNER" --format json \
      --jq '.fields[] | select(.name == "Status") | .id')"
    option_id="$(gh project field-list "$PROJECT" --owner "$OWNER" --format json \
      --jq ".fields[] | select(.name == \"Status\") | .options[]
            | select((.name | ascii_downcase) == \"$target\") | .id")"

    if [[ -z "$field_id" || -z "$option_id" ]]; then
      echo "Brak pola Status lub opcji \"$2\" na tablicy. Dostępne:" >&2
      gh project field-list "$PROJECT" --owner "$OWNER" --format json \
        --jq '.fields[] | select(.name == "Status") | .options[].name' >&2
      exit 1
    fi

    item_id="$(gh project item-list "$PROJECT" --owner "$OWNER" --format json --limit 1000 \
      --jq ".items[] | select(.content.repository == \"$REPO\" and .content.number == $issue) | .id")"
    if [[ -z "$item_id" ]]; then
      url="$(gh issue view "$issue" --json url -q .url)"
      item_id="$(gh project item-add "$PROJECT" --owner "$OWNER" --url "$url" --format json --jq .id)"
    fi

    gh project item-edit --id "$item_id" --project-id "$project_id" \
      --field-id "$field_id" --single-select-option-id "$option_id" >/dev/null
    echo "#$issue -> $2"
    ;;
  *)
    sed -n '2,6p' "$0" >&2
    exit 1
    ;;
esac
