#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Dict, Tuple

# Target paths for global tools
HOME = Path.home()
TARGETS = {
    "claude": HOME / ".claude" / "skills",
    "gemini": HOME / ".gemini" / "config" / "skills",
    "copilot": HOME / ".copilot" / "agents",
    "codex": HOME / ".codex" / "skills",
}

def load_frontmatter(skill_md_path: Path) -> Tuple[Dict[str, str], str]:
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

def clean_target(target: Path) -> None:
    """Safely deletes a file, directory, or symlink at the target path."""
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

def link_or_copy(source: Path, target: Path, is_directory: bool = False) -> None:
    """Attempts to create a symlink; falls back to copying on OS permission restrictions."""
    target.parent.mkdir(parents=True, exist_ok=True)
    
    if target.exists() or target.is_symlink():
        clean_target(target)
        
    try:
        os.symlink(source, target, target_is_directory=is_directory)
        print(f"  [Linked] {target.name} -> {source}")
    except (OSError, PermissionError):
        # Fallback to copy (Crucial for non-developer mode Windows users)
        if is_directory:
            try:
                shutil.copytree(source, target)
                try:
                    (target / ".agent-workflows-source").touch()
                except OSError as err:
                    print(f"  [Warning] Failed to write source signature to {target}: {err}")
                print(f"  [Copied (Fallback)] {target.name} (Directory)")
            except OSError as err:
                print(f"  [Error] Failed to copy directory {source} to {target}: {err}")
        else:
            try:
                signature = "<!-- Source: agent-workflows -->\n"
                content = source.read_text(encoding="utf-8")
                target.write_text(signature + content, encoding="utf-8")
                print(f"  [Copied (Fallback)] {target.name} (File)")
            except (OSError, UnicodeDecodeError):
                try:
                    shutil.copy2(source, target)
                    print(f"  [Copied (Fallback)] {target.name} (File via binary copy)")
                except OSError as copy_err:
                    print(f"  [Error] Failed to copy file {source} to {target}: {copy_err}")

def _is_managed_target(item: Path, repo_dir: Path) -> bool:
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
        if (item / ".agent-workflows-source").exists():
            return True
    # 3. File Copy check (starts with signature comment)
    elif item.is_file():
        try:
            with open(item, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline()
            if "<!-- Source: agent-workflows -->" in first_line:
                return True
        except OSError:
            pass

    return False

def sync_target_directory(skills_dir: Path, target_path: Path, uninstall_all: bool = False) -> None:
    """Removes orphaned or stale rules in the target directory managed by this repository."""
    if not target_path.exists():
        return

    # Get active skills in repository
    active_skills = {folder.name for folder in skills_dir.iterdir() if folder.is_dir()}
    repo_dir = skills_dir.parent.resolve()
    copilot_suffix = ".agent.md"

    for item in target_path.iterdir():
        if _is_managed_target(item, repo_dir):
            # Extract skill name from target file/folder name
            skill_name = item.name
            if skill_name.endswith(copilot_suffix):
                skill_name = skill_name[:-len(copilot_suffix)]

            # Remove if uninstalling or skill no longer active
            if uninstall_all or skill_name not in active_skills:
                try:
                    clean_target(item)
                    print(f"  [Cleaned Orphaned] {item.name}")
                except OSError as err:
                    print(f"  [Error] Failed to clean orphaned target {item.name}: {err}")

def install_global(skills_dir: Path) -> None:
    """Installs skills globally for detected agent tool folders."""
    print("Scanning active agent configurations...")
    linked_any = False

    for tool, target_path in TARGETS.items():
        # Check if the parent configuration folder exists (indicates tool is active/installed)
        parent_config = target_path.parent
        if parent_config.exists():
            print(f"\nConfiguring {tool.upper()} skills at: {target_path}")
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Sync target path to clean up any orphaned rules first!
            sync_target_directory(skills_dir, target_path, uninstall_all=False)
            
            for skill_folder in skills_dir.iterdir():
                if skill_folder.is_dir():
                    if tool in ["claude", "gemini", "codex"]:
                        # Directory-based linking
                        link_or_copy(skill_folder, target_path / skill_folder.name, is_directory=True)
                    elif tool == "copilot":
                        # Flat file-based linking with .agent.md suffix
                        skill_file = skill_folder / "SKILL.md"
                        if skill_file.exists():
                            link_or_copy(skill_file, target_path / f"{skill_folder.name}.agent.md", is_directory=False)
            linked_any = True

    if not linked_any:
        print("\nNo active agent config directories (e.g. ~/.claude or ~/.gemini/antigravity) were detected.")
        print("Please run your agent tools at least once to initialize their default paths.")

def uninstall_global(skills_dir: Path) -> None:
    """Cleans up all globally linked/copied skills."""
    print("Cleaning global agent configurations...")
    for tool, target_path in TARGETS.items():
        if target_path.exists():
            print(f"\nCleaning {tool.upper()} skills at: {target_path}")
            sync_target_directory(skills_dir, target_path, uninstall_all=True)

def compile_project(skills_dir: Path, project_path: Path) -> None:
    """Compiles rules locally into the target project workspace for Cursor and Windsurf."""
    project_path = project_path.resolve()
    if not project_path.is_dir():
        print(f"Error: Target path {project_path} is not a valid directory.")
        sys.exit(1)

    cursor_dir = project_path / ".cursor" / "rules"
    windsurf_dir = project_path / ".windsurf" / "rules"

    print(f"Configuring project-level rules at: {project_path}")

    # Process all skills
    for skill_folder in skills_dir.iterdir():
        if skill_folder.is_dir():
            skill_md = skill_folder / "SKILL.md"
            if not skill_md.exists():
                continue

            metadata, body = load_frontmatter(skill_md)
            desc = metadata.get("description", f"Behavior rule for {skill_folder.name}")
            
            # Cursor Compilation (.mdc format)
            cursor_dir.mkdir(parents=True, exist_ok=True)
            cursor_file = cursor_dir / f"{skill_folder.name}.mdc"
            cursor_content = f"---\ndescription: {desc}\nglobs: [\"**/*\"]\nalwaysApply: false\n---\n\n{body.strip()}\n"
            with open(cursor_file, "w", encoding="utf-8") as f:
                f.write(cursor_content)
            print(f"  [Cursor Rule Created] {cursor_file.relative_to(project_path)}")

            # Windsurf Compilation (.md format)
            windsurf_dir.mkdir(parents=True, exist_ok=True)
            windsurf_file = windsurf_dir / f"{skill_folder.name}.md"
            with open(windsurf_file, "w", encoding="utf-8") as f:
                f.write(f"# {skill_folder.name.replace('-', ' ').title()}\n\n{body.strip()}\n")
            print(f"  [Windsurf Rule Created] {windsurf_file.relative_to(project_path)}")

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

    args = parser.parse_args()

    repo_dir = Path(__file__).parent.resolve()
    skills_dir = repo_dir / "skills"

    if not skills_dir.exists() or not skills_dir.is_dir():
        print(f"Error: skills directory not found at {skills_dir}")
        sys.exit(1)

    if args.command == "link":
        install_global(skills_dir)
    elif args.command == "unlink":
        uninstall_global(skills_dir)
    elif args.command == "project":
        compile_project(skills_dir, Path(args.path))

if __name__ == "__main__":
    main()
