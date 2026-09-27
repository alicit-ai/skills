#!/usr/bin/env bash
# Copy the alicit skill from one alicit release into this marketplace.
#
#   scripts/sync-alicit.sh <alicit-checkout> <tag>
#
# The alicit repository is the source of the skill: it changes in the same
# pull request as the CLI that it describes. This script takes exactly the
# files that git tracks under skills/alicit at <tag>, so no cache or local
# file can come with them. The evals go to evals/alicit/, outside the plugin,
# because users do not need them. The plugin version becomes the CLI version.
set -euo pipefail

source_repo="${1:?usage: sync-alicit.sh <alicit-checkout> <tag>}"
tag="${2:?usage: sync-alicit.sh <alicit-checkout> <tag>}"
case "$tag" in v[0-9]*.[0-9]*.[0-9]*) ;; *) echo "ERROR: not a release tag: $tag" >&2; exit 1 ;; esac

root="$(cd "$(dirname "$0")/.." && pwd)"
commit="$(git -C "$source_repo" rev-parse --verify "$tag^{commit}")"
version="${tag#v}"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
git -C "$source_repo" archive --format=tar "$commit" skills/alicit | tar -x -C "$work"
[ -f "$work/skills/alicit/SKILL.md" ] || { echo "ERROR: $tag has no skills/alicit/SKILL.md" >&2; exit 1; }

rm -rf "$root/evals/alicit"
if [ -d "$work/skills/alicit/evals" ]; then
  mkdir -p "$root/evals"
  mv "$work/skills/alicit/evals" "$root/evals/alicit"
fi
rm -rf "$root/plugins/alicit/skills/alicit"
mkdir -p "$root/plugins/alicit/skills"
mv "$work/skills/alicit" "$root/plugins/alicit/skills/alicit"

python3 - "$root/catalog.json" "$version" "$tag" "$commit" <<'PY'
import json, sys
path, version, tag, commit = sys.argv[1:]
catalog = json.load(open(path))
plugin = next(p for p in catalog["plugins"] if p["name"] == "alicit")
plugin["version"] = version
plugin["source"].update(tag=tag, commit=commit)
open(path, "w").write(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
PY

python3 "$root/scripts/build.py"
echo "Synced the alicit skill from $tag ($commit)."
