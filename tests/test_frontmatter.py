import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import setup

# Agent Skills spec keys.
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


class SkillFrontmatterTest(unittest.TestCase):
    def test_every_skill_frontmatter_matches_spec(self):
        fs = setup.FileSystemManager()
        skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertTrue(skill_files)
        for path in skill_files:
            with self.subTest(skill=path.parent.name):
                meta, _ = fs.load_frontmatter(path)
                self.assertEqual(set(meta) - SPEC_KEYS, set(), "non-spec keys")
                self.assertEqual(meta.get("name"), path.parent.name)
                self.assertLessEqual(len(meta["name"]), 64)
                description = meta.get("description", "")
                self.assertTrue(description)
                self.assertLessEqual(len(description), 1024)


class AgentFrontmatterTest(unittest.TestCase):
    def test_light_agent_is_orchestrate_step_on_sonnet(self):
        fs = setup.FileSystemManager()
        loaded = {}
        for name in ("orchestrate-step", "orchestrate-step-light"):
            meta, body = fs.load_frontmatter(ROOT / "agents" / name / "agent.md")
            self.assertEqual(meta.get("name"), name)
            loaded[name] = (meta, body)
        self.assertEqual(loaded["orchestrate-step"][1], loaded["orchestrate-step-light"][1])
        self.assertNotIn("model", loaded["orchestrate-step"][0])
        self.assertEqual(loaded["orchestrate-step-light"][0].get("model"), "sonnet")


class OrchestrateCoreBudgetTest(unittest.TestCase):
    def test_orchestrate_skill_fits_reattach_budget(self):
        # Compaction re-attaches only a skill's first 5,000 tokens; about 1.72 tokens per word here.
        text = (ROOT / "skills" / "orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.split()), 2700)


if __name__ == "__main__":
    unittest.main()
