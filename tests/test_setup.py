import contextlib
import io
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

import setup


class SetupTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo_dir = self.root / "agent-workflows"
        self.skills_dir = self.repo_dir / "skills"
        self.skills_dir.mkdir(parents=True)
        self.agents_dir = self.repo_dir / "agents"
        self.agents_dir.mkdir()
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

    def add_agent(self, name="orchestrate-step", description="Test agent", body="# Agent\n\nBody text\n"):
        agent_dir = self.agents_dir / name
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n{body}",
            encoding="utf-8",
        )
        return agent_dir

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
        plain_source = self.root / "plain.md"
        plain_source.write_text("# Plain\n", encoding="utf-8")
        plain_target = self.root / "plain-copy.md"

        with mock.patch("setup.os.symlink", side_effect=OSError("no symlink")):
            installed = self.run_quiet(self.fs.link_or_copy, source, target, self.repo_dir)
            plain_installed = self.run_quiet(self.fs.link_or_copy, plain_source, plain_target, self.repo_dir)

        self.assertTrue(installed)
        lines = target.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "---")
        self.assertIn("source: agent-workflows", lines[1])
        self.assertTrue(self.fs.is_managed_target(target, self.repo_dir))
        self.assertTrue(plain_installed)
        self.assertTrue(plain_target.read_text(encoding="utf-8").startswith(setup.FileSystemManager.SIGNATURE_COMMENT))


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
        self.assertFalse((config.home / ".copilot" / "skills").exists())

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

    def make_copilot_home(self):
        config = self.make_config()
        (config.home / ".copilot").mkdir(parents=True)
        return config

    def add_legacy_copilot_agent_files(self, config):
        """Creates a managed signature file, a managed symlink (when supported) and a user-owned agent file."""
        agents = config.home / ".copilot" / "agents"
        agents.mkdir(parents=True)
        managed = [agents / "skill-00.agent.md"]
        managed[0].write_text(setup.FileSystemManager.SIGNATURE_COMMENT + "legacy", encoding="utf-8")
        if self.can_create_directory_symlink():
            managed.append(agents / "skill-01.agent.md")
            os.symlink(self.skills_dir / "skill-01" / "SKILL.md", managed[1])
        unmanaged = agents / "mine.agent.md"
        unmanaged.write_text("user-owned", encoding="utf-8")
        return managed, unmanaged

    def test_install_global_copilot_installs_skill_directories(self):
        self.add_skills()
        config = self.make_copilot_home()

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)

        installed = list((config.home / ".copilot" / "skills").iterdir())
        self.assertEqual(len(installed), 17)
        self.assertTrue(all(self.fs.is_managed_target(item, self.repo_dir) for item in installed))
        self.assertFalse((config.home / ".copilot" / "agents").exists())

    def test_link_removes_legacy_managed_copilot_agent_files_and_preserves_unmanaged(self):
        self.add_skills()
        config = self.make_copilot_home()
        managed, unmanaged = self.add_legacy_copilot_agent_files(config)

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)

        self.assertFalse(any(item.exists() or item.is_symlink() for item in managed))
        self.assertEqual(unmanaged.read_text(encoding="utf-8"), "user-owned")

    def test_unlink_removes_legacy_managed_copilot_agent_files_and_preserves_unmanaged(self):
        self.add_skills()
        config = self.make_copilot_home()
        managed, unmanaged = self.add_legacy_copilot_agent_files(config)

        self.run_quiet(setup.uninstall_global, self.skills_dir, config, self.fs)

        self.assertFalse(any(item.exists() or item.is_symlink() for item in managed))
        self.assertEqual(unmanaged.read_text(encoding="utf-8"), "user-owned")

    def test_link_and_unlink_preserve_unmanaged_copilot_skill_directory(self):
        self.add_skills()
        config = self.make_copilot_home()
        user_skill = config.home / ".copilot" / "skills" / "gh-stack"
        user_skill.mkdir(parents=True)
        (user_skill / "SKILL.md").write_text("user-owned", encoding="utf-8")

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)
        self.assertEqual((user_skill / "SKILL.md").read_text(encoding="utf-8"), "user-owned")
        self.run_quiet(setup.uninstall_global, self.skills_dir, config, self.fs)

        self.assertEqual((user_skill / "SKILL.md").read_text(encoding="utf-8"), "user-owned")
        self.assertEqual(list((config.home / ".copilot" / "skills").iterdir()), [user_skill])

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


class AgentInstallTests(SetupTestCase):
    HOST_PARENTS = {
        "claude": (".claude",),
        "gemini": (".gemini", "config"),
        "copilot": (".copilot",),
        "codex": (".codex",),
    }

    def make_home(self, hosts=None, home_name="home"):
        config = setup.AppConfig(home_dir=self.root / home_name)
        for host in hosts or self.HOST_PARENTS:
            parent = config.home.joinpath(*self.HOST_PARENTS[host])
            parent.mkdir(parents=True)
        return config

    def agent_dir(self, config, host):
        return next(target.path for target in config.agent_targets if target.name == host)

    def agent_path(self, config, host):
        agent_target = next(target for target in config.agent_targets if target.name == host)
        return agent_target.path / f"orchestrate-step{agent_target.file_suffix}"

    def link(self, config, **kwargs):
        return self.capture_stdout(setup.install_global, self.skills_dir, config, self.fs, **kwargs)[1]

    def unlink(self, config):
        self.run_quiet(setup.uninstall_global, self.skills_dir, config, self.fs)

    def test_link_installs_agent_only_for_detected_hosts(self):
        self.requires_symlink_support()
        self.add_skills()
        self.add_agent()
        for host in self.HOST_PARENTS:
            with self.subTest(host=host):
                config = self.make_home([host], home_name=f"home-{host}")

                self.link(config)

                installed = self.agent_path(config, host)
                self.assertTrue(installed.exists())
                self.assertTrue(self.fs.is_managed_target(installed, self.repo_dir))
                if host == "gemini":
                    self.assertTrue((installed / "agent.md").is_file())
                for other in self.HOST_PARENTS:
                    if other != host:
                        self.assertFalse(self.agent_dir(config, other).exists())

    def test_relink_keeps_agent_in_every_dir(self):
        self.requires_symlink_support()
        self.add_skills()
        self.add_agent()
        config = self.make_home()
        legacy_dir = self.agent_dir(config, "copilot")
        legacy_dir.mkdir()
        legacy = legacy_dir / "skill-00.agent.md"
        legacy.write_text(setup.FileSystemManager.SIGNATURE_COMMENT + "legacy", encoding="utf-8")

        self.link(config)
        self.link(config)

        for host in self.HOST_PARENTS:
            with self.subTest(host=host):
                installed = self.agent_path(config, host)
                self.assertTrue(installed.exists())
                self.assertTrue(self.fs.is_managed_target(installed, self.repo_dir))
        self.assertTrue((legacy_dir / "orchestrate-step.agent.md").exists())
        self.assertFalse(legacy.exists())

    def test_unlink_removes_agent_from_every_dir(self):
        self.requires_symlink_support()
        self.add_skills()
        self.add_agent()
        config = self.make_home()

        self.link(config)
        self.unlink(config)

        for host in self.HOST_PARENTS:
            with self.subTest(host=host):
                remaining = [
                    item
                    for item in self.agent_dir(config, host).iterdir()
                    if self.fs.is_managed_target(item, self.repo_dir)
                ]
                self.assertEqual(remaining, [])

    def test_link_and_unlink_preserve_unmanaged_agent_files(self):
        self.requires_symlink_support()
        self.add_skills()
        self.add_agent()
        config = self.make_home()
        user_files = [
            self.agent_dir(config, "claude") / "mine.md",
            self.agent_dir(config, "copilot") / "mine.agent.md",
            self.agent_dir(config, "codex") / "mine.toml",
            self.agent_dir(config, "gemini") / "mine" / "agent.md",
        ]
        for user_file in user_files:
            user_file.parent.mkdir(parents=True)
            user_file.write_text("user-owned", encoding="utf-8")

        self.link(config)
        for user_file in user_files:
            self.assertEqual(user_file.read_text(encoding="utf-8"), "user-owned")
        self.unlink(config)

        for user_file in user_files:
            self.assertEqual(user_file.read_text(encoding="utf-8"), "user-owned")

    @unittest.skipIf(tomllib is None, "tomllib requires Python 3.11+")
    def test_codex_agent_toml_parses_with_three_keys_and_marker(self):
        self.add_skills()
        self.add_agent(description="Run one step", body="# Agent\n\nBody text\n")
        config = self.make_home(["codex"])

        self.link(config)

        installed = self.agent_path(config, "codex")
        parsed = tomllib.loads(installed.read_text(encoding="utf-8"))
        self.assertEqual(set(parsed), {"name", "description", "developer_instructions"})
        self.assertEqual(parsed["name"], "orchestrate-step")
        self.assertEqual(parsed["description"], "Run one step")
        self.assertEqual(parsed["developer_instructions"], "# Agent\n\nBody text")
        self.assertIn("# source: agent-workflows", installed.read_text(encoding="utf-8").splitlines()[:5])
        self.assertTrue(self.fs.is_managed_target(installed, self.repo_dir))

    @unittest.skipIf(tomllib is None, "tomllib requires Python 3.11+")
    def test_codex_agent_toml_round_trips_hostile_text(self):
        description = 'He said "hi" and used \\'
        bodies = [
            '"""\n\'\'\'\n\\\nliteral \\n here\nC:\\path\\\ttab\x01\x7f caf\u00e9 \u2603\nends with a quote"',
            "ends with a backslash \\",
        ]
        for body in bodies:
            with self.subTest(body=body):
                text = setup.build_codex_agent_toml("agent", {"description": description}, body)

                parsed = tomllib.loads(text)

                self.assertEqual(parsed["name"], "agent")
                self.assertEqual(parsed["description"], description)
                self.assertEqual(parsed["developer_instructions"], body.strip())

    def test_unmanaged_agent_collision_skipped_without_force(self):
        self.add_skills()
        self.add_agent()
        config = self.make_home(["claude", "codex"])
        collisions = [self.agent_path(config, "claude"), self.agent_path(config, "codex")]
        for collision in collisions:
            collision.parent.mkdir(parents=True)
            collision.write_text("user-owned", encoding="utf-8")

        output = self.link(config)

        self.assertIn("Skipped unmanaged existing target", output)
        for collision in collisions:
            self.assertEqual(collision.read_text(encoding="utf-8"), "user-owned")

    def test_force_replaces_unmanaged_agent_collision(self):
        self.requires_symlink_support()
        self.add_skills()
        agent_dir = self.add_agent()
        config = self.make_home(["claude", "codex"])
        collisions = [self.agent_path(config, "claude"), self.agent_path(config, "codex")]
        for collision in collisions:
            collision.parent.mkdir(parents=True)
            collision.write_text("user-owned", encoding="utf-8")

        self.link(config, force=True)

        claude_agent, codex_agent = collisions
        self.assertTrue(claude_agent.is_symlink())
        self.assert_same_path(claude_agent.resolve(), agent_dir / "agent.md")
        self.assertTrue(self.fs.is_managed_target(codex_agent, self.repo_dir))
        if tomllib is not None:
            self.assertEqual(tomllib.loads(codex_agent.read_text(encoding="utf-8"))["name"], "orchestrate-step")

    def test_symlink_failure_copies_agents_with_markers(self):
        self.add_skills()
        self.add_agent(description="Run one step")
        config = self.make_home(["claude", "gemini", "copilot"])

        with mock.patch("setup.os.symlink", side_effect=OSError("no symlink")):
            self.link(config)
            self.link(config)

        for host in ("claude", "copilot"):
            with self.subTest(host=host):
                installed = self.agent_path(config, host)
                content = installed.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"))
                self.assertIn("description: Run one step", content)
                self.assertTrue(self.fs.is_managed_target(installed, self.repo_dir))
        gemini_agent = self.agent_path(config, "gemini")
        self.assertTrue(gemini_agent.is_dir())
        self.assertTrue((gemini_agent / setup.FileSystemManager.MARKER_FILE).exists())

        self.unlink(config)

        for host in ("claude", "gemini", "copilot"):
            self.assertEqual(list(self.agent_dir(config, host).iterdir()), [])


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

    def test_install_global_materializes_copilot_skill_directory_with_includes(self):
        self.add_shared_fragment("shared/review-guidelines.md", "Shared review rubric\n")
        self.add_skill_with_include("review-pr", "shared/review-guidelines.md")
        config = setup.AppConfig(home_dir=self.root / "home")
        (config.home / ".copilot").mkdir(parents=True)

        self.run_quiet(setup.install_global, self.skills_dir, config, self.fs)

        installed = config.home / ".copilot" / "skills" / "review-pr"
        content = (installed / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue((installed / setup.FileSystemManager.MARKER_FILE).exists())
        self.assertIn("Shared review rubric", content)
        self.assertNotIn("<!-- include:", content)
        self.assertFalse((config.home / ".copilot" / "agents").exists())


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

        self.run_quiet(setup.sync_target_directory, target_dir, {"active"}, self.repo_dir, self.fs)

        self.assertTrue(active_target.exists())
        self.assertFalse(orphan_target.exists())
        self.assertTrue((unmanaged_target / "README.md").exists())

    def test_sync_target_directory_uses_explicit_names_not_skills_folder(self):
        self.add_skill("active")
        self.add_skill("orphan")
        target_dir = self.root / "target"
        target_dir.mkdir()
        for name in ("active", "orphan"):
            (target_dir / name).mkdir()
            (target_dir / name / setup.FileSystemManager.MARKER_FILE).touch()

        self.run_quiet(setup.sync_target_directory, target_dir, {"active"}, self.repo_dir, self.fs)

        self.assertTrue((target_dir / "active").exists())
        self.assertFalse((target_dir / "orphan").exists())

    def test_sync_target_directory_strips_suffix_against_explicit_names(self):
        self.add_skill("active")
        target_dir = self.root / "copilot"
        target_dir.mkdir()
        active_file = target_dir / "active.agent.md"
        orphan_file = target_dir / "orphan.agent.md"
        active_file.write_text(setup.FileSystemManager.SIGNATURE_COMMENT + "active", encoding="utf-8")
        orphan_file.write_text(setup.FileSystemManager.SIGNATURE_COMMENT + "orphan", encoding="utf-8")

        self.run_quiet(setup.sync_target_directory, target_dir, {"active"}, self.repo_dir, self.fs, file_suffix=".agent.md")

        self.assertTrue(active_file.exists())
        self.assertFalse(orphan_file.exists())


class RegistryDescriptionSyncTests(unittest.TestCase):
    """AGENTS.md declares frontmatter `description` authoritative; these guard the mirrors of it."""

    AGENTS_ROW = re.compile(r"^\|\s*\*\*`([a-z0-9-]+)`\*\*\s*\|[^|]*\|\s*(.+?)\s*\|[^|]*\|\s*$")
    BULLET = re.compile(r"^\*\s+\*\*`([a-z0-9-]+)`\*\*:\s*(.+?)\s*$")
    STATED_COUNT = re.compile(r"the (\d+) core skills")

    def setUp(self):
        self.repo = Path(setup.__file__).resolve().parent

    def read_text(self, filename):
        return (self.repo / filename).read_text(encoding="utf-8")

    def read_lines(self, filename):
        return self.read_text(filename).splitlines()

    def frontmatter_descriptions(self):
        fs = setup.FileSystemManager()
        descriptions = {}
        for skill_dir in sorted((self.repo / "skills").iterdir()):
            if skill_dir.is_dir():
                metadata, _ = fs.load_frontmatter(skill_dir / "SKILL.md")
                descriptions[skill_dir.name] = metadata.get("description")
        return descriptions

    def matched_descriptions(self, filename, pattern):
        matches = (pattern.match(line) for line in self.read_lines(filename))
        return {match.group(1): match.group(2) for match in matches if match}

    def assert_mirror_matches(self, mirror, mirrored, expected):
        """Compares one skill per subTest so a failure names the skill and prints both strings."""
        for name, description in expected.items():
            with self.subTest(skill=name, mirror=mirror):
                self.assertEqual(mirrored[name], description)

    def test_frontmatter_description_matches_agents_table_and_readme_index(self):
        frontmatter = self.frontmatter_descriptions()
        agents = self.matched_descriptions("AGENTS.md", self.AGENTS_ROW)
        readme = self.matched_descriptions("README.md", self.BULLET)

        self.assertEqual(sorted(agents), sorted(frontmatter))
        self.assertEqual(sorted(readme), sorted(frontmatter))
        self.assert_mirror_matches("AGENTS.md", agents, frontmatter)
        self.assert_mirror_matches("README.md", readme, frontmatter)

    def test_lifecycle_describes_every_skill_by_bullet_or_by_name(self):
        frontmatter = self.frontmatter_descriptions()
        lifecycle = self.matched_descriptions("LIFECYCLE.md", self.BULLET)
        prose = self.read_text("LIFECYCLE.md")

        self.assertEqual([name for name in lifecycle if name not in frontmatter], [])
        self.assert_mirror_matches("LIFECYCLE.md", lifecycle, {name: frontmatter[name] for name in lifecycle})
        # Skills carried by narrative prose rather than a bullet count either emphasis form.
        unbulleted = sorted(set(frontmatter) - set(lifecycle))
        self.assertEqual([name for name in unbulleted if f"`{name}`" not in prose], [])

    def test_agents_registry_states_the_actual_skill_count(self):
        skill_count = len(self.frontmatter_descriptions())
        stated = [int(match.group(1)) for match in self.STATED_COUNT.finditer(self.read_text("AGENTS.md"))]

        self.assertEqual(stated, [skill_count])
if __name__ == "__main__":
    unittest.main()

