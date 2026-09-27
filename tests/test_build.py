import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build", ROOT / "scripts" / "build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class BuildTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copy(ROOT / "catalog.json", self.root)
        skill = self.root / "plugins" / "alicit" / "skills" / "alicit"
        skill.mkdir(parents=True)
        self.skill = skill / "SKILL.md"
        self.skill.write_text("---\nname: alicit\ndescription: Use alicit for every credential.\n---\n# alicit\n")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.catalog = json.loads((self.root / "catalog.json").read_text())

    def errors(self):
        return build.check_skills(self.root, self.catalog)

    def test_a_valid_skill_passes(self):
        self.assertEqual(self.errors(), [])

    def test_the_committed_manifests_match_the_catalog(self):
        for path, content in build.manifests(json.loads((ROOT / "catalog.json").read_text())).items():
            self.assertEqual((ROOT / path).read_text(), content, path)

    def test_an_unquoted_colon_in_the_description_fails(self):
        # The darrengruber/skills 7913a97 bug: a plain scalar with ": " in it
        # is a mapping to YAML, and the skills CLI then skipped the skill.
        self.skill.write_text("---\nname: alicit\ndescription: Use it: always\n---\n")
        self.assertTrue(any("not valid YAML" in e for e in self.errors()))

    def test_a_name_that_differs_from_the_directory_fails(self):
        self.skill.write_text("---\nname: other\ndescription: Use alicit.\n---\n")
        self.assertTrue(any("but the directory is" in e for e in self.errors()))

    def test_a_long_description_fails(self):
        self.skill.write_text("---\nname: alicit\ndescription: " + "x" * 901 + "\n---\n")
        self.assertTrue(any("limit here is 900" in e for e in self.errors()))

    def test_an_eval_or_cache_in_a_plugin_fails(self):
        for name in ("evals/evals.json", "scripts/x.pyc"):
            path = self.skill.parent / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}")
        errors = self.errors()
        self.assertTrue(any("evals/evals.json" in e for e in errors))
        self.assertTrue(any("x.pyc" in e for e in errors))

    def test_an_ignored_cache_does_not_count(self):
        # Only files that a clone has can reach a user.
        (self.root / ".gitignore").write_text("__pycache__/\n")
        cache = self.skill.parent / "__pycache__" / "x.pyc"
        cache.parent.mkdir()
        cache.write_text("")
        self.assertEqual(self.errors(), [])

    def test_a_plugin_missing_from_the_catalog_fails(self):
        other = self.root / "plugins" / "other" / "skills" / "other"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("---\nname: other\ndescription: Other.\n---\n")
        self.assertTrue(any("plugins/other/ is not in catalog.json" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
