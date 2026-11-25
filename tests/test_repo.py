"""Structure checks: manifests, hook files, skill and agent frontmatter."""

import json
import os
import re
import unittest

from helpers import ROOT

PLUGINS = os.path.join(ROOT, "plugins")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def frontmatter(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return None
    fields = {}
    key = None
    for line in match.group(1).splitlines():
        top = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if top:
            key, value = top.group(1), top.group(2).strip()
            fields[key] = value
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    for k, v in fields.items():
        if v in (">", "|", ">-", "|-"):
            fields[k] = ""
    return fields


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Marketplace(unittest.TestCase):
    def setUp(self):
        self.market = load_json(os.path.join(ROOT, ".claude-plugin", "marketplace.json"))

    def test_required_fields(self):
        self.assertTrue(KEBAB.match(self.market["name"]))
        self.assertTrue(self.market["owner"]["name"])
        self.assertTrue(self.market["plugins"])

    def test_every_plugin_entry_matches_its_manifest(self):
        listed = set()
        for entry in self.market["plugins"]:
            source = entry["source"]
            self.assertTrue(source.startswith("./") and ".." not in source, source)
            manifest = load_json(os.path.join(ROOT, source, ".claude-plugin", "plugin.json"))
            self.assertEqual(manifest["name"], entry["name"])
            self.assertTrue(KEBAB.match(manifest["name"]))
            self.assertTrue(SEMVER.match(manifest["version"]))
            self.assertEqual(manifest.get("version"), entry.get("version", manifest["version"]))
            self.assertEqual(manifest.get("license"), "MIT")
            listed.add(os.path.normpath(os.path.join(ROOT, source)))
        on_disk = {os.path.join(PLUGINS, d) for d in os.listdir(PLUGINS)
                   if os.path.isdir(os.path.join(PLUGINS, d))}
        self.assertEqual(listed, on_disk, "every folder in plugins/ must be listed in marketplace.json")


class Hooks(unittest.TestCase):
    def test_hook_files_parse_and_point_at_real_scripts(self):
        for plugin in os.listdir(PLUGINS):
            path = os.path.join(PLUGINS, plugin, "hooks", "hooks.json")
            if not os.path.isfile(path):
                continue
            hooks = load_json(path)["hooks"]
            for event, groups in hooks.items():
                self.assertIn(event, {"PreToolUse", "PostToolUse", "Stop", "StopFailure", "Notification",
                                      "SessionStart", "SessionEnd", "UserPromptSubmit"})
                for group in groups:
                    for hook in group["hooks"]:
                        self.assertEqual(hook["type"], "command")
                        if hook.get("async"):
                            # Claude Code does not enforce timeout on async hooks, so none is set
                            self.assertNotIn("timeout", hook, "timeout does nothing on an async hook")
                        else:
                            self.assertLessEqual(hook.get("timeout", 60), 30, "hooks must stay fast")
                        script = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+?)\"?(?:\s|$)", hook["command"])
                        self.assertTrue(script, hook["command"])
                        self.assertTrue(os.path.isfile(os.path.join(PLUGINS, plugin, script.group(1))),
                                        hook["command"])


class SkillsAndAgents(unittest.TestCase):
    def test_skills(self):
        count = 0
        for dirpath, _, files in os.walk(PLUGINS):
            if "SKILL.md" not in files:
                continue
            count += 1
            path = os.path.join(dirpath, "SKILL.md")
            fm = frontmatter(path)
            self.assertIsNotNone(fm, path)
            self.assertEqual(fm.get("name"), os.path.basename(dirpath), path)
            self.assertGreater(len(fm.get("description", "")), 40, f"{path}: description too thin to trigger")
            # every file the skill links to must exist
            with open(path, encoding="utf-8") as f:
                body = f.read()
            for link in re.findall(r"\]\((?!https?://|#)([^)\s]+)\)", body):
                target = os.path.normpath(os.path.join(dirpath, link.split("#")[0]))
                self.assertTrue(os.path.exists(target), f"{path}: broken link {link}")
        self.assertGreaterEqual(count, 9)

    def test_agents(self):
        agents_dir = os.path.join(PLUGINS, "gtm-outbound", "agents")
        names = [n for n in os.listdir(agents_dir) if n.endswith(".md")]
        self.assertEqual(len(names), 7)
        for name in names:
            fm = frontmatter(os.path.join(agents_dir, name))
            self.assertIsNotNone(fm, name)
            self.assertEqual(fm.get("name"), name[:-3])
            self.assertTrue(fm.get("description"), name)
            if "model" in fm:
                self.assertIn(fm["model"], {"haiku", "sonnet", "opus", "inherit"}, name)


class NoSecrets(unittest.TestCase):
    PATTERNS = [
        re.compile(r"\b(?:sk|rk)-(?:live|proj|ant)?[A-Za-z0-9_\-]{24,}"),
        re.compile(r"\bxox[abprs]-\d{6,}-[A-Za-z0-9\-]+"),
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]{6,}/B[A-Z0-9]{6,}/[A-Za-z0-9]{20,}"),
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ]

    def test_no_credentials_in_the_repo(self):
        for dirpath, dirnames, files in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for name in files:
                path = os.path.join(dirpath, name)
                if name.endswith(".pyc") or path == os.path.abspath(__file__):
                    continue
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                for pattern in self.PATTERNS:
                    self.assertIsNone(pattern.search(text), f"possible secret in {path}")
                self.assertNotEqual(name, ".env", f"{path}: never commit a .env file")


if __name__ == "__main__":
    unittest.main()
