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
                self.assertFalse(set(meta) - SPEC_KEYS, "non-spec keys")
                self.assertEqual(meta.get("name"), path.parent.name)
                self.assertLessEqual(len(meta["name"]), 64)
                description = meta.get("description", "")
                self.assertTrue(description)
                self.assertLessEqual(len(description), 1024)


if __name__ == "__main__":
    unittest.main()
