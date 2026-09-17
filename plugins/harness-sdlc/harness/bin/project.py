#!/usr/bin/env python3
"""Project profile initialization and validation; no package installation or command execution."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

PLUGIN = Path(__file__).resolve().parents[2]
WORK_TYPES = {"feature", "bugfix", "refactor", "docs", "cicd"}
START = "<!-- harness-sdlc:start -->"
END = "<!-- harness-sdlc:end -->"
LINK = f"""{START}
## Harness SDLC

이 프로젝트의 하네스 설정은 `.harness/project.json`, 추가 규칙은
`.harness/context.md`와 `.harness/rules.md`에서 읽는다.
최초 설정·운영 규칙 변경은 설치된 harness-sdlc의 `harness-init` 스킬,
개발 작업·재개는 `sdlc-orchestrator` 스킬을 사용한다.
공통 자산은 설치된 플러그인에서 읽고 캐시에는 쓰지 않는다.
{END}
"""


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected object")
    return data


def defaults():
    return read_json(PLUGIN / "harness/defaults.json")


def merge(base, override, prefix=""):
    """Strict recursive object merge; arrays replace, unknown keys fail."""
    if not isinstance(override, dict):
        raise ValueError(f"{prefix or 'settings'}: expected object")
    result = copy.deepcopy(base)
    for key, value in override.items():
        name = f"{prefix}.{key}" if prefix else key
        if key not in base:
            raise ValueError(f"unknown setting: {name}")
        expected = base[key]
        if isinstance(expected, dict):
            result[key] = merge(expected, value, name)
        else:
            numeric = prefix == "coverage_thresholds"
            if (numeric and type(value) not in (int, float)) or (
                not numeric and type(value) is not type(expected)
            ):
                raise ValueError(f"{name}: invalid type")
            result[key] = copy.deepcopy(value)
    return result


def validate_settings(config):
    enums = {
        "execution_mode": {"skill", "balanced", "agent", "ask"},
        "docs.workspace_retention": {"keep", "archive"},
        "project.ddd_level": {"auto", "0", "1", "2", "3"},
        "project.ci_provider": {"unspecified", "github-actions", "gitlab-ci", "jenkins", "other"},
        "project.autonomy": {"analysis", "implementation", "delivery"},
        "project.document_scope": {"required", "full"},
    }
    for name, allowed in enums.items():
        value = config
        for part in name.split("."):
            value = value[part]
        if value not in allowed:
            raise ValueError(f"{name}: expected one of {sorted(allowed)}")
    for key, value in config["coverage_thresholds"].items():
        if not 0 <= value <= 100:
            raise ValueError(f"coverage_thresholds.{key}: expected 0..100")
    groups = [config["gate"], *config["suggest_thresholds"].values()]
    if any(type(v) is not int or v < 1 for group in groups for v in group.values()):
        raise ValueError("gate/suggest_thresholds: expected positive integers")
    allowed_rules = {f"A{i}" for i in range(1, 10)}
    allowed_roles = {p.stem for p in (PLUGIN / "agents").glob("*.md")}
    for name, values, allowed in (
        ("architecture_rules", config["architecture_rules"], allowed_rules),
        ("project.roles", config["project"]["roles"], allowed_roles),
    ):
        strings(values, name)
        if len(values) != len(set(values)) or not set(values) <= allowed:
            raise ValueError(f"{name}: duplicate or unknown value")


def strings(value, name):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{name}: expected list of non-empty strings")


def starter():
    return {
        "schema_version": 1, "status": "draft", "purpose": "",
        "success_criteria": [], "constraints": [], "work_types": [],
        "context_sources": [], "open_questions": [], "extensions": [], "settings": {},
    }


def project_root(raw):
    root = Path(raw).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory not found: {root}")
    if root == PLUGIN or PLUGIN in root.parents:
        raise ValueError("project must be outside the plugin package")
    if (root / ".harness").is_symlink():
        raise ValueError(".harness must not be a symlink")
    return root


def profile(root, ready=False):
    root = project_root(root)
    path = root / ".harness/project.json"
    if path.is_symlink():
        raise ValueError("project.json must not be a symlink")
    data = read_json(path)
    if set(data) != set(starter()):
        raise ValueError("profile fields differ from schema_version 1; migrate explicitly")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported schema_version; explicit migration required")
    if data["status"] not in ("draft", "ready"):
        raise ValueError("status must be draft or ready")
    if not isinstance(data["purpose"], str):
        raise ValueError("purpose must be a string")
    for key in ("success_criteria", "constraints", "work_types", "context_sources", "open_questions", "extensions"):
        strings(data[key], key)
    if not set(data["work_types"]) <= WORK_TYPES:
        raise ValueError("unknown work_types")
    if ready and data["status"] != "ready":
        raise ValueError("profile is draft; resume harness-init")
    if data["status"] == "ready" and (
        not data["purpose"].strip() or not data["success_criteria"]
        or not data["work_types"] or data["open_questions"]
    ):
        raise ValueError("ready profile needs purpose, success_criteria, work_types and no open_questions")
    for ref in [".harness/context.md", ".harness/rules.md", *data["extensions"]]:
        p = Path(ref)
        target = (root / p).resolve()
        if p.is_absolute() or ".." in p.parts or not target.is_relative_to(root / ".harness"):
            raise ValueError(f"profile reference must stay inside .harness: {ref}")
        if target.suffix != ".md" or not target.is_file():
            raise ValueError(f"profile reference missing or not Markdown: {ref}")
    validate_settings(merge(defaults(), data["settings"]))
    return data


def initialize(root, link=False):
    root = project_root(root)
    directory = root / ".harness"
    files = {
        directory / "project.json": json.dumps(starter(), ensure_ascii=False, indent=2) + "\n",
        directory / "context.md": "# 프로젝트 맥락\n\n## 목적과 인터뷰 답변\n\n## 관찰 근거\n\n## 결정과 가정\n",
        directory / "rules.md": "# 프로젝트 운영 규칙\n\n공통 하네스에 추가할 프로젝트별 절차와 체크리스트를 기록한다.\n",
    }
    # Preflight before any writes; do not follow linked user files.
    for path in [*files, *([root / "AGENTS.md", root / "CLAUDE.md"] if link else [])]:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"refusing non-regular target: {path}")
    if (directory / "project.json").exists():
        existing = read_json(directory / "project.json")
        if type(existing.get("schema_version")) is not int or existing["schema_version"] != 1:
            raise ValueError("unsupported schema_version; init will not migrate it")
    links = {}
    if link:
        for name in ("AGENTS.md", "CLAUDE.md"):
            path = root / name
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            if START in text or END in text:
                if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
                    raise ValueError(f"invalid harness markers in {name}; resolve before init")
                continue  # Preserve even user-edited managed blocks.
            links[path] = text + ("\n\n" if text else "") + LINK
    directory.mkdir(exist_ok=True)
    created = []
    for path, content in files.items():
        if not path.exists():
            with path.open("x", encoding="utf-8") as f:
                f.write(content)
            created.append(str(path.relative_to(root)))
    for path, content in links.items():
        path.write_text(content, encoding="utf-8")
        created.append(str(path.relative_to(root)))
    return {"created_or_linked": created, "next": "Interview or resume using harness-init; existing files preserved."}


def resolve(root, task=None, override=None):
    root = project_root(root)
    data = profile(root, ready=True)
    effective = defaults()
    layers = [("project", data["settings"])]
    if task:
        layers.append(("task", read_json(Path(task))))
    if override:
        layers.append(("user", read_json(Path(override))))
    for _, settings in layers:
        effective = merge(effective, settings)
        validate_settings(effective)
    manifest = read_json(PLUGIN / ".codex-plugin/plugin.json")
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {
        "schema_version": 1, "plugin_version": manifest["version"],
        "profile_sha256": fingerprint, "layers": ["defaults", *[n for n, _ in layers]],
        "settings": effective,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "check", "resolve"):
        p = sub.add_parser(command)
        p.add_argument("project")
        if command == "init":
            p.add_argument("--link", action="store_true")
        elif command == "check":
            p.add_argument("--ready", action="store_true")
        else:
            p.add_argument("--task-config")
            p.add_argument("--override")
    args = parser.parse_args()
    try:
        root = project_root(args.project)
        if args.command == "init":
            result = initialize(root, args.link)
        elif args.command == "check":
            result = {"status": profile(root, args.ready)["status"], "valid": True}
        else:
            result = resolve(root, args.task_config, args.override)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
