#!/usr/bin/env python3
"""Generate every marketplace manifest from catalog.json, and check the skills.

catalog.json is the only file that a person edits for a plugin's name,
version, description or keywords. This script writes, from it:

  .claude-plugin/marketplace.json            Claude Code marketplace
  .agents/plugins/marketplace.json           Codex marketplace
  plugins/<name>/.claude-plugin/plugin.json  Claude Code plugin manifest
  plugins/<name>/.codex-plugin/plugin.json   Codex plugin manifest

It also checks, for every plugin:

  - the plugins/ directories and the catalog name the same plugins;
  - each SKILL.md has YAML frontmatter that a real YAML parser reads, with a
    `name` equal to its directory and a `description` of at most 900
    characters (the agents stop at 1024; the margin is for edits);
  - no file that a user should not get is in a plugin: caches, compiled
    Python, editor files, archives or evals.

usage: build.py          write the manifests, then check
       build.py --check  fail if a manifest differs from what it would write
"""
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAX_DESCRIPTION = 900
FORBIDDEN = re.compile(r"(^|/)(__pycache__|\.DS_Store|evals|node_modules)(/|$)|\.(pyc|skill|zip|tar\.gz)$")


def plugin_manifest(catalog: dict, plugin: dict) -> dict:
    return {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "name": plugin["name"],
        "displayName": plugin["displayName"],
        "version": plugin["version"],
        "description": plugin["description"],
        "author": catalog["owner"],
        "homepage": catalog["homepage"],
        "repository": catalog["repository"],
        "license": catalog["license"],
        "keywords": plugin["keywords"],
    }


def codex_manifest(catalog: dict, plugin: dict) -> dict:
    return {
        "name": plugin["name"],
        "version": plugin["version"],
        "description": plugin["description"],
        "author": catalog["owner"],
        "homepage": catalog["homepage"],
        "repository": catalog["repository"],
        "license": catalog["license"],
        "keywords": plugin["keywords"],
        "skills": "./skills/",
        "interface": {
            "displayName": plugin["displayName"],
            "shortDescription": plugin["shortDescription"],
            "longDescription": plugin["description"],
            "developerName": catalog["owner"]["name"],
            "category": plugin["codexCategory"],
            "capabilities": plugin["capabilities"],
            "websiteURL": catalog["homepage"],
            "defaultPrompt": plugin["defaultPrompt"],
        },
    }


def claude_marketplace(catalog: dict) -> dict:
    return {
        "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
        "name": catalog["name"],
        "owner": catalog["owner"],
        "metadata": {"description": catalog["description"]},
        "plugins": [
            {
                "name": p["name"],
                "source": f"./plugins/{p['name']}",
                "description": p["description"],
                "version": p["version"],
                "category": p["category"],
            }
            for p in catalog["plugins"]
        ],
    }


def codex_marketplace(catalog: dict) -> dict:
    return {
        "name": catalog["name"],
        "interface": {"displayName": catalog["displayName"]},
        "plugins": [
            {
                "name": p["name"],
                "source": {"source": "local", "path": f"./plugins/{p['name']}"},
                "policy": {"installation": "AVAILABLE"},
                "category": p["codexCategory"],
            }
            for p in catalog["plugins"]
        ],
    }


def manifests(catalog: dict) -> dict:
    files = {
        ".claude-plugin/marketplace.json": claude_marketplace(catalog),
        ".agents/plugins/marketplace.json": codex_marketplace(catalog),
    }
    for plugin in catalog["plugins"]:
        base = f"plugins/{plugin['name']}"
        files[f"{base}/.claude-plugin/plugin.json"] = plugin_manifest(catalog, plugin)
        files[f"{base}/.codex-plugin/plugin.json"] = codex_manifest(catalog, plugin)
    return {path: json.dumps(data, indent=2, ensure_ascii=False) + "\n" for path, data in files.items()}


def tracked_files(root: Path) -> list:
    """Files that git tracks or would add, never ignored ones. A plugin gets
    exactly these, so an untracked cache cannot fail or pass a check."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root, check=True, capture_output=True, text=True,
        ).stdout
        return sorted(line for line in out.splitlines() if line)
    except (OSError, subprocess.CalledProcessError):
        return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)


def check_skills(root: Path, catalog: dict) -> list:
    errors = []
    names = [p["name"] for p in catalog["plugins"]]
    if len(names) != len(set(names)):
        errors.append("catalog.json names a plugin twice")
    files = tracked_files(root)
    on_disk = {f.split("/")[1] for f in files if f.startswith("plugins/") and f.count("/") >= 2}
    for missing in sorted(set(names) - on_disk):
        errors.append(f"catalog.json names {missing}, but plugins/{missing}/ has no files")
    for extra in sorted(on_disk - set(names)):
        errors.append(f"plugins/{extra}/ is not in catalog.json")
    for path in files:
        if path.startswith("plugins/") and FORBIDDEN.search(path):
            errors.append(f"{path}: users must not get this file; keep it out of plugins/")
    for plugin in catalog["plugins"]:
        skills = [f for f in files if re.fullmatch(rf"plugins/{re.escape(plugin['name'])}/skills/[^/]+/SKILL\.md", f)]
        if not skills:
            errors.append(f"plugins/{plugin['name']} has no skills/<name>/SKILL.md")
        for skill in skills:
            errors.extend(check_skill(root / skill, skill))
        if len(plugin["description"]) > MAX_DESCRIPTION:
            errors.append(f"catalog.json: the {plugin['name']} description is longer than {MAX_DESCRIPTION} characters")
    return errors


def check_skill(path: Path, name: str) -> list:
    text = path.read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return [f"{name}: no YAML frontmatter between --- lines"]
    try:
        front = yaml.safe_load(match[1])
    except yaml.YAMLError as error:
        return [f"{name}: frontmatter is not valid YAML: {error}"]
    if not isinstance(front, dict):
        return [f"{name}: frontmatter is not a mapping"]
    errors = []
    directory = path.parent.name
    if front.get("name") != directory:
        errors.append(f"{name}: name is {front.get('name')!r}, but the directory is {directory!r}")
    description = front.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{name}: description must be a non-empty string")
    elif len(description) > MAX_DESCRIPTION:
        errors.append(f"{name}: description has {len(description)} characters; the limit here is {MAX_DESCRIPTION}")
    return errors


def main(argv: list) -> int:
    check = argv[1:] == ["--check"]
    if argv[1:] not in ([], ["--check"]):
        print(__doc__.rsplit("usage:", 1)[1], file=sys.stderr)
        return 2
    catalog = json.loads((ROOT / "catalog.json").read_text())
    errors = []
    for path, content in manifests(catalog).items():
        target = ROOT / path
        if check:
            if not target.exists() or target.read_text() != content:
                errors.append(f"{path} is out of date; run scripts/build.py")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    errors.extend(check_skills(ROOT, catalog))
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if not errors:
        print(f"{len(catalog['plugins'])} plugin(s): manifests {'match' if check else 'written'}, skills valid.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
