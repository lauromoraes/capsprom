#!/usr/bin/env bash
# Archive local CapsProm artifacts to bioserver04 and enforce the local storage budget.
# Contract: configs/capsprom_local_storage_policy_v1.yaml. Run from WSL at the repository root.
#   check  - report project footprint against the budget (read-only)
#   copy   - rsync ARCHIVE + BACKUP sets, then verify SHA-256 on the remote host
#   prune  - re-verify remotely, then delete only the ARCHIVE set locally
set -euo pipefail

REMOTE="${REMOTE:-bioserver04}"
DEST="${DEST:-/home/lauro/backups/capsprom/local-archive-v1}"
BUDGET_GB="${BUDGET_GB:-8}"
KEY="$HOME/.ssh/capsprom_bioserver04"
SSH=(ssh); [[ -f "$KEY" ]] && SSH+=(-i "$KEY")
STAGE="tmp/storage_archive_v1"

# Copied and later removed locally (unreferenced by src/, scripts/, configs/, specs/).
ARCHIVE_DIRS=(data/interim/dinuc data/interim/trinuc data/interim/aligned_fasta data/interim/cropped_fasta)
ARCHIVE_GLOB_DIR=outputs/neural_smoke   # only *.pt checkpoints are pruned here
# Copied as off-machine backup only; never pruned.
BACKUP=(data/raw data/processed mlflow.db mlruns)

remote() { "${SSH[@]}" "$REMOTE" "$@"; }
verify() { remote "cd '$DEST' && sha256sum --quiet -c manifest.sha256"; }
# Exactly the files prune deletes; manifest paths start at column 67 ("<64-hex>  <path>").
to_delete() { { find "${ARCHIVE_DIRS[@]}" -type f; find "$ARCHIVE_GLOB_DIR" -type f -name '*.pt'; } | LC_ALL=C sort; }

case "${1:-check}" in
  check)
    du -sh data/* outputs mlruns mlflow.db 2>/dev/null | sort -h
    used_kb=$(du -sk --exclude=.venv --exclude=.git . | cut -f1)
    echo "project (excluding .venv/.git): $((used_kb / 1048576)) GB; budget ${BUDGET_GB} GB"
    (( used_kb <= BUDGET_GB * 1048576 )) || { echo "OVER BUDGET: run copy then prune"; exit 1; }
    ;;
  copy)
    pgrep -f "mlflow (server|ui)|python[0-9.]* -m capsprom" >/dev/null && { echo "abort: a local MLflow/CapsProm process is running"; exit 1; }
    mkdir -p "$STAGE"
    paths=("${ARCHIVE_DIRS[@]}" "$ARCHIVE_GLOB_DIR" "${BACKUP[@]}")
    echo "hashing ${#paths[@]} paths (slow on large trees)..."
    find "${paths[@]}" -type f -print0 | sort -z | xargs -0 sha256sum > "$STAGE/manifest.sha256"
    remote "mkdir -p '$DEST' && df -h '$DEST' | tail -1"
    rsync -a --relative --info=progress2 -e "${SSH[*]}" "${paths[@]}" "$REMOTE:$DEST/"
    rsync -a -e "${SSH[*]}" "$STAGE/manifest.sha256" "$REMOTE:$DEST/"
    verify
    date -u +%Y-%m-%dT%H:%M:%SZ > "$STAGE/VERIFIED"
    echo "copy verified: $(wc -l < "$STAGE/manifest.sha256") files at $REMOTE:$DEST"
    ;;
  prune)
    [[ -f "$STAGE/VERIFIED" ]] || { echo "abort: run copy first"; exit 1; }
    verify   # fresh remote check immediately before deletion
    # Abort if any file to delete was added or changed after copy (it would have no backup).
    unarchived=$(LC_ALL=C comm -23 <(to_delete) <(cut -c67- "$STAGE/manifest.sha256" | LC_ALL=C sort))
    [[ -z "$unarchived" ]] || { printf 'abort: not in archive manifest:\n%s\n' "$unarchived"; exit 1; }
    awk 'NR==FNR {d[$0]; next} substr($0, 67) in d' <(to_delete) "$STAGE/manifest.sha256" \
      | sha256sum --quiet -c || { echo "abort: local files changed since copy"; exit 1; }
    rm -rf -- "${ARCHIVE_DIRS[@]}"
    find "$ARCHIVE_GLOB_DIR" -name '*.pt' -delete
    cat > data/interim/ARCHIVED.md <<NOTE
# Archived interim data
Moved on $(date -u +%Y-%m-%d) to \`$REMOTE:$DEST\` (SHA-256 verified; manifest at \`$DEST/manifest.sha256\`):
${ARCHIVE_DIRS[*]} and \`$ARCHIVE_GLOB_DIR/**/*.pt\`.
Restore: \`rsync -a $REMOTE:$DEST/data/interim/<name> data/interim/\`
NOTE
    echo "pruned; run: scripts/storage_archive.sh check"
    ;;
  *) echo "usage: $0 {check|copy|prune}"; exit 2 ;;
esac
