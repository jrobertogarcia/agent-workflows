import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import setup


class SetupTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo_dir = self.root / "agent-workflows"
        self.skills_dir = self.repo_dir / "skills"
        self.skills_dir.mkdir(parents=True)
        self.fs = setup.FileSystemManager()

    def add_skill(self, name, description="Test skill"):
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nBody text\n",
            encoding="utf-8",
        )
        return skill_dir

    def add_skills(self, count=17):
        return [self.add_skill(f"skill-{index:02d}") for index in range(count)]

    def capture_stdout(self, func, *args, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = func(*args, **kwargs)
        return result, output.getvalue()

    def run_quiet(self, func, *args, **kwargs):
        return self.capture_stdout(func, *args, **kwargs)[0]

    def can_create_directory_symlink(self):
        source = self.root / "symlink-probe-source"
        target = self.root / "symlink-probe-target"
        source.mkdir(exist_ok=True)
        try:
            os.symlink(source, target, target_is_directory=True)
            return target.is_symlink()
        except (OSError, NotImplementedError):
            return False
        finally:
            try:
                if target.is_symlink() or target.exists():
                    target.unlink()
            except OSError:
                pass

    def requires_symlink_support(self):
        if not self.can_create_directory_symlink():
            self.skipTest("OS/user permissions do not allow creating directory symlinks")

    def assert_same_path(self, left, right):
        self.assertEqual(os.path.realpath(left), os.path.realpath(right))


class FrontmatterTests(SetupTestCase):
    def test_load_frontmatter_parses_metadata_and_body(self):
        skill = self.add_skill("gather-context", "Context Discovery Phase")

        metadata, body = self.fs.load_frontmatter(skill / "SKILL.md")

        self.assertEqual(metadata["name"], "gather-context")
        self.assertEqual(metadata["description"], "Context Discovery Phase")
        self.assertNotIn("---", body)
        self.assertIn("# gather-context", body)

    def test_load_frontmatter_handles_missing_file(self):
        metadata, body = self.fs.load_frontmatter(self.skills_dir / "missing" / "SKILL.md")

        self.assertEqual(metadata, {})
        self.assertEqual(body, "")


class ManagedTargetTests(SetupTestCase):
    def test_symlink_into_repo_is_managed(self):
        self.requires_symlink_support()
        source = self.add_skill("managed-skill")
        target = self.root / "target"
        os.symlink(source, target, target_is_directory=True)

        self.assertTrue(self.fs.is_managed_target(target, self.repo_dir))

    def test_broken_symlink_inside_repo_is_managed(self):
        self.requires_symlink_support()
        target = self.root / "broken-link"
        os.symlink(self.repo_dir / "missing", target)

        self.assertTrue(self.fs.is_managed_target(target, self.repo_dir))

    def test_relative_broken_symlink_inside_repo_is_managed(self):
        self.requires_symlink_support()
        target = self.root / "relative-broken-link"
        os.symlink(Path("agent-workflows") / "missing", target)

        self.assertTrue(self.fs.is_managed_target(target, self.repo_dir))

    def test_broken_symlink_with_agent_workflows_name_outside_repo_is_unmanaged(self):
        self.requires_symlink_support()
        target = self.root / "lookalike-broken-link"
        os.symlink(self.root / "my-agent-workflows-notes" / "missing", target)

        self.assertFalse(self.fs.is_managed_target(target, self.repo_dir))

    def test_directory_marker_is_managed(self):
        target = self.root / "copied-skill"
        target.mkdir()
        (target / setup.FileSystemManager.MARKER_FILE).touch()

        self.assertTrue(self.fs.is_managed_target(target, self.repo_dir))

    def test_source_signature_file_is_managed(self):
        target = self.root / "skill.agent.md"
        target.write_text(setup.FileSystemManager.SIGNATURE_COMMENT + "body", encoding="utf-8")

        self.assertTrue(self.fs.is_managed_target(target, self.repo_dir))

    def test_compiler_source_tag_file_is_managed(self):
        target = self.root / "skill.mdc"
        target.write_text("---\nsource: agent-workflows\n---\n", encoding="utf-8")

        self.assertTrue(self.fs.is_managed_target(target, self.repo_dir))

    def test_ordinary_user_targets_are_unmanaged(self):
        user_file = self.root / "user.md"
        user_file.write_text("user-owned", encoding="utf-8")
        user_dir = self.root / "user-dir"
        user_dir.mkdir()

        self.assertFalse(self.fs.is_managed_target(user_file, self.repo_dir))
        self.assertFalse(self.fs.is_managed_target(user_dir, self.repo_dir))


class LinkOrCopyTests(SetupTestCase):
    def test_new_target_is_linked_successfully(self):
        self.requires_symlink_support()
        source = self.add_skill("new-target")
        target = self.root / "target"

        installed = self.run_quiet(self.fs.link_or_copy, source, target, self.repo_dir, is_directory=True)

        self.assertTrue(installed)
        self.assertTrue(target.is_symlink())
        self.assert_same_path(target.resolve(), source)

    def test_existing_managed_target_is_replaced(self):
        self.requires_symlink_support()
        old_source = self.add_skill("old-source")
        new_source = self.add_skill("new-source")
        target = self.root / "target"
        os.symlink(old_source, target, target_is_directory=True)

        installed = self.run_quiet(self.fs.link_or_copy, new_source, target, self.repo_dir, is_directory=True)

        self.assertTrue(installed)
        self.assertTrue(target.is_symlink())
        self.assert_same_path(target.resolve(), new_source)

    def test_existing_unmanaged_target_is_skipped_by_default(self):
        source = self.add_skill("source")
        target = self.root / "target"
        target.mkdir()
        (target / "README.md").write_text("user-owned", encoding="utf-8")

        installed, output = self.capture_stdout(
            self.fs.link_or_copy,
            source,
            target,
            self.repo_dir,
            is_directory=True,
        )

        self.assertFalse(installed)
        self.assertIn("Skipped unmanaged existing target", output)
        self.assertTrue((target / "README.md").exists())
        self.assertFalse(target.is_symlink())

    def test_force_replaces_unmanaged_target(self):
        self.requires_symlink_support()
        source = self.add_skill("source")
        target = self.root / "target"
        target.mkdir()
        (target / "README.md").write_text("user-owned", encoding="utf-8")

        installed = self.run_quiet(self.fs.link_or_copy, source, target, self.repo_dir, is_directory=True, force=True)

        self.assertTrue(installed)
        self.assertTrue(target.is_symlink())
        self.assert_same_path(target.resolve(), source)

    def test_symlink_failure_falls_back_to_directory_copy_with_marker(self):
        source = self.add_skill("copy-source")
        target = self.root / "copied-target"

        with mock.patch("setup.os.symlink", side_effect=OSError("no symlink")):
            installed = self.run_quiet(self.fs.link_or_copy, source, target, self.repo_dir, is_directory=True)

        self.assertTrue(installed)
        self.assertTrue(target.is_dir())
        self.assertTrue((target / setup.FileSystemManager.MARKER_FILE).exists())
        self.assertTrue((target / "SKILL.md").exists())

    def test_symlink_failure_falls_back_to_file_copy_with_signature(self):
        source_dir = self.add_skill("file-source")
        source = source_dir / "SKILL.md"
        target = self.root / "file-source.agent.md"

        with mock.patch("setup.os.symlink", side_effect=OSError("no symlink")):
            installed = self.run_quiet(self.fs.link_or_copy, source, target, self.repo_dir)

        self.assertTrue(installed)
        self.assertTrue(target.is_file())
        self.assertTrue(target.read_text(encoding="utf-8").startswith(setup.FileSystemManager.SIGNATURE_COMMENT))


class GlobalInstallTests(SetupTestCase):
    def make_config(self):
        return setup.AppConfig(home_dir=self.root / "home")

    def test_install_global_only_configures_detected_parent_directories(self):
        self.add_skills()
        config = self.make_config()
        (config.home / ".codex").mkdir(parents=True)

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)

        self.assertTrue((config.home / ".codex" / "skills").exists())
        self.assertFalse((config.home / ".claude" / "skills").exists())
        self.assertFalse((config.home / ".copilot" / "agents").exists())

    def test_install_and_uninstall_global_codex_targets(self):
        self.requires_symlink_support()
        self.add_skills()
        config = self.make_config()
        (config.home / ".codex").mkdir(parents=True)

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)
        installed = list((config.home / ".codex" / "skills").iterdir())
        installed_are_symlinks = [item.is_symlink() for item in installed]
        self.run_quiet(setup.uninstall_global, self.skills_dir, config, self.fs)
        remaining = list((config.home / ".codex" / "skills").iterdir())

        self.assertEqual(len(installed), 17)
        self.assertTrue(all(installed_are_symlinks))
        self.assertEqual(remaining, [])

    def test_global_install_skips_unmanaged_collision_and_installs_others(self):
        self.add_skills()
        config = self.make_config()
        codex_skills = config.home / ".codex" / "skills"
        codex_skills.mkdir(parents=True)
        collision = codex_skills / "skill-00"
        collision.mkdir()
        (collision / "README.md").write_text("user-owned", encoding="utf-8")

        _, output = self.capture_stdout(setup.install_global, self.skills_dir, config, self.fs)

        installed = [
            item
            for item in codex_skills.iterdir()
            if item.name != "skill-00" and self.fs.is_managed_target(item, self.repo_dir)
        ]
        self.assertIn("Skipped unmanaged existing target", output)
        self.assertTrue((collision / "README.md").exists())
        self.assertEqual(len(installed), 16)

    def test_global_install_symlink_failure_falls_back_to_copied_skills(self):
        self.add_skills()
        config = self.make_config()
        codex_skills = config.home / ".codex" / "skills"
        codex_skills.mkdir(parents=True)

        with mock.patch("setup.os.symlink", side_effect=OSError("no symlink")):
            self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)

        installed = list(codex_skills.iterdir())
        self.assertEqual(len(installed), 17)
        self.assertTrue(all(item.is_dir() for item in installed))
        self.assertTrue(all((item / setup.FileSystemManager.MARKER_FILE).exists() for item in installed))

    def test_global_install_force_replaces_unmanaged_collision(self):
        self.requires_symlink_support()
        self.add_skills()
        config = self.make_config()
        codex_skills = config.home / ".codex" / "skills"
        codex_skills.mkdir(parents=True)
        collision = codex_skills / "skill-00"
        collision.mkdir()
        (collision / "README.md").write_text("user-owned", encoding="utf-8")

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs, force=True)

        installed = list(codex_skills.iterdir())
        self.assertEqual(len(installed), 17)
        self.assertTrue((codex_skills / "skill-00").is_symlink())

    def test_uninstall_global_preserves_unmanaged_files(self):
        self.add_skills()
        config = self.make_config()
        codex_skills = config.home / ".codex" / "skills"
        codex_skills.mkdir(parents=True)
        unmanaged = codex_skills / "user-skill"
        unmanaged.mkdir()
        (unmanaged / "README.md").write_text("user-owned", encoding="utf-8")

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)
        self.run_quiet(setup.uninstall_global, self.skills_dir, config, self.fs)

        self.assertTrue((unmanaged / "README.md").exists())
        self.assertEqual(list(codex_skills.iterdir()), [unmanaged])


class ProjectCompilationTests(SetupTestCase):
    def test_compile_project_creates_cursor_and_windsurf_rules(self):
        self.add_skills()
        project = self.root / "project"
        project.mkdir()

        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs)

        cursor_rules = sorted((project / ".cursor" / "rules").glob("*.mdc"))
        windsurf_rules = sorted((project / ".windsurf" / "rules").glob("*.md"))
        cursor_content = (project / ".cursor" / "rules" / "skill-00.mdc").read_text(encoding="utf-8")
        windsurf_content = (project / ".windsurf" / "rules" / "skill-00.md").read_text(encoding="utf-8")

        self.assertEqual(len(cursor_rules), 17)
        self.assertEqual(len(windsurf_rules), 17)
        self.assertIn('description: "Test skill"', cursor_content)
        self.assertIn('globs: ["**/*"]', cursor_content)
        self.assertIn("alwaysApply: false", cursor_content)
        self.assertIn("source: agent-workflows", cursor_content)
        self.assertTrue(windsurf_content.startswith("<!-- Source: agent-workflows -->"))
        self.assertIn("# Skill 00", windsurf_content)

    def test_compile_project_clean_removes_managed_rules(self):
        self.add_skills()
        project = self.root / "project"
        project.mkdir()

        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs)
        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs, clean_only=True)

        self.assertEqual(list((project / ".cursor" / "rules").iterdir()), [])
        self.assertEqual(list((project / ".windsurf" / "rules").iterdir()), [])

    def test_compile_project_clean_preserves_unmanaged_rules(self):
        self.add_skills()
        project = self.root / "project"
        cursor_dir = project / ".cursor" / "rules"
        windsurf_dir = project / ".windsurf" / "rules"
        cursor_dir.mkdir(parents=True)
        windsurf_dir.mkdir(parents=True)
        cursor_user_file = cursor_dir / "user.mdc"
        windsurf_user_file = windsurf_dir / "user.md"
        cursor_user_file.write_text("user-owned", encoding="utf-8")
        windsurf_user_file.write_text("user-owned", encoding="utf-8")

        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs, clean_only=True)

        self.assertTrue(cursor_user_file.exists())
        self.assertTrue(windsurf_user_file.exists())

    def test_compile_project_aborts_on_unmanaged_collision_without_changes(self):
        self.add_skill("skill-00")
        project = self.root / "project"
        cursor_dir = project / ".cursor" / "rules"
        windsurf_dir = project / ".windsurf" / "rules"
        cursor_dir.mkdir(parents=True)
        windsurf_dir.mkdir(parents=True)
        cursor_collision = cursor_dir / "skill-00.mdc"
        windsurf_collision = windsurf_dir / "skill-00.md"
        cursor_collision.write_text("user-owned", encoding="utf-8")
        windsurf_collision.write_text("user-owned", encoding="utf-8")

        with self.assertRaises(setup.WorkflowSetupError):
            setup.compile_project(self.skills_dir, project, self.fs)

        self.assertEqual(cursor_collision.read_text(encoding="utf-8"), "user-owned")
        self.assertEqual(windsurf_collision.read_text(encoding="utf-8"), "user-owned")

    def test_compile_project_force_replaces_unmanaged_collision(self):
        self.add_skill("skill-00")
        project = self.root / "project"
        cursor_dir = project / ".cursor" / "rules"
        windsurf_dir = project / ".windsurf" / "rules"
        cursor_dir.mkdir(parents=True)
        windsurf_dir.mkdir(parents=True)
        cursor_collision = cursor_dir / "skill-00.mdc"
        windsurf_collision = windsurf_dir / "skill-00.md"
        cursor_collision.write_text("user-owned", encoding="utf-8")
        windsurf_collision.write_text("user-owned", encoding="utf-8")

        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs, force=True)

        cursor_content = cursor_collision.read_text(encoding="utf-8")
        windsurf_content = windsurf_collision.read_text(encoding="utf-8")
        self.assertIn("source: agent-workflows", cursor_content)
        self.assertTrue(windsurf_content.startswith("<!-- Source: agent-workflows -->"))
        self.assertNotIn("user-owned", cursor_content)
        self.assertNotIn("user-owned", windsurf_content)

    def test_compile_project_refreshes_managed_rules(self):
        self.add_skill("skill-00", "Original description")
        project = self.root / "project"
        project.mkdir()

        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs)
        cursor_file = project / ".cursor" / "rules" / "skill-00.mdc"
        self.assertIn('description: "Original description"', cursor_file.read_text(encoding="utf-8"))

        skill_file = self.skills_dir / "skill-00" / "SKILL.md"
        skill_file.write_text(
            "---\nname: skill-00\ndescription: Updated description\n---\n\n# skill-00\n\nUpdated body\n",
            encoding="utf-8",
        )

        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs)
        updated_content = cursor_file.read_text(encoding="utf-8")
        self.assertIn('description: "Updated description"', updated_content)
        self.assertIn("Updated body", updated_content)


class IncludeExpansionTests(SetupTestCase):
    def add_shared_fragment(self, relative_path, content):
        fragment = self.repo_dir / relative_path
        fragment.parent.mkdir(parents=True, exist_ok=True)
        fragment.write_text(content, encoding="utf-8")
        return fragment

    def add_skill_with_include(self, name, include_path, description="Included skill"):
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n"
            f"<!-- include: {include_path} -->\n",
            encoding="utf-8",
        )
        return skill_dir

    def test_expand_includes_renders_shared_fragment(self):
        self.add_shared_fragment("shared/review-guidelines.md", "Shared review rubric\n")
        skill = self.add_skill_with_include("review-branch", "shared/review-guidelines.md")

        _, body = load_skill_content(skill, self.repo_dir)
        self.assertIn("Shared review rubric", body)
        self.assertNotIn("<!-- include:", body)

    def test_expand_includes_rejects_missing_file(self):
        skill = self.add_skill_with_include("review-branch", "shared/missing.md")

        with self.assertRaises(setup.WorkflowSetupError):
            load_skill_content(skill, self.repo_dir)

    def test_expand_includes_rejects_repo_escape(self):
        skill = self.add_skill_with_include("review-branch", "../outside.md")

        with self.assertRaises(setup.WorkflowSetupError):
            load_skill_content(skill, self.repo_dir)

    def test_compile_project_expands_review_skills(self):
        self.add_shared_fragment("shared/review-guidelines.md", "Shared review rubric\n")
        self.add_skill_with_include("review-branch", "shared/review-guidelines.md")
        self.add_skill_with_include("review-pr", "shared/review-guidelines.md")
        project = self.root / "project"
        project.mkdir()

        self.run_quiet(setup.compile_project, self.skills_dir, project, self.fs)

        branch_content = (project / ".cursor" / "rules" / "review-branch.mdc").read_text(encoding="utf-8")
        pr_content = (project / ".cursor" / "rules" / "review-pr.mdc").read_text(encoding="utf-8")
        self.assertIn("Shared review rubric", branch_content)
        self.assertIn("Shared review rubric", pr_content)
        self.assertIn("# review-branch", branch_content)
        self.assertIn("# review-pr", pr_content)
        self.assertNotIn("<!-- include:", branch_content)
        self.assertNotIn("<!-- include:", pr_content)

    def test_install_global_materializes_directory_skill_with_includes(self):
        self.add_shared_fragment("shared/review-guidelines.md", "Shared review rubric\n")
        self.add_skill_with_include("review-branch", "shared/review-guidelines.md")
        config = setup.AppConfig(home_dir=self.root / "home")
        (config.home / ".codex").mkdir(parents=True)

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)

        installed = config.home / ".codex" / "skills" / "review-branch"
        content = (installed / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue((installed / setup.FileSystemManager.MARKER_FILE).exists())
        self.assertIn("Shared review rubric", content)
        self.assertNotIn("<!-- include:", content)

    def test_install_global_materializes_flat_file_skill_with_includes(self):
        self.add_shared_fragment("shared/review-guidelines.md", "Shared review rubric\n")
        self.add_skill_with_include("review-pr", "shared/review-guidelines.md")
        config = setup.AppConfig(home_dir=self.root / "home")
        (config.home / ".copilot").mkdir(parents=True)

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)

        installed = config.home / ".copilot" / "agents" / "review-pr.agent.md"
        content = installed.read_text(encoding="utf-8")
        self.assertTrue(content.startswith(setup.FileSystemManager.SIGNATURE_COMMENT))
        self.assertIn("Shared review rubric", content)
        self.assertNotIn("<!-- include:", content)


def load_skill_content(skill_folder, repo_dir):
    return setup.load_skill_content(skill_folder, repo_dir)


class OrphanCleanupTests(SetupTestCase):
    def test_sync_target_directory_removes_orphaned_managed_targets_only(self):
        self.requires_symlink_support()
        active_skill = self.add_skill("active")
        target_dir = self.root / "target"
        target_dir.mkdir()
        active_target = target_dir / "active"
        orphan_target = target_dir / "orphan"
        unmanaged_target = target_dir / "user"
        os.symlink(active_skill, active_target, target_is_directory=True)
        orphan_target.mkdir()
        (orphan_target / setup.FileSystemManager.MARKER_FILE).touch()
        unmanaged_target.mkdir()
        (unmanaged_target / "README.md").write_text("user-owned", encoding="utf-8")

        self.run_quiet(setup.sync_target_directory, self.skills_dir, target_dir, self.fs)

        self.assertTrue(active_target.exists())
        self.assertFalse(orphan_target.exists())
        self.assertTrue((unmanaged_target / "README.md").exists())

    def test_sync_target_directory_handles_copilot_suffix(self):
        self.add_skill("active")
        target_dir = self.root / "copilot"
        target_dir.mkdir()
        active_file = target_dir / "active.agent.md"
        orphan_file = target_dir / "orphan.agent.md"
        active_file.write_text(setup.FileSystemManager.SIGNATURE_COMMENT + "active", encoding="utf-8")
        orphan_file.write_text(setup.FileSystemManager.SIGNATURE_COMMENT + "orphan", encoding="utf-8")

        self.run_quiet(setup.sync_target_directory, self.skills_dir, target_dir, self.fs, file_suffix=".agent.md")

        self.assertTrue(active_file.exists())
        self.assertFalse(orphan_file.exists())


class HandoverConventionTests(unittest.TestCase):
    def test_handover_path_convention_is_identical_in_producer_and_consumer(self):
        skills = Path(setup.__file__).resolve().parent / "skills"
        producer = (skills / "prepare-handover" / "SKILL.md").read_text(encoding="utf-8")
        consumer = (skills / "review-branch" / "SKILL.md").read_text(encoding="utf-8")

        path_literal = "~/.agent-workflows/<repo>/<branch>/handover.md"
        repo_expression = "basename(dirname(git rev-parse --path-format=absolute --git-common-dir))"
        branch_expression = "git branch --show-current"
        tip_label = "Branch tip:"

        self.assertIn(path_literal, producer)
        self.assertIn(path_literal, consumer)
        self.assertIn(repo_expression, producer)
        self.assertIn(repo_expression, consumer)
        self.assertIn(branch_expression, producer)
        self.assertIn(branch_expression, consumer)
        self.assertIn(tip_label, producer)
        self.assertIn(tip_label, consumer)


if __name__ == "__main__":
    unittest.main()
