#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# Configuration registry class for developer tools/agents
class AgentTarget:
    def __init__(self, name: str, path: Path, is_directory_based: bool, file_suffix: str = ""):
        self.name: str = name
        self.path: Path = path
        self.is_directory_based: bool = is_directory_based
        self.file_suffix: str = file_suffix


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

    def load_frontmatter(self, skill_md_path: Path) -> Tuple[Dict[str, str], str]:
        """Parses a SKILL.md file and extracts its frontmatter and markdown body."""
        empty_metadata: Dict[str, str] = {}
        if not skill_md_path.exists():
            return empty_metadata, ""
        
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        
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
                        metadata[key.strip()] = value.strip()
                return metadata, "\n".join(body_lines)
                
        return empty_metadata, content

    def clean_target(self, target: Path) -> None:
        """Safely deletes a file, directory, or symlink at the target path."""
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)

    def link_or_copy(self, source: Path, target: Path, is_directory: bool = False) -> None:
        """Attempts to create a symlink; falls back to copying on OS permission restrictions."""
        target.parent.mkdir(parents=True, exist_ok=True)
        
        if target.exists() or target.is_symlink():
            self.clean_target(target)
            
        try:
            os.symlink(source, target, target_is_directory=is_directory)
            print(f"  [Linked] {target.name} -> {source}")
        except (OSError, PermissionError):
            # Fallback to copy (Crucial for non-developer mode Windows users)
            if is_directory:
                try:
                    shutil.copytree(source, target)
                    try:
                        (target / self.MARKER_FILE).touch()
                    except OSError as err:
                        print(f"  [Warning] Failed to write source signature to {target}: {err}")
                    print(f"  [Copied (Fallback)] {target.name} (Directory)")
                except OSError as err:
                    print(f"  [Error] Failed to copy directory {source} to {target}: {err}")
            else:
                try:
                    content = source.read_text(encoding="utf-8")
                    target.write_text(self.SIGNATURE_COMMENT + content, encoding="utf-8")
                    print(f"  [Copied (Fallback)] {target.name} (File)")
                except (OSError, UnicodeDecodeError):
                    try:
                        shutil.copy2(source, target)
                        print(f"  [Copied (Fallback)] {target.name} (File via binary copy)")
                    except OSError as copy_err:
                        print(f"  [Error] Failed to copy file {source} to {target}: {copy_err}")

    def is_managed_target(self, item: Path, repo_dir: Path) -> bool:
        """Determines whether a target item (symlink, file, or directory) is managed by this repository."""
        # 1. Symlink check
        if item.is_symlink():
            try:
                resolved = item.resolve()
                if repo_dir in resolved.parents or resolved == repo_dir:
                    return True
            except (OSError, ValueError):
                # Broken symlink - check if link target text contains "agent-workflows"
                try:
                    link_target = os.readlink(item)
                    if "agent-workflows" in link_target:
                        return True
                except OSError:
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


def sync_target_directory(skills_dir: Path, target_path: Path, fs_manager: FileSystemManager, file_suffix: str = "", uninstall_all: bool = False) -> None:
    """Removes orphaned or stale rules in the target directory managed by this repository."""
    if not target_path.exists():
        return

    # Get active skills in repository
    active_skills = {folder.name for folder in skills_dir.iterdir() if folder.is_dir()}
    repo_dir = skills_dir.parent.resolve()

    for item in target_path.iterdir():
        if fs_manager.is_managed_target(item, repo_dir):
            # Extract skill name from target file/folder name
            skill_name = item.name
            if file_suffix and skill_name.endswith(file_suffix):
                skill_name = skill_name[:-len(file_suffix)]

            # Remove if uninstalling or skill no longer active
            if uninstall_all or skill_name not in active_skills:
                try:
                    fs_manager.clean_target(item)
                    print(f"  [Cleaned Orphaned] {item.name}")
                except OSError as err:
                    print(f"  [Error] Failed to clean orphaned target {item.name}: {err}")


def install_global(skills_dir: Path, config: AppConfig, fs_manager: FileSystemManager) -> None:
    """Installs skills globally for detected agent tool folders."""
    print("Scanning active agent configurations...")
    linked_any = False

    for target in config.targets:
        # Check if the parent configuration folder exists (indicates tool is active/installed)
        parent_config = target.path.parent
        if parent_config.exists():
            print(f"\nConfiguring {target.name.upper()} skills at: {target.path}")
            target.path.mkdir(parents=True, exist_ok=True)
            
            # Sync target path to clean up any orphaned rules first!
            sync_target_directory(skills_dir, target.path, fs_manager, file_suffix=target.file_suffix, uninstall_all=False)
            
            for skill_folder in skills_dir.iterdir():
                if skill_folder.is_dir():
                    if target.is_directory_based:
                        # Directory-based linking
                        fs_manager.link_or_copy(skill_folder, target.path / skill_folder.name, is_directory=True)
                    else:
                        # Flat file-based linking with custom suffix
                        skill_file = skill_folder / "SKILL.md"
                        if skill_file.exists():
                            fs_manager.link_or_copy(skill_file, target.path / f"{skill_folder.name}{target.file_suffix}", is_directory=False)
            linked_any = True

    if not linked_any:
        print("\nNo active agent config directories (e.g. ~/.claude or ~/.gemini/antigravity) were detected.")
        print("Please run your agent tools at least once to initialize their default paths.")


def uninstall_global(skills_dir: Path, config: AppConfig, fs_manager: FileSystemManager) -> None:
    """Cleans up all globally linked/copied skills."""
    print("Cleaning global agent configurations...")
    for target in config.targets:
        if target.path.exists():
            print(f"\nCleaning {target.name.upper()} skills at: {target.path}")
            sync_target_directory(skills_dir, target.path, fs_manager, file_suffix=target.file_suffix, uninstall_all=True)
class RuleCompiler:
    """Base class defining the interface for rule compilers."""
    def compile(self, skill_name: str, metadata: Dict[str, str], body: str, project_path: Path) -> None:
        raise NotImplementedError

    def clean(self, project_path: Path, fs_manager: FileSystemManager, active_skills: Set[str], repo_dir: Path, uninstall_all: bool = False) -> None:
        raise NotImplementedError


class CursorRuleCompiler(RuleCompiler):
    """Compiles rules into Cursor's .mdc format."""
    def compile(self, skill_name: str, metadata: Dict[str, str], body: str, project_path: Path) -> None:
        cursor_dir = project_path / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        cursor_file = cursor_dir / f"{skill_name}.mdc"
        desc = metadata.get("description", f"Behavior rule for {skill_name}")
        cursor_content = f"---\ndescription: {desc}\nglobs: [\"**/*\"]\nalwaysApply: false\nsource: agent-workflows\n---\n\n{body.strip()}\n"
        with open(cursor_file, "w", encoding="utf-8") as f:
            f.write(cursor_content)
        print(f"  [Cursor Rule Created] {cursor_file.relative_to(project_path)}")

    def clean(self, project_path: Path, fs_manager: FileSystemManager, active_skills: Set[str], repo_dir: Path, uninstall_all: bool = False) -> None:
        cursor_dir = project_path / ".cursor" / "rules"
        if not cursor_dir.exists():
            return
        for item in cursor_dir.iterdir():
            if fs_manager.is_managed_target(item, repo_dir):
                skill_name = item.name[:-4]  # strip '.mdc'
                if uninstall_all or skill_name not in active_skills:
                    try:
                        fs_manager.clean_target(item)
                        print(f"  [Cursor Rule Cleaned] {item.relative_to(project_path)}")
                    except OSError as err:
                        print(f"  [Error] Failed to clean Cursor rule {item.name}: {err}")


class WindsurfRuleCompiler(RuleCompiler):
    """Compiles rules into Windsurf's .md rule format."""
    def compile(self, skill_name: str, metadata: Dict[str, str], body: str, project_path: Path) -> None:
        windsurf_dir = project_path / ".windsurf" / "rules"
        windsurf_dir.mkdir(parents=True, exist_ok=True)
        windsurf_file = windsurf_dir / f"{skill_name}.md"
        title = skill_name.replace('-', ' ').title()
        with open(windsurf_file, "w", encoding="utf-8") as f:
            f.write(f"<!-- Source: agent-workflows -->\n# {title}\n\n{body.strip()}\n")
        print(f"  [Windsurf Rule Created] {windsurf_file.relative_to(project_path)}")

    def clean(self, project_path: Path, fs_manager: FileSystemManager, active_skills: Set[str], repo_dir: Path, uninstall_all: bool = False) -> None:
        windsurf_dir = project_path / ".windsurf" / "rules"
        if not windsurf_dir.exists():
            return
        for item in windsurf_dir.iterdir():
            if fs_manager.is_managed_target(item, repo_dir):
                skill_name = item.name[:-3]  # strip '.md'
                if uninstall_all or skill_name not in active_skills:
                    try:
                        fs_manager.clean_target(item)
                        print(f"  [Windsurf Rule Cleaned] {item.relative_to(project_path)}")
                    except OSError as err:
                        print(f"  [Error] Failed to clean Windsurf rule {item.name}: {err}")


def compile_project(skills_dir: Path, project_path: Path, fs_manager: FileSystemManager, clean_only: bool = False) -> None:
    """Compiles rules locally into the target project workspace for all registered compilers."""
    project_path = project_path.resolve()
    if not project_path.is_dir():
        print(f"Error: Target path {project_path} is not a valid directory.")
        sys.exit(1)

    compilers: List[RuleCompiler] = [
        CursorRuleCompiler(),
        WindsurfRuleCompiler()
    ]

    repo_dir = skills_dir.parent.resolve()
    active_skills = {folder.name for folder in skills_dir.iterdir() if folder.is_dir()}

    print(f"Configuring project-level rules at: {project_path}")

    # Synchronize/clean rules first
    for compiler in compilers:
        compiler.clean(project_path, fs_manager, active_skills, repo_dir, uninstall_all=clean_only)

    if clean_only:
        return

    # Process all skills
    for skill_folder in skills_dir.iterdir():
        if skill_folder.is_dir():
            skill_md = skill_folder / "SKILL.md"
            if not skill_md.exists():
                continue

            metadata, body = fs_manager.load_frontmatter(skill_md)
            for compiler in compilers:
                compiler.compile(skill_folder.name, metadata, body, project_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared Agent Skills Repository installer script.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Link command
    subparsers.add_parser("link", help="Link skills globally to active agent config directories.")

    # Unlink command
    subparsers.add_parser("unlink", help="Unlink global skills from agent config directories.")

    # Project command
    proj_parser = subparsers.add_parser("project", help="Link/Compile skills locally for Cursor and Windsurf in a project.")
    proj_parser.add_argument("--path", default=".", help="Path to the local project workspace root (defaults to current directory).")
    proj_parser.add_argument("--clean", action="store_true", help="Remove all compiled rules in the project workspace.")

    args = parser.parse_args()

    repo_dir = Path(__file__).parent.resolve()
    skills_dir = repo_dir / "skills"

    if not skills_dir.exists() or not skills_dir.is_dir():
        print(f"Error: skills directory not found at {skills_dir}")
        sys.exit(1)

    config = AppConfig()
    fs_manager = FileSystemManager()

    if args.command == "link":
        install_global(skills_dir, config, fs_manager)
    elif args.command == "unlink":
        uninstall_global(skills_dir, config, fs_manager)
    elif args.command == "project":
        compile_project(skills_dir, Path(args.path), fs_manager, clean_only=args.clean)


if __name__ == "__main__":
    main()
