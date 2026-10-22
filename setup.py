#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# Configuration registry class for developer tools/agents
class AgentTarget:
    def __init__(self, name: str, path: Path, file_suffix: str = "", host_dir: Optional[Path] = None):
        self.name: str = name
        self.path: Path = path
        # Directory whose existence means the host is installed.
        self.host_dir: Path = host_dir or path.parent
        self.file_suffix: str = file_suffix


class WorkflowSetupError(Exception):
    """Custom exception raised when setup/compilation operations fail."""
    pass


class Console:
    """Helper for formatted console logging output."""
    @staticmethod
    def info(message: str) -> None:
        print(message)

    @staticmethod
    def success(action: str, target: str, detail: str = "") -> None:
        extra = f" -> {detail}" if detail else ""
        print(f"  [{action}] {target}{extra}")

    @staticmethod
    def warning(message: str) -> None:
        print(f"  [Warning] {message}")

    @staticmethod
    def error(message: str) -> None:
        print(f"  [Error] {message}", file=sys.stderr)


class AppConfig:
    """Encapsulates system configuration and active agent targets."""
    def __init__(self, home_dir: Optional[Path] = None):
        self.home: Path = home_dir or Path.home()
        self.install_dir: Path = self.home / ".local" / "share" / "agent-workflows"
        self.targets: List[AgentTarget] = [
            AgentTarget("claude", self.home / ".claude" / "skills"),
            AgentTarget("gemini", self.home / ".gemini" / "config" / "skills"),
            AgentTarget("copilot", self.home / ".copilot" / "skills"),
            AgentTarget("codex", self.home / ".agents" / "skills", host_dir=self.home / ".codex"),
        ]
        self.agent_targets: List[AgentTarget] = [
            AgentTarget("claude", self.home / ".claude" / "agents", ".md"),
            AgentTarget("gemini", self.home / ".gemini" / "config" / "agents"),
            AgentTarget("copilot", self.home / ".copilot" / "agents", ".agent.md"),
            AgentTarget("codex", self.home / ".codex" / "agents", ".toml"),
        ]


class FileSystemManager:
    """Manages files and directories (linking, copying, cleaning, parsing frontmatter)."""
    SIGNATURE_COMMENT = "<!-- Source: agent-workflows -->\n"
    MARKER_FILE = ".agent-workflows-source"

    def _is_path_in_repo(self, path: Path, repo_dir: Path) -> bool:
        """Checks whether a path is equal to or nested inside the repository directory."""
        try:
            resolved_path = path.resolve(strict=False)
            resolved_repo = repo_dir.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return False

        return resolved_path == resolved_repo or resolved_repo in resolved_path.parents

    def load_frontmatter(self, skill_md_path: Path) -> Tuple[Dict[str, str], str]:
        """Parses a SKILL.md file and extracts its frontmatter and markdown body."""
        empty_metadata: Dict[str, str] = {}
        if not skill_md_path.exists():
            return empty_metadata, ""
        
        try:
            with open(skill_md_path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as err:
            raise WorkflowSetupError(f"Failed to read skill file {skill_md_path}: {err}")
        
        lines = content.splitlines()
        if len(lines) > 0 and lines[0].strip() == "---":
            end_idx = -1
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    end_idx = i
                    break
            if end_idx != -1:
                frontmatter_lines = lines[1:end_idx]
                body_lines = lines[end_idx+1:]
                
                # Parse simple YAML key-value pairs
                metadata: Dict[str, str] = {}
                for line in frontmatter_lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        val = value.strip()
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        metadata[key.strip()] = val
                return metadata, "\n".join(body_lines)
                
        return empty_metadata, content

    def clean_target(self, target: Path) -> None:
        """Safely deletes a file, directory, or symlink at the target path."""
        try:
            if target.is_symlink() or target.is_file():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
        except OSError as err:
            raise WorkflowSetupError(f"Failed to clean target {target}: {err}")

    def link_or_copy(self, source: Path, target: Path, repo_dir: Path, is_directory: bool = False, force: bool = False) -> bool:
        """Attempts to create a symlink; falls back to copying on OS permission restrictions."""
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            raise WorkflowSetupError(f"Failed to create directory {target.parent}: {err}")
        
        if target.exists() or target.is_symlink():
            if not force and not self.is_managed_target(target, repo_dir):
                Console.warning(f"Skipped unmanaged existing target: {target}. Use --force to replace it.")
                return False
            self.clean_target(target)
            
        try:
            os.symlink(source, target, target_is_directory=is_directory)
            Console.success("Linked", target.name, str(source))
            return True
        except (OSError, PermissionError):
            # Fallback to copy (Crucial for non-developer mode Windows users)
            if is_directory:
                try:
                    shutil.copytree(source, target)
                    try:
                        (target / self.MARKER_FILE).touch()
                    except OSError as err:
                        Console.warning(f"Failed to write source signature to {target}: {err}")
                    Console.success("Copied (Fallback)", target.name, "Directory")
                    return True
                except OSError as err:
                    raise WorkflowSetupError(f"Failed to copy directory {source} to {target}: {err}")
            else:
                try:
                    content = source.read_text(encoding="utf-8")
                    if content.startswith("---\n"):
                        # Keep the frontmatter on line 1 so hosts still parse it.
                        marked = "---\n# source: agent-workflows\n" + content[len("---\n"):]
                    else:
                        marked = self.SIGNATURE_COMMENT + content
                    target.write_text(marked, encoding="utf-8")
                    Console.success("Copied (Fallback)", target.name, "File")
                    return True
                except (OSError, UnicodeDecodeError):
                    try:
                        shutil.copy2(source, target)
                        Console.success("Copied (Fallback)", target.name, "File via binary copy")
                        return True
                    except OSError as copy_err:
                        raise WorkflowSetupError(f"Failed to copy file {source} to {target}: {copy_err}")

    def is_managed_target(self, item: Path, repo_dir: Path) -> bool:
        """Determines whether a target item (symlink, file, or directory) is managed by this repository."""
        # 1. Symlink check
        if item.is_symlink():
            try:
                if self._is_path_in_repo(item.resolve(strict=False), repo_dir):
                    return True
                if not item.exists():
                    link_target = Path(os.readlink(item))
                    if not link_target.is_absolute():
                        link_target = item.parent / link_target
                    if self._is_path_in_repo(link_target, repo_dir):
                        return True
            except (OSError, RuntimeError, ValueError):
                # Broken or malformed symlink - inspect the raw target path conservatively.
                try:
                    link_target = Path(os.readlink(item))
                    if not link_target.is_absolute():
                        link_target = item.parent / link_target
                    if self._is_path_in_repo(link_target, repo_dir):
                        return True
                except (OSError, RuntimeError, ValueError):
                    pass
        # 2. Directory Copy check (contains marker file)
        elif item.is_dir():
            if (item / self.MARKER_FILE).exists():
                return True
        # 3. File Copy check (starts with signature comment or contains compiler source tag)
        elif item.is_file():
            try:
                with open(item, "r", encoding="utf-8", errors="ignore") as f:
                    first_lines = [f.readline() for _ in range(5)]
                content_sample = "".join(first_lines)
                if (self.SIGNATURE_COMMENT.strip() in content_sample or
                        "source: agent-workflows" in content_sample or
                        "<!-- Source: agent-workflows -->" in content_sample):
                    return True
            except OSError:
                pass

        return False


def load_skill_content(skill_folder: Path) -> Tuple[Dict[str, str], str]:
    """Loads a skill manifest."""
    return FileSystemManager().load_frontmatter(skill_folder / "SKILL.md")


def install_skill(
    skill_folder: Path,
    target: Path,
    repo_dir: Path,
    fs_manager: FileSystemManager,
    force: bool = False,
) -> bool:
    """Installs a skill globally."""
    if not (skill_folder / "SKILL.md").exists():
        return False
    return fs_manager.link_or_copy(skill_folder, target, repo_dir, is_directory=True, force=force)


def list_folder_names(folder: Path) -> Set[str]:
    """Returns the names of the subfolders in a repository folder."""
    try:
        return {child.name for child in folder.iterdir() if child.is_dir()}
    except OSError as err:
        raise WorkflowSetupError(f"Failed to read folder {folder}: {err}")


def toml_string(value: str, multiline: bool = False) -> str:
    """Returns a TOML basic string; multiline output parses back to exactly the input."""
    escaped: List[str] = []
    for char in value:
        if char == "\\":
            escaped.append("\\\\")
        elif char == '"':
            escaped.append('\\"')
        elif char == "\t" or (char == "\n" and multiline):
            escaped.append(char)
        elif ord(char) < 0x20 or ord(char) == 0x7F:
            escaped.append("\\n" if char == "\n" else f"\\u{ord(char):04X}")
        else:
            escaped.append(char)
    text = "".join(escaped)
    return f'"""\n{text}"""' if multiline else f'"{text}"'


def build_codex_agent_toml(name: str, metadata: Dict[str, str], body: str) -> str:
    """Builds a Codex agent TOML file from agent frontmatter and body."""
    return (
        "# source: agent-workflows\n"
        f"name = {toml_string(metadata.get('name', name))}\n"
        f"description = {toml_string(metadata.get('description', ''))}\n"
        f"developer_instructions = {toml_string(body.strip(), multiline=True)}\n"
    )


def install_codex_agent(
    agent_folder: Path,
    target: Path,
    repo_dir: Path,
    fs_manager: FileSystemManager,
    force: bool = False,
) -> bool:
    """Generates a Codex agent TOML file; it is a copy because the source marker must live in the file."""
    if target.exists() or target.is_symlink():
        if not force and not fs_manager.is_managed_target(target, repo_dir):
            Console.warning(f"Skipped unmanaged existing target: {target}. Use --force to replace it.")
            return False
        fs_manager.clean_target(target)

    metadata, body = fs_manager.load_frontmatter(agent_folder / "agent.md")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_codex_agent_toml(agent_folder.name, metadata, body), encoding="utf-8")
    except OSError as err:
        raise WorkflowSetupError(f"Failed to write Codex agent {target}: {err}")
    Console.success("Generated", target.name)
    return True


def install_agent(
    agent_folder: Path,
    target: AgentTarget,
    repo_dir: Path,
    fs_manager: FileSystemManager,
    force: bool = False,
) -> bool:
    """Installs an agent in the form the target host reads."""
    agent_md = agent_folder / "agent.md"
    if not agent_md.exists():
        return False

    name = agent_folder.name
    if target.file_suffix == ".toml":
        return install_codex_agent(agent_folder, target.path / f"{name}.toml", repo_dir, fs_manager, force=force)
    if not target.file_suffix:
        return fs_manager.link_or_copy(agent_folder, target.path / name, repo_dir, is_directory=True, force=force)
    return fs_manager.link_or_copy(agent_md, target.path / f"{name}{target.file_suffix}", repo_dir, force=force)


def sync_target_directory(
    target_path: Path,
    active_names: Set[str],
    repo_dir: Path,
    fs_manager: FileSystemManager,
    file_suffix: str = "",
    uninstall_all: bool = False,
) -> None:
    """Removes orphaned or stale rules in the target directory managed by this repository."""
    if not target_path.exists():
        return

    try:
        items = list(target_path.iterdir())
    except OSError as err:
        Console.warning(f"Failed to read target directory {target_path} for sync/cleanup: {err}")
        return

    for item in items:
        if fs_manager.is_managed_target(item, repo_dir):
            # Extract skill name from target file/folder name
            skill_name = item.name
            if file_suffix and skill_name.endswith(file_suffix):
                skill_name = skill_name[:-len(file_suffix)]

            # Remove if uninstalling or skill no longer active
            if uninstall_all or skill_name not in active_names:
                try:
                    fs_manager.clean_target(item)
                    Console.success("Cleaned Orphaned", item.name)
                except WorkflowSetupError as err:
                    Console.error(f"Failed to clean orphaned target {item.name}: {err}")


# Repo-maintainer tooling, not part of the lifecycle; installed only on request.
MAINTAINER_SKILLS = {"triage-feedback"}


def install_global(
    skills_dir: Path, config: AppConfig, fs_manager: FileSystemManager, force: bool = False, maintainer: bool = False
) -> int:
    """Installs skills and agents globally for detected agent tool folders; returns how many were skipped."""
    skipped = 0
    Console.info("Scanning active agent configurations...")
    linked_any = False
    repo_dir = skills_dir.parent.resolve()
    skill_names = list_folder_names(skills_dir)
    if not maintainer:
        skill_names -= MAINTAINER_SKILLS
    agent_names = list_folder_names(repo_dir / "agents")

    for target in config.targets:
        # Check if the parent configuration folder exists (indicates tool is active/installed)
        if target.host_dir.exists():
            Console.info(f"\nConfiguring {target.name.upper()} skills at: {target.path}")
            try:
                target.path.mkdir(parents=True, exist_ok=True)
            except OSError as err:
                raise WorkflowSetupError(f"Failed to create target directory {target.path}: {err}")
            
            if not maintainer:
                for name in sorted(MAINTAINER_SKILLS):
                    if fs_manager.is_managed_target(target.path / name, repo_dir):
                        Console.warning(f"Removed maintainer-only skill {name}; rerun with --maintainer to keep it.")

            # Sync target path to clean up any orphaned rules first!
            sync_target_directory(target.path, skill_names, repo_dir, fs_manager)
            
            for name in sorted(skill_names):
                if not install_skill(skills_dir / name, target.path / name, repo_dir, fs_manager, force=force):
                    skipped += 1
            linked_any = True

    for agent_target in config.agent_targets:
        if agent_target.path.parent.exists():
            Console.info(f"\nConfiguring {agent_target.name.upper()} agents at: {agent_target.path}")
            sync_target_directory(
                agent_target.path, agent_names, repo_dir, fs_manager, file_suffix=agent_target.file_suffix
            )
            for name in sorted(agent_names):
                if not install_agent(repo_dir / "agents" / name, agent_target, repo_dir, fs_manager, force=force):
                    skipped += 1

    if not linked_any:
        Console.info("\nNo active agent config directories (e.g. ~/.claude/skills or ~/.gemini/config/skills) were detected.")
        Console.info("Please run your agent tools at least once to initialize their default paths.")
    return skipped


def run_git(*args: str) -> None:
    """Runs a git command, raising WorkflowSetupError when it fails."""
    try:
        subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as err:
        detail = getattr(err, "stderr", "") or err
        raise WorkflowSetupError(f"git {' '.join(args)} failed: {str(detail).strip()}")


def install_ref(
    origin: str, ref: str, config: AppConfig, fs_manager: FileSystemManager, force: bool = False, maintainer: bool = False
) -> None:
    """Checks out a release tag detached in the install directory and links its skills."""
    install_dir = config.install_dir
    if (install_dir / ".git").exists():
        run_git("-C", str(install_dir), "fetch", "--force", "--tags", origin)
    else:
        install_dir.parent.mkdir(parents=True, exist_ok=True)
        run_git("clone", origin, str(install_dir))
    run_git("-C", str(install_dir), "checkout", "--detach", f"refs/tags/{ref}")
    Console.info(f"Installed {ref} at {install_dir}")
    skipped = install_global(install_dir / "skills", config, fs_manager, force=force, maintainer=maintainer)
    if skipped:
        Console.warning(f"{skipped} entries were skipped as unmanaged. Run `unlink` from your old checkout, or pass --force.")


def uninstall_global(skills_dir: Path, config: AppConfig, fs_manager: FileSystemManager) -> None:
    """Cleans up all globally linked/copied skills and agents."""
    Console.info("Cleaning global agent configurations...")
    repo_dir = skills_dir.parent.resolve()
    for target in config.targets:
        if target.path.exists():
            Console.info(f"\nCleaning {target.name.upper()} skills at: {target.path}")
            sync_target_directory(target.path, set(), repo_dir, fs_manager, uninstall_all=True)
    for agent_target in config.agent_targets:
        if agent_target.path.exists():
            Console.info(f"\nCleaning {agent_target.name.upper()} agents at: {agent_target.path}")
            sync_target_directory(
                agent_target.path, set(), repo_dir, fs_manager, file_suffix=agent_target.file_suffix, uninstall_all=True
            )


# Not compiled into project rules: it needs subagents, which Cursor and Windsurf rules lack.
PROJECT_EXCLUDED_SKILLS = {"orchestrate"}


class RuleCompiler:
    """Base class defining the interface for rule compilers."""
    def destination_path(self, skill_name: str, project_path: Path) -> Path:
        raise NotImplementedError

    def compile(self, skill_name: str, metadata: Dict[str, str], body: str, project_path: Path) -> None:
        raise NotImplementedError

    def clean(self, project_path: Path, fs_manager: FileSystemManager, active_skills: Set[str], repo_dir: Path, uninstall_all: bool = False) -> None:
        raise NotImplementedError


class CursorRuleCompiler(RuleCompiler):
    """Compiles rules into Cursor's .mdc format."""
    def destination_path(self, skill_name: str, project_path: Path) -> Path:
        return project_path / ".cursor" / "rules" / f"{skill_name}.mdc"

    def compile(self, skill_name: str, metadata: Dict[str, str], body: str, project_path: Path) -> None:
        try:
            cursor_dir = project_path / ".cursor" / "rules"
            cursor_dir.mkdir(parents=True, exist_ok=True)
            cursor_file = self.destination_path(skill_name, project_path)
            desc = metadata.get("description", f"Behavior rule for {skill_name}")
            safe_desc = desc.replace('\\', '\\\\').replace('"', '\\"')
            cursor_content = f"---\ndescription: \"{safe_desc}\"\nglobs: [\"**/*\"]\nalwaysApply: false\nsource: agent-workflows\n---\n\n{body.strip()}\n"
            with open(cursor_file, "w", encoding="utf-8") as f:
                f.write(cursor_content)
            Console.success("Cursor Rule Created", str(cursor_file.relative_to(project_path)))
        except OSError as err:
            raise WorkflowSetupError(f"Failed to write Cursor rule for {skill_name}: {err}")

    def clean(self, project_path: Path, fs_manager: FileSystemManager, active_skills: Set[str], repo_dir: Path, uninstall_all: bool = False) -> None:
        cursor_dir = project_path / ".cursor" / "rules"
        if not cursor_dir.exists():
            return
        try:
            for item in cursor_dir.iterdir():
                if fs_manager.is_managed_target(item, repo_dir):
                    skill_name = item.name[:-4]  # strip '.mdc'
                    if uninstall_all or skill_name not in active_skills:
                        fs_manager.clean_target(item)
                        Console.success("Cursor Rule Cleaned", str(item.relative_to(project_path)))
        except OSError as err:
            raise WorkflowSetupError(f"Failed to list Cursor rules directory for clean: {err}")


class WindsurfRuleCompiler(RuleCompiler):
    """Compiles rules into Windsurf's .md rule format."""
    def destination_path(self, skill_name: str, project_path: Path) -> Path:
        return project_path / ".windsurf" / "rules" / f"{skill_name}.md"

    def compile(self, skill_name: str, metadata: Dict[str, str], body: str, project_path: Path) -> None:
        try:
            windsurf_dir = project_path / ".windsurf" / "rules"
            windsurf_dir.mkdir(parents=True, exist_ok=True)
            windsurf_file = self.destination_path(skill_name, project_path)
            title = skill_name.replace('-', ' ').title()
            with open(windsurf_file, "w", encoding="utf-8") as f:
                f.write(f"<!-- Source: agent-workflows -->\n# {title}\n\n{body.strip()}\n")
            Console.success("Windsurf Rule Created", str(windsurf_file.relative_to(project_path)))
        except OSError as err:
            raise WorkflowSetupError(f"Failed to write Windsurf rule for {skill_name}: {err}")

    def clean(self, project_path: Path, fs_manager: FileSystemManager, active_skills: Set[str], repo_dir: Path, uninstall_all: bool = False) -> None:
        windsurf_dir = project_path / ".windsurf" / "rules"
        if not windsurf_dir.exists():
            return
        try:
            for item in windsurf_dir.iterdir():
                if fs_manager.is_managed_target(item, repo_dir):
                    skill_name = item.name[:-3]  # strip '.md'
                    if uninstall_all or skill_name not in active_skills:
                        fs_manager.clean_target(item)
                        Console.success("Windsurf Rule Cleaned", str(item.relative_to(project_path)))
        except OSError as err:
            raise WorkflowSetupError(f"Failed to list Windsurf rules directory for clean: {err}")


def preflight_project_compilation(
    skills_to_compile: List[Tuple[str, Dict[str, str], str]],
    compilers: List[RuleCompiler],
    project_path: Path,
    fs_manager: FileSystemManager,
    repo_dir: Path,
    force: bool = False,
) -> None:
    """Aborts before any writes when unmanaged destination collisions exist."""
    collisions: List[Path] = []
    for skill_name, _, _ in skills_to_compile:
        for compiler in compilers:
            destination = compiler.destination_path(skill_name, project_path)
            if (destination.exists() or destination.is_symlink()) and not fs_manager.is_managed_target(destination, repo_dir):
                collisions.append(destination)

    if collisions and not force:
        collision_list = ", ".join(str(path) for path in collisions)
        raise WorkflowSetupError(
            f"Refusing to overwrite unmanaged project rules: {collision_list}. Use --force to replace them."
        )


def compile_project(
    skills_dir: Path,
    project_path: Path,
    fs_manager: FileSystemManager,
    clean_only: bool = False,
    force: bool = False,
) -> None:
    """Compiles rules locally into the target project workspace for all registered compilers."""
    project_path = project_path.resolve()
    if not project_path.is_dir():
        raise WorkflowSetupError(f"Target path {project_path} is not a valid directory.")

    compilers: List[RuleCompiler] = [
        CursorRuleCompiler(),
        WindsurfRuleCompiler()
    ]

    active_skills = list_folder_names(skills_dir) - PROJECT_EXCLUDED_SKILLS - MAINTAINER_SKILLS
    repo_dir = skills_dir.parent.resolve()

    Console.info(f"Configuring project-level rules at: {project_path}")

    skills_to_compile: List[Tuple[str, Dict[str, str], str]] = []
    try:
        for skill_folder in skills_dir.iterdir():
            if skill_folder.is_dir() and skill_folder.name in active_skills:
                skill_md = skill_folder / "SKILL.md"
                if not skill_md.exists():
                    continue
                metadata, body = load_skill_content(skill_folder)
                # Rules are single files, so inline the skill's reference docs.
                for extra in sorted(skill_folder.glob("*.md")):
                    if extra.name != "SKILL.md":
                        body += "\n\n" + extra.read_text(encoding="utf-8")
                skills_to_compile.append((skill_folder.name, metadata, body))
    except OSError as err:
        raise WorkflowSetupError(f"Failed to list skills during compilation: {err}")

    if not clean_only:
        preflight_project_compilation(skills_to_compile, compilers, project_path, fs_manager, repo_dir, force=force)

    # Synchronize/clean managed rules only after preflight passes
    for compiler in compilers:
        compiler.clean(project_path, fs_manager, active_skills, repo_dir, uninstall_all=clean_only)

    if clean_only:
        return

    for skill_name, metadata, body in skills_to_compile:
        for compiler in compilers:
            destination = compiler.destination_path(skill_name, project_path)
            if (destination.exists() or destination.is_symlink()) and not fs_manager.is_managed_target(destination, repo_dir):
                fs_manager.clean_target(destination)
            compiler.compile(skill_name, metadata, body, project_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared Agent Skills Repository installer script.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Link command
    link_parser = subparsers.add_parser("link", help="Link skills globally to active agent config directories.")
    link_parser.add_argument("--force", action="store_true", help="Replace existing unmanaged target files or directories.")
    link_parser.add_argument("--maintainer", action="store_true", help="Also install maintainer-only skills.")

    # Install command
    install_parser = subparsers.add_parser("install", help="Check out a release tag and link its skills globally.")
    install_parser.add_argument("--ref", required=True, help="Release tag to install.")
    install_parser.add_argument("--force", action="store_true", help="Replace existing unmanaged target files or directories.")
    install_parser.add_argument("--maintainer", action="store_true", help="Also install maintainer-only skills.")

    # Unlink command
    subparsers.add_parser("unlink", help="Unlink global skills from agent config directories.")

    # Project command
    proj_parser = subparsers.add_parser("project", help="Link/Compile skills locally for Cursor and Windsurf in a project.")
    proj_parser.add_argument("--path", default=".", help="Path to the local project workspace root (defaults to current directory).")
    proj_parser.add_argument("--clean", action="store_true", help="Remove all compiled rules in the project workspace.")
    proj_parser.add_argument("--force", action="store_true", help="Replace existing unmanaged project rule files.")

    args = parser.parse_args()

    repo_dir = Path(__file__).parent.resolve()
    skills_dir = repo_dir / "skills"

    if not skills_dir.exists() or not skills_dir.is_dir():
        Console.error(f"skills directory not found at {skills_dir}")
        sys.exit(1)

    config = AppConfig()
    fs_manager = FileSystemManager()

    try:
        if args.command == "link":
            install_global(skills_dir, config, fs_manager, force=args.force, maintainer=args.maintainer)
        elif args.command == "install":
            origin = subprocess.run(
                ["git", "-C", str(repo_dir), "remote", "get-url", "origin"], capture_output=True, text=True
            ).stdout.strip()
            if not origin:
                raise WorkflowSetupError("No origin remote found in this checkout.")
            install_ref(origin, args.ref, config, fs_manager, force=args.force, maintainer=args.maintainer)
        elif args.command == "unlink":
            uninstall_global(skills_dir, config, fs_manager)
        elif args.command == "project":
            compile_project(skills_dir, Path(args.path), fs_manager, clean_only=args.clean, force=args.force)
    except WorkflowSetupError as err:
        Console.error(str(err))
        sys.exit(1)


if __name__ == "__main__":
    main()
