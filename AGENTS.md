# Agent rules for alicit-ai/skills

This repository is a public plugin marketplace. Everything in it ships to
users.

- Edit plugin names, versions, descriptions and keywords only in
  `catalog.json`. Then run `python3 scripts/build.py`. Never edit a generated
  manifest by hand.
- Do not edit `plugins/alicit/skills/alicit/`. Change `skills/alicit` in
  `alicit-ai/alicit`, and publish it with `scripts/sync-alicit.sh` at a release
  tag.
- A new skill goes in `plugins/<plugin>/skills/<skill>/SKILL.md`, with its
  plugin in `catalog.json`. Keep one copy. Put its evals in `evals/<skill>/`.
- Never commit a secret, a token, an internal hostname, or an absolute path
  from your machine. In a skill, refer to its own files with a relative path.
- Before you push, run `python3 scripts/build.py --check`,
  `python3 -m unittest discover -s tests` and `claude plugin validate .`.
- Use Conventional Commits for commit messages.
