"""Behavioral regression checks in isolated repositories; no installed plugin changes."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("harness_project", PACKAGE / "harness/bin/project.py")
project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harness-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project with spaces"
        self.root.mkdir()

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, ensure_ascii=False, indent=2) if isinstance(data, dict) else data
        path.write_text(text, encoding="utf-8")
        return path

    def ready(self, settings=None):
        project.initialize(self.root)
        data = project.starter()
        data.update(status="ready", purpose="기존 웹 서비스 유지보수",
                    success_criteria=["API 호환성과 회귀 테스트 통과"], work_types=["bugfix"])
        data["settings"] = settings or {}
        self.write(".harness/project.json", data)
        return data

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def cli(self, *args, package=PACKAGE):
        return subprocess.run([sys.executable, str(package / "harness/bin/project.py"), *map(str, args)],
                              text=True, capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def test_init_creates_only_project_profile(self):
        project.initialize(self.root)
        self.assertEqual(set(p.name for p in self.root.iterdir()), {".harness"})
        self.assertEqual(project.profile(self.root)["status"], "draft")
        with self.assertRaisesRegex(ValueError, "draft"):
            project.profile(self.root, ready=True)

    def test_reinit_preserves_answers_rules_and_existing_instructions(self):
        self.write("AGENTS.md", "# User instructions\nKeep this byte-for-byte.")
        self.write("CLAUDE.md", "# Other rules\n")
        project.initialize(self.root, link=True)
        self.ready({"execution_mode": "skill"})
        self.write(".harness/rules.md", "# User edits\nPreserve API compatibility.\n")
        before = self.snapshot()
        self.assertEqual(project.initialize(self.root, link=True)["created_or_linked"], [])
        self.assertEqual(before, self.snapshot())
        self.assertTrue((self.root / "AGENTS.md").read_text().startswith("# User instructions\nKeep this byte-for-byte."))

    def test_interrupted_init_preserves_draft_and_fills_missing_files(self):
        data = project.starter()
        data.update(purpose="Maintain desktop app", open_questions=["Which OS versions?"])
        self.write(".harness/project.json", data)
        project.initialize(self.root)
        self.assertEqual(project.profile(self.root), data)
        self.assertTrue((self.root / ".harness/rules.md").exists())

    def test_future_schema_is_not_overwritten_or_completed(self):
        self.write(".harness/project.json", {"schema_version": 2})
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "unsupported schema"):
            project.initialize(self.root, link=True)
        self.assertEqual(before, self.snapshot())

    def test_malformed_link_markers_fail_before_any_writes(self):
        self.write("AGENTS.md", project.START)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "markers"):
            project.initialize(self.root, link=True)
        self.assertEqual(before, self.snapshot())

    def test_symlink_targets_are_not_followed(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.root / ".harness").symlink_to(outside, target_is_directory=True)
        result = self.cli("init", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_ready_requires_purpose_criteria_types_and_no_questions(self):
        data = self.ready()
        for key, value in (("purpose", ""), ("success_criteria", []), ("work_types", []),
                           ("open_questions", ["Unresolved requirement"])):
            with self.subTest(key=key):
                changed = {**data, key: value}
                self.write(".harness/project.json", changed)
                with self.assertRaisesRegex(ValueError, "ready profile"):
                    project.profile(self.root)

    def test_configuration_precedence_and_recursive_merge(self):
        self.ready({"execution_mode": "skill", "coverage_thresholds": {"total": 81}, "project": {"roles": ["backend-engineer"]}})
        task = self.write("task.json", {"coverage_thresholds": {"total": 83}, "project": {"roles": ["test-engineer"]}})
        user = self.write("user.json", {"execution_mode": "agent", "coverage_thresholds": {"total": 85}})
        actual = project.resolve(self.root, task, user)
        self.assertEqual(actual["settings"]["execution_mode"], "agent")
        self.assertEqual(actual["settings"]["coverage_thresholds"], {"domain": 90, "application": 80, "adapter": 60, "total": 85})
        self.assertEqual(actual["settings"]["project"]["roles"], ["test-engineer"])
        self.assertEqual(actual["layers"], ["defaults", "project", "task", "user"])
        self.assertNotIn(str(PACKAGE), json.dumps(actual))

    def test_invalid_settings_are_errors_not_silent_defaults(self):
        cases = [
            {"unknown": 1}, {"gate": {"max_retries": 0}}, {"gate": {"max_retries": True}},
            {"coverage_thresholds": {"total": 101}}, {"coverage_thresholds": {"domain": True}},
            {"execution_mode": "turbo"}, {"docs": {"workspace_retention": "delete"}},
            {"project": {"roles": ["unknown-role"]}}, {"architecture_rules": ["A10"]},
        ]
        for settings in cases:
            with self.subTest(settings=settings):
                self.ready(settings)
                with self.assertRaises(ValueError):
                    project.resolve(self.root)

    def test_missing_and_escaping_extensions_are_rejected(self):
        for ref in (".harness/missing.md", "../outside.md", "README.md", "/etc/hosts"):
            with self.subTest(ref=ref):
                data = self.ready()
                data["extensions"] = [ref]
                self.write(".harness/project.json", data)
                with self.assertRaises(ValueError):
                    project.profile(self.root)

    def test_valid_project_extension(self):
        data = self.ready()
        self.write(".harness/checklists/api.md", "# API compatibility checks\n")
        data["extensions"] = [".harness/checklists/api.md"]
        self.write(".harness/project.json", data)
        self.assertEqual(project.profile(self.root), data)

    def test_duplicate_json_keys_are_rejected(self):
        path = self.write("duplicate.json", '{"execution_mode":"skill","execution_mode":"agent"}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            project.read_json(path)

    def test_resolve_is_read_only_and_never_executes_test_commands(self):
        marker = self.root / "must-not-exist"
        self.ready({"project": {"test_commands": {"unit": f"touch '{marker}'"}}})
        before = self.snapshot()
        result = self.cli("resolve", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(marker.exists())

    def test_cached_package_relocation_and_update_preserve_project(self):
        self.ready({"gate": {"max_retries": 2}})
        before = self.snapshot()
        cache = Path(self.temp.name) / "cache with spaces" / "0.1.0"
        shutil.copytree(PACKAGE, cache, ignore=shutil.ignore_patterns("__pycache__", "tests"))
        first = self.cli("resolve", self.root, package=cache)
        self.assertEqual(first.returncode, 0, first.stderr)
        manifest_path = cache / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = "0.2.0"
        manifest_path.write_text(json.dumps(manifest))
        second = self.cli("resolve", self.root, package=cache)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(first.stdout)["settings"], json.loads(second.stdout)["settings"])
        self.assertEqual(json.loads(second.stdout)["plugin_version"], "0.2.0")
        self.assertEqual(before, self.snapshot())
        check = subprocess.run(["bash", str(cache / "harness/bin/verify.sh"), "--project", str(self.root)], text=True, capture_output=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertFalse((cache / "harness/bin/__pycache__").exists())

    def test_unrelated_project_commands_and_agents_do_not_fail_validation(self):
        self.ready()
        self.write(".claude/commands/user-command.md", "# User command\n")
        self.write(".claude/agents/custom.md", "---\nname: custom\nmodel: sonnet\n---\n")
        result = subprocess.run(["bash", str(PACKAGE / "harness/bin/verify.sh"), "--project", str(self.root)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_legacy_install_does_not_write_into_project(self):
        self.write("harness/config.yml.harness-new", "User's pending merge")
        before = self.snapshot()
        result = subprocess.run(["bash", str(PACKAGE / "harness/bin/install.sh"), str(self.root)], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.snapshot())
        self.assertIn("harness-init", result.stderr)

    def test_nonexistent_project_fails_without_creating_it(self):
        missing = self.root / "missing"
        result = self.cli("init", missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(missing.exists())

    def test_plugin_cannot_initialize_itself(self):
        result = self.cli("init", PACKAGE)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the plugin", result.stderr)


if __name__ == "__main__":
    unittest.main()
