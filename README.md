# alicit skills

Agent skills from [alicit](https://alicit.ai): scoped, human-approved
credentials for AI agents. This repository is a plugin marketplace for Claude
Code and Codex, and a skill source for `npx skills`.

To install the alicit CLI and onboard, see <https://alicit.ai/install>.

## Install

**Claude Code**

```sh
claude plugin marketplace add alicit-ai/skills
claude plugin install alicit@alicit
```

In a session, the same is `/plugin marketplace add alicit-ai/skills`, then
`/plugin install alicit@alicit`.

**Codex**

```sh
codex plugin marketplace add alicit-ai/skills
codex plugin add alicit@alicit
```

**Any other agent**

```sh
npx skills add alicit-ai/skills --skill alicit
```

To pin a version, use the tag after `#`: `npx skills add
alicit-ai/skills#alicit-v1.8.1 --skill alicit`.

## Plugins

| Plugin | Skills | Version |
|---|---|---|
| `alicit` | `alicit` | the alicit CLI version it describes |

## How it works

`catalog.json` is the only file that you edit for a plugin's name, version,
description or keywords. `scripts/build.py` writes the four manifests from it:
the Claude Code and Codex marketplaces, and each plugin's Claude Code and Codex
manifest. CI fails if a manifest differs from what the catalog gives.

Each skill has one copy, under `plugins/<plugin>/skills/<skill>/`. Nothing else
in the repository copies it. Evals live in `evals/<skill>/`, outside the
plugin, so users do not get them.

### The alicit skill

The alicit skill's source is `skills/alicit` in the alicit repository, because
it changes in the same pull request as the CLI that it describes. Each alicit
release publishes it here:

```sh
scripts/sync-alicit.sh <alicit-checkout> v1.8.1
```

The script copies only the files that git tracks at that tag, moves the evals
out of the plugin, sets the plugin version to the CLI version, records the tag
and commit in `catalog.json`, and runs `scripts/build.py`. Do not edit
`plugins/alicit/skills/alicit/` here; the next sync replaces it.

### Checks

```sh
uv run --script scripts/build.py --check       # manifests match; skills are valid
uv run --with-requirements scripts/build.py python -m unittest discover -s tests
claude plugin validate .
```

`build.py` reads each `SKILL.md` frontmatter with a real YAML parser. The
`name` must equal the directory, and the `description` must be at most 900
characters. A plugin must not hold caches, compiled Python, archives or evals.
It checks only files that git tracks or would add, so an ignored cache on your
disk cannot change the result.

### Releases

After CI passes on `main`, `release.yml` tags each new `<plugin>-v<version>`
and publishes a GitHub Release with the plugin as a tarball. A version that
already has a tag is left alone.

## License

Apache-2.0. See `LICENSE`.
