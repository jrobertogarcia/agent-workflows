#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from pathlib import Path

# Target paths for global tools
HOME = Path.home()
TARGETS = {
    "claude": HOME / ".claude" / "skills",
    "gemini": HOME / ".gemini" / "antigravity" / "skills",
    "copilot": HOME / ".copilot" / "agents",
    "codex": HOME / ".codex" / "skills",
}

def load_frontmatter(skill_md_path: Path):
    """Parses a SKILL.md file and extracts its frontmatter and markdown body."""
    if not skill_md_path.exists():
        return {}, ""
    
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
            metadata = {}
            for line in frontmatter_lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            return metadata, "\n".join(body_lines)
            
    return {}, content

def clean_target(target: Path):
    """Safely deletes a file, directory, or symlink at the target path."""
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

def link_or_copy(source: Path, target: Path, is_directory: bool = False):
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
            shutil.copytree(source, target)
            print(f"  [Copied (Fallback)] {target.name} (Directory)")
        else:
            shutil.copy2(source, target)
            print(f"  [Copied (Fallback)] {target.name} (File)")

def install_global(skills_dir: Path):
    """Installs skills globally for detected agent tool folders."""
    print("Scanning active agent configurations...")
    linked_any = False

    for tool, target_path in TARGETS.items():
        # Check if the parent configuration folder exists (indicates tool is active/installed)
        parent_config = target_path.parent
        if parent_config.exists():
            print(f"\nConfiguring {tool.upper()} skills at: {target_path}")
            target_path.mkdir(parents=True, exist_ok=True)
            
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

def uninstall_global(skills_dir: Path):
    """Cleans up all globally linked/copied skills."""
    print("Cleaning global agent configurations...")
    for tool, target_path in TARGETS.items():
        if target_path.exists():
            print(f"\nCleaning {tool.upper()} skills at: {target_path}")
            for skill_folder in skills_dir.iterdir():
                if skill_folder.is_dir():
                    if tool in ["claude", "gemini", "codex"]:
                        target = target_path / skill_folder.name
                        if target.exists() or target.is_symlink():
                            clean_target(target)
                            print(f"  [Removed] {target.name}")
                    elif tool == "copilot":
                        target = target_path / f"{skill_folder.name}.agent.md"
                        if target.exists() or target.is_symlink():
                            clean_target(target)
                            print(f"  [Removed] {target.name}")

def compile_project(skills_dir: Path, project_path: Path):
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

def main():
    parser = argparse.ArgumentParser(description="Shared Agent Skills Repository installer script.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Link command
    subparsers.add_parser("link", help="Link skills globally to active agent config directories.")

    # Unlink command
    subparsers.add_parser("unlink", help="Unlink global skills from agent config directories.")

    # Project command
    proj_parser = subparsers.add_parser("project", help="Link/Compile skills locally for Cursor and Windsurf in a project.")
    proj_parser.add_argument("--path", required=True, help="Path to the local project workspace root.")

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
