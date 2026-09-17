#!/usr/bin/env python3
"""Validate plugin-owned assets, not unrelated files in a consuming repository."""
import argparse
import re
import sys

sys.dont_write_bytecode = True
import project

ROOT = project.PLUGIN


def verify():
    errors = []
    required = [
        "harness/runtime.md", "harness/project-profile.md", "harness/defaults.json",
        "harness/pipeline.md", "harness/execution-modes.md",
        "harness/entrypoints/AGENTS.md", "harness/entrypoints/CLAUDE.md",
        "skills/harness-init/SKILL.md", "skills/sdlc-orchestrator/SKILL.md",
    ]
    for name in required:
        if not (ROOT / name).is_file():
            errors.append(f"missing {name}")
    for vendor in (".codex-plugin", ".claude-plugin"):
        try:
            manifest = project.read_json(ROOT / vendor / "plugin.json")
            if manifest.get("name") != "harness-sdlc":
                errors.append(f"{vendor}: unexpected plugin identity")
            if manifest.get("skills") != "./skills/":
                errors.append(f"{vendor}: expected skills ./skills/")
            if vendor == ".claude-plugin" and "agents" in manifest:
                errors.append("Claude agents use standard agents/ discovery; omit custom agents field")
        except (ValueError, OSError) as error:
            errors.append(str(error))
    try:
        project.validate_settings(project.merge(project.defaults(), project.defaults()))
    except (ValueError, OSError) as error:
        errors.append(str(error))

    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    agents = sorted((ROOT / "agents").glob("*.md"))
    if not skills or not agents:
        errors.append("skills and agents must not be empty")
    routing = (ROOT / "harness/entrypoints/AGENTS.md").read_text(encoding="utf-8")
    for file in skills + agents:
        text = file.read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        name = file.parent.name if file.name == "SKILL.md" else file.stem
        if not front or not re.search(rf"^name: {re.escape(name)}$", front[1], re.M):
            errors.append(f"{file.relative_to(ROOT)}: missing/mismatched frontmatter name")
        if not front or not re.search(r"^description: .+", front[1], re.M):
            errors.append(f"{file.relative_to(ROOT)}: missing description")
        if "harness/runtime.md" not in text:
            errors.append(f"{name}: missing runtime bootstrap")
        if file.name == "SKILL.md" and f"`{name}`" not in routing:
            errors.append(f"{name}: missing routing entry")

    for directory in ("skills", "agents", "harness", "docs/template"):
        for file in (ROOT / directory).rglob("*.md"):
            text = file.read_text(encoding="utf-8")
            if directory in ("skills", "agents") and re.search(r"\.claude/(agents|skills)/", text):
                errors.append(f"{file.relative_to(ROOT)}: legacy copy-install reference")
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith("#") or any(c in link for c in "{}*"):
                    continue
                target = (file.parent / link.split("#")[0]).resolve()
                if not target.is_relative_to(ROOT) or not target.exists():
                    errors.append(f"{file.relative_to(ROOT)}: broken/outside link {link}")
            for ref in re.findall(r"`((?:harness/|skills/|agents/|docs/template/)[A-Za-z0-9_./-]+)`", text):
                if ref == "harness/config.yml" and file.name == "project-profile.md":
                    continue  # Input to migration, not a package asset.
                if not (ROOT / ref).exists():
                    errors.append(f"{file.relative_to(ROOT)}: missing asset {ref}")
    return errors, len(skills), len(agents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="also check this project's ready profile")
    args = parser.parse_args()
    try:
        errors, skills, agents = verify()
        if args.project:
            project.profile(project.project_root(args.project), ready=True)
    except (ValueError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    print(f"Package: {skills} skills, {agents} roles; failures: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
