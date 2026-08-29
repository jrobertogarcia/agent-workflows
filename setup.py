#!/usr/bin/env python3
import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

INCLUDE_PATTERN = re.compile(r"<!--\s*include:\s*([^\s]+?)\s*-->")

# Configuration registry class for developer tools/agents
class AgentTarget:
    def __init__(self, name: str, path: Path, is_directory_based: bool, file_suffix: str = ""):
        self.name: str = name
        self.path: Path = path
        self.is_directory_based: bool = is_directory_based
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
        self.targets: List[AgentTarget] = [
            AgentTarget("claude", self.home / ".claude" / "skills", is_directory_based=True),
            AgentTarget("gemini", self.home / ".gemini" / "config" / "skills", is_directory_based=True),
            AgentTarget("copilot", self.home / ".copilot" / "agents", is_directory_based=False, file_suffix=".agent.md"),
            AgentTarget("codex", self.home / ".codex" / "skills", is_directory_based=True),
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
                    target.write_text(self.SIGNATURE_COMMENT + content, encoding="utf-8")
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


def has_includes(body: str) -> bool:
    """Returns True when the skill body contains include directives."""
    return INCLUDE_PATTERN.search(body) is not None


def resolve_include_path(include_path: str, repo_dir: Path) -> Path:
    """Resolves an include path to an absolute path within the repository."""
    candidate = Path(include_path)
    if candidate.is_absolute():
        raise WorkflowSetupError(f"Include path must be relative to the repository: {include_path}")

    resolved = (repo_dir / candidate).resolve()
    repo_resolved = repo_dir.resolve()
    if resolved != repo_resolved and repo_resolved not in resolved.parents:
        raise WorkflowSetupError(f"Include path escapes repository: {include_path}")

    return resolved


def expand_includes(body: str, repo_dir: Path, _seen: Optional[Set[str]] = None) -> str:
    """Expands include directives into the skill body."""
    seen = set(_seen or [])

    def replace_match(match: re.Match[str]) -> str:
        include_path = match.group(1).strip()
        resolved = resolve_include_path(include_path, repo_dir)
        normalized = str(resolved)

        if normalized in seen:
            raise WorkflowSetupError(f"Circular include detected: {include_path}")

        if not resolved.is_file():
            raise WorkflowSetupError(f"Missing include file: {include_path}")

        try:
            included_content = resolved.read_text(encoding="utf-8")
        except OSError as err:
            raise WorkflowSetupError(f"Failed to read include file {include_path}: {err}")

        return expand_includes(included_content, repo_dir, seen | {normalized})

    return INCLUDE_PATTERN.sub(replace_match, body)


def build_skill_md(metadata: Dict[str, str], body: str) -> str:
    """Builds a SKILL.md file from metadata and body."""
    frontmatter_lines = ["---"]
    for key, value in metadata.items():
        frontmatter_lines.append(f"{key}: {value}")
    frontmatter_lines.append("---")
    return "\n".join(frontmatter_lines) + "\n\n" + body.strip() + "\n"


def load_skill_content(skill_folder: Path, repo_dir: Path) -> Tuple[Dict[str, str], str]:
    """Loads and expands a skill manifest."""
    skill_md = skill_folder / "SKILL.md"
    metadata, body = FileSystemManager().load_frontmatter(skill_md)
    if has_includes(body):
        body = expand_includes(body, repo_dir)
    return metadata, body


def materialize_skill_directory(
    skill_folder: Path,
    target: Path,
    metadata: Dict[str, str],
    expanded_body: str,
    repo_dir: Path,
    fs_manager: FileSystemManager,
    force: bool = False,
) -> bool:
    """Copies a skill directory with an expanded SKILL.md for include-based skills."""
    if target.exists() or target.is_symlink():
        if not force and not fs_manager.is_managed_target(target, repo_dir):
            Console.warning(f"Skipped unmanaged existing target: {target}. Use --force to replace it.")
            return False
        fs_manager.clean_target(target)

    try:
        shutil.copytree(skill_folder, target)
        (target / fs_manager.MARKER_FILE).touch()
        (target / "SKILL.md").write_text(build_skill_md(metadata, expanded_body), encoding="utf-8")
        Console.success("Materialized", target.name, "Directory with expanded includes")
        return True
    except OSError as err:
        raise WorkflowSetupError(f"Failed to materialize skill directory {skill_folder.name}: {err}")


def materialize_skill_file(
    target: Path,
    metadata: Dict[str, str],
    expanded_body: str,
    repo_dir: Path,
    fs_manager: FileSystemManager,
    force: bool = False,
) -> bool:
    """Writes a flat skill file with expanded includes for Copilot-style targets."""
    if target.exists() or target.is_symlink():
        if not force and not fs_manager.is_managed_target(target, repo_dir):
            Console.warning(f"Skipped unmanaged existing target: {target}. Use --force to replace it.")
            return False
        fs_manager.clean_target(target)

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        content = fs_manager.SIGNATURE_COMMENT + build_skill_md(metadata, expanded_body)
        target.write_text(content, encoding="utf-8")
        Console.success("Materialized", target.name, "File with expanded includes")
        return True
    except OSError as err:
        raise WorkflowSetupError(f"Failed to materialize skill file {target.name}: {err}")


def install_skill(
    skill_folder: Path,
    target: Path,
    repo_dir: Path,
    fs_manager: FileSystemManager,
    is_directory: bool = False,
    force: bool = False,
) -> bool:
    """Installs a skill globally, materializing when includes must be expanded."""
    skill_md = skill_folder / "SKILL.md"
    if not skill_md.exists():
        return False

    metadata, body = fs_manager.load_frontmatter(skill_md)
    if has_includes(body):
        expanded_body = expand_includes(body, repo_dir)
        if is_directory:
            return materialize_skill_directory(
                skill_folder, target, metadata, expanded_body, repo_dir, fs_manager, force=force
            )
        return materialize_skill_file(target, metadata, expanded_body, repo_dir, fs_manager, force=force)

    return fs_manager.link_or_copy(skill_folder if is_directory else skill_md, target, repo_dir, is_directory=is_directory, force=force)


def sync_target_directory(skills_dir: Path, target_path: Path, fs_manager: FileSystemManager, file_suffix: str = "", uninstall_all: bool = False) -> None:
    """Removes orphaned or stale rules in the target directory managed by this repository."""
    if not target_path.exists():
        return

    # Get active skills in repository
    try:
        active_skills = {folder.name for folder in skills_dir.iterdir() if folder.is_dir()}
    except OSError as err:
        raise WorkflowSetupError(f"Failed to read skills folder {skills_dir}: {err}")
        
    repo_dir = skills_dir.parent.resolve()

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
            if uninstall_all or skill_name not in active_skills:
                try:
                    fs_manager.clean_target(item)
                    Console.success("Cleaned Orphaned", item.name)
                except WorkflowSetupError as err:
                    Console.error(f"Failed to clean orphaned target {item.name}: {err}")


def install_global(skills_dir: Path, config: AppConfig, fs_manager: FileSystemManager, force: bool = False) -> None:
    """Installs skills globally for detected agent tool folders."""
    Console.info("Scanning active agent configurations...")
    linked_any = False
    repo_dir = skills_dir.parent.resolve()

    for target in config.targets:
        # Check if the parent configuration folder exists (indicates tool is active/installed)
        parent_config = target.path.parent
        if parent_config.exists():
            Console.info(f"\nConfiguring {target.name.upper()} skills at: {target.path}")
            try:
                target.path.mkdir(parents=True, exist_ok=True)
            except OSError as err:
                raise WorkflowSetupError(f"Failed to create target directory {target.path}: {err}")
            
            # Sync target path to clean up any orphaned rules first!
            sync_target_directory(skills_dir, target.path, fs_manager, file_suffix=target.file_suffix, uninstall_all=False)
            
            try:
                for skill_folder in skills_dir.iterdir():
                    if skill_folder.is_dir():
                        if target.is_directory_based:
                            install_skill(
                                skill_folder,
                                target.path / skill_folder.name,
                                repo_dir,
                                fs_manager,
                                is_directory=True,
                                force=force,
                            )
                        else:
                            install_skill(
                                skill_folder,
                                target.path / f"{skill_folder.name}{target.file_suffix}",
                                repo_dir,
                                fs_manager,
                                is_directory=False,
                                force=force,
                            )
            except OSError as err:
                raise WorkflowSetupError(f"Failed to read skills folder during installation: {err}")
            linked_any = True

    if not linked_any:
        Console.info("\nNo active agent config directories (e.g. ~/.claude/skills or ~/.gemini/config/skills) were detected.")
        Console.info("Please run your agent tools at least once to initialize their default paths.")


def uninstall_global(skills_dir: Path, config: AppConfig, fs_manager: FileSystemManager) -> None:
    """Cleans up all globally linked/copied skills."""
    Console.info("Cleaning global agent configurations...")
    for target in config.targets:
        if target.path.exists():
            Console.info(f"\nCleaning {target.name.upper()} skills at: {target.path}")
            sync_target_directory(skills_dir, target.path, fs_manager, file_suffix=target.file_suffix, uninstall_all=True)


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

    try:
        active_skills = {folder.name for folder in skills_dir.iterdir() if folder.is_dir()}
    except OSError as err:
        raise WorkflowSetupError(f"Failed to read skills directory: {err}")
        
    repo_dir = skills_dir.parent.resolve()

    Console.info(f"Configuring project-level rules at: {project_path}")

    skills_to_compile: List[Tuple[str, Dict[str, str], str]] = []
    try:
        for skill_folder in skills_dir.iterdir():
            if skill_folder.is_dir():
                skill_md = skill_folder / "SKILL.md"
                if not skill_md.exists():
                    continue
                metadata, body = load_skill_content(skill_folder, repo_dir)
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
            install_global(skills_dir, config, fs_manager, force=args.force)
        elif args.command == "unlink":
            uninstall_global(skills_dir, config, fs_manager)
        elif args.command == "project":
            compile_project(skills_dir, Path(args.path), fs_manager, clean_only=args.clean, force=args.force)
    except WorkflowSetupError as err:
        Console.error(str(err))
        sys.exit(1)


if __name__ == "__main__":
    main()
