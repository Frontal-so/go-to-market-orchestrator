import contextlib
import io
import json
import os
import shutil
import stat
import tempfile
import unittest
from unittest import mock

from helpers import MIGRATE, load, run_script

V1_HOOK = {"type": "command", "command": "bash \"$CLAUDE_GTM_DIR/orchestrator/run.sh\" slack ping"}
OWN_HOOK = {"type": "command", "command": "python3 ~/bin/my-own-hook.py"}


def make_v1_clone(root):
    """A directory shaped like a v1 clone, with the files v1's installer linked to."""
    os.makedirs(os.path.join(root, "orchestrator"))
    open(os.path.join(root, "orchestrator", "run.sh"), "w").close()
    os.makedirs(os.path.join(root, "skills", "signal-monitor"))
    open(os.path.join(root, "skills", "signal-monitor", "SKILL.md"), "w").close()
    os.makedirs(os.path.join(root, "agents", "commands"))
    for name in ("meeting-prep.md", "hook-writer.md"):
        open(os.path.join(root, "agents", name), "w").close()
    return root


def settings_with_v1():
    return {
        "model": "sonnet",
        "hooks": {
            "Stop": [{"hooks": [V1_HOOK, OWN_HOOK]}],
            "PostToolUse": [{"matcher": "*", "hooks": [V1_HOOK]}],
            "PreToolUse": [{"matcher": "Bash", "hooks": [OWN_HOOK]}],
        },
    }


class RemoveV1Hooks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = self.tmp.name
        self.settings = os.path.join(self.home, "settings.json")
        with open(self.settings, "w") as f:
            json.dump(settings_with_v1(), f)

    def tearDown(self):
        self.tmp.cleanup()

    def run_migrate(self, *args):
        return run_script(MIGRATE, "", ["--claude-home", self.home, *args])

    def read(self):
        with open(self.settings) as f:
            return json.load(f)

    def test_dry_run_changes_nothing(self):
        result = self.run_migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 v1 hook(s) would be removed", result.stdout)
        self.assertEqual(self.read(), settings_with_v1())

    def test_apply_removes_only_v1_hooks_and_backs_up(self):
        result = self.run_migrate("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read(), {
            "model": "sonnet",
            "hooks": {
                "Stop": [{"hooks": [OWN_HOOK]}],
                "PreToolUse": [{"matcher": "Bash", "hooks": [OWN_HOOK]}],
            },
        })
        backups = [n for n in os.listdir(self.home) if n.startswith("settings.json.bak-v1-")]
        self.assertEqual(len(backups), 1)
        with open(os.path.join(self.home, backups[0])) as f:
            self.assertEqual(json.load(f), settings_with_v1())

    def test_unparseable_settings_are_left_alone(self):
        with open(self.settings, "w") as f:
            f.write("{ not json")
        result = self.run_migrate("--apply")
        self.assertEqual(result.returncode, 2)
        with open(self.settings) as f:
            self.assertEqual(f.read(), "{ not json")

    def test_copies_are_moved_only_with_evidence(self):
        clone = make_v1_clone(os.path.join(self.home, "src", "go-to-market-orchestrator"))
        v1_skill = os.path.join(self.home, "skills", "signal-monitor")
        own_skill = os.path.join(self.home, "skills", "lead-enrichment")  # same name as a v1 skill, but yours
        os.makedirs(v1_skill)
        os.makedirs(own_skill)
        os.symlink(os.path.join(clone, "skills", "signal-monitor", "SKILL.md"), os.path.join(v1_skill, "SKILL.md"))
        with open(os.path.join(own_skill, "SKILL.md"), "w") as f:
            f.write("---\nname: lead-enrichment\ndescription: x\n---\n")
        with open(os.path.join(self.home, ".gtm-installed.json"), "w") as f:
            json.dump({"skills": ["signal-monitor"], "agents": [], "commands": []}, f)

        dry = self.run_migrate("--move-copies")
        self.assertTrue(os.path.isdir(v1_skill), "a dry run must not move anything")
        self.assertIn(v1_skill, dry.stdout)
        self.assertNotIn(own_skill, dry.stdout)

        result = self.run_migrate("--apply", "--move-copies")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(os.path.exists(v1_skill))
        self.assertTrue(os.path.isdir(own_skill), "a same-name skill of your own is never moved")
        backups = [n for n in os.listdir(self.home) if n.startswith("gtm-v1-backup-")]
        self.assertEqual(len(backups), 1)
        self.assertTrue(os.path.islink(os.path.join(self.home, backups[0], "skills", "signal-monitor", "SKILL.md")))

    def test_same_name_file_without_evidence_is_left_alone(self):
        agent = os.path.join(self.home, "agents", "meeting-prep.md")
        os.makedirs(os.path.dirname(agent))
        with open(agent, "w") as f:
            f.write("---\nname: meeting-prep\ndescription: mine\n---\n")
        self.run_migrate("--apply", "--move-copies")
        self.assertTrue(os.path.isfile(agent))

    def test_symlinked_settings_are_edited_in_place(self):
        real = os.path.join(self.home, "dotfiles-settings.json")
        os.rename(self.settings, real)
        os.symlink(real, self.settings)
        result = self.run_migrate("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(os.path.islink(self.settings), "the link must stay a link")
        with open(real) as f:
            self.assertNotIn("CLAUDE_GTM_DIR", f.read())

    def test_unrelated_run_sh_hooks_are_kept(self):
        other = {"type": "command", "command": "bash ~/work/orchestrator/run.sh build"}
        with open(self.settings, "w") as f:
            json.dump({"hooks": {"Stop": [{"hooks": [other]}]}}, f)
        self.run_migrate("--apply")
        self.assertEqual(self.read(), {"hooks": {"Stop": [{"hooks": [other]}]}})

    # (1) only v1's exact command form counts as a v1 hook
    def test_only_the_exact_v1_command_form_is_removed(self):
        braces = {"type": "command", "command": "bash ${CLAUDE_GTM_DIR}/orchestrator/run.sh notion log-session"}
        mentions = {"type": "command", "command": "echo $CLAUDE_GTM_DIR; bash ~/work/orchestrator/run.sh build"}
        chained = {"type": "command", "command": "bash \"$CLAUDE_GTM_DIR/orchestrator/run.sh\" slack notify && ./deploy.sh"}
        with open(self.settings, "w") as f:
            json.dump({"hooks": {"Stop": [{"hooks": [braces, mentions, chained]}]}}, f)
        result = self.run_migrate("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read(), {"hooks": {"Stop": [{"hooks": [mentions, chained]}]}})

    # (2) v1's install record alone does not move a file you replaced
    def test_install_record_alone_does_not_move_a_replaced_file(self):
        skill = os.path.join(self.home, "skills", "signal-monitor")
        os.makedirs(skill)
        with open(os.path.join(skill, "SKILL.md"), "w") as f:
            f.write("---\nname: signal-monitor\ndescription: my own version\n---\n")
        with open(os.path.join(self.home, ".gtm-installed.json"), "w") as f:
            json.dump({"root": "/nowhere", "skills": ["signal-monitor"], "agents": [], "commands": []}, f)
        result = self.run_migrate("--apply", "--move-copies")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(os.path.isfile(os.path.join(skill, "SKILL.md")), "a replaced file is never moved")
        self.assertIn("left alone", result.stdout)
        self.assertIn(skill, result.stdout)

    def test_exact_v1_file_is_found_by_its_hash(self):
        m = load(MIGRATE, "remove_v1_hooks_hash")
        agent = os.path.join(self.home, "agents", "hook-writer.md")
        os.makedirs(os.path.dirname(agent))
        with open(agent, "w") as f:
            f.write("v1 text")
        self.assertFalse(m.is_v1_copy(agent, "agents", set()))
        with mock.patch.object(m, "V1_HASHES", {m.sha256(agent)}):
            self.assertTrue(m.is_v1_copy(agent, "agents", set()))

    # (3) a link counts only when it points into a real v1 clone, at v1's own layout
    def test_symlink_must_point_into_a_v1_clone(self):
        clone = make_v1_clone(os.path.join(self.home, "src", "gtm"))
        lookalike = os.path.join(self.home, "src", "not-go-to-market-orchestrator-custom", "agents")
        os.makedirs(lookalike)
        open(os.path.join(lookalike, "meeting-prep.md"), "w").close()
        agents = os.path.join(self.home, "agents")
        os.makedirs(agents)
        os.symlink(os.path.join(lookalike, "meeting-prep.md"), os.path.join(agents, "meeting-prep.md"))
        os.symlink(os.path.join(clone, "agents", "hook-writer.md"), os.path.join(agents, "hook-writer.md"))
        gone = os.path.join(self.home, "deleted-clone")  # a clone removed since: dangling link, record root
        os.symlink(os.path.join(gone, "agents", "lead-prioritizer.md"), os.path.join(agents, "lead-prioritizer.md"))
        with open(os.path.join(self.home, ".gtm-installed.json"), "w") as f:
            json.dump({"root": gone, "skills": [], "agents": ["lead-prioritizer.md"], "commands": []}, f)
        result = self.run_migrate("--apply", "--move-copies")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(os.path.islink(os.path.join(agents, "meeting-prep.md")), "a lookalike path is not a v1 clone")
        self.assertFalse(os.path.lexists(os.path.join(agents, "hook-writer.md")))
        self.assertFalse(os.path.lexists(os.path.join(agents, "lead-prioritizer.md")))

    # (4) secrets in printed hook commands are masked
    def test_mask_hides_tokens_webhooks_and_key_values(self):
        m = load(MIGRATE, "remove_v1_hooks_mask")
        for secret, command in (
            ("T000/B000/abcdef", "bash x.sh https://hooks.slack.com/services/T000/B000/abcdef"),
            ("123/tok", "curl -d x https://discord.com/api/webhooks/123/tok"),
            ("987/zz", "curl https://hooks.zapier.com/hooks/catch/987/zz"),
            ("shorttok", "curl -H 'Authorization: Bearer shorttok' x"),
            ("dXNlcjpw", "curl -H 'Authorization: Basic dXNlcjpw' x"),
            ("abc123", "HUBSPOT_API_KEY=abc123 bash run.sh"),
            ("hunter2", "curl --password=hunter2 x"),
            ("q1w2e3", "curl 'https://api.example/x?access_token=q1w2e3&page=2'"),
        ):
            self.assertNotIn(secret, m.mask(command), command)

    # (5) the backup keeps the settings file's mode
    def test_backup_keeps_a_restrictive_mode(self):
        os.chmod(self.settings, 0o600)
        result = self.run_migrate("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        backup = [n for n in os.listdir(self.home) if n.startswith("settings.json.bak-v1-")][0]
        self.assertEqual(stat.S_IMODE(os.stat(os.path.join(self.home, backup)).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.settings).st_mode), 0o600)

    # (6) the new file goes through an exclusive temp file, and a change meanwhile aborts the write
    def run_in_process(self, m, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = m.main(["--claude-home", self.home, *args])
        return code, out.getvalue()

    def test_old_predictable_temp_name_is_not_followed(self):
        m = load(MIGRATE, "remove_v1_hooks_tmp")
        victim = os.path.join(self.home, "victim.txt")
        with open(victim, "w") as f:
            f.write("keep me")
        os.symlink(victim, self.settings + f".tmp-{os.getpid()}")
        code, _ = self.run_in_process(m, "--apply")
        self.assertEqual(code, 0)
        with open(victim) as f:
            self.assertEqual(f.read(), "keep me")
        self.assertNotIn("CLAUDE_GTM_DIR", json.dumps(self.read()))
        self.assertEqual([n for n in os.listdir(self.home) if n.startswith(".settings-v1-clean-")], [])

    def test_a_change_meanwhile_leaves_the_file_alone(self):
        m = load(MIGRATE, "remove_v1_hooks_race")
        real_mkstemp = tempfile.mkstemp

        def someone_writes(*a, **kw):
            with open(self.settings, "w") as f:
                json.dump({"model": "opus"}, f)
            return real_mkstemp(*a, **kw)

        with mock.patch.object(m.tempfile, "mkstemp", side_effect=someone_writes):
            code, out = self.run_in_process(m, "--apply")
        self.assertEqual(code, 4)
        self.assertIn("changed while this ran", out)
        self.assertEqual(self.read(), {"model": "opus"})
        self.assertEqual([n for n in os.listdir(self.home) if n.startswith(".settings-v1-clean-")], [])

    # (7) the move report says exactly what moved and what did not
    def test_move_report_names_what_moved_and_what_did_not(self):
        m = load(MIGRATE, "remove_v1_hooks_move")
        clone = make_v1_clone(os.path.join(self.home, "src", "gtm"))
        agents = os.path.join(self.home, "agents")
        os.makedirs(agents)
        for name in ("meeting-prep.md", "hook-writer.md"):
            os.symlink(os.path.join(clone, "agents", name), os.path.join(agents, name))
        real_move = shutil.move

        def flaky(src, dst):
            if src.endswith("meeting-prep.md"):
                raise PermissionError("denied")
            return real_move(src, dst)

        with mock.patch.object(m.shutil, "move", side_effect=flaky):
            code, out = self.run_in_process(m, "--apply", "--move-copies")
        self.assertEqual(code, 3)
        self.assertIn("moved " + os.path.join(agents, "hook-writer.md"), out)
        self.assertIn("NOT moved (1)", out)
        self.assertIn(os.path.join(agents, "meeting-prep.md") + ": denied", out)
        self.assertNotIn("listed above", out)
        self.assertTrue(os.path.islink(os.path.join(agents, "meeting-prep.md")))


    # (8) v1's install record moves last, and only once every other move has succeeded
    def test_install_record_stays_until_everything_else_moved(self):
        m = load(MIGRATE, "remove_v1_hooks_marker")
        agents = os.path.join(self.home, "agents")
        os.makedirs(agents)
        gone = os.path.join(self.home, "deleted-clone")  # dangling link, known only through the record root
        link = os.path.join(agents, "lead-prioritizer.md")
        os.symlink(os.path.join(gone, "agents", "lead-prioritizer.md"), link)
        marker = os.path.join(self.home, ".gtm-installed.json")
        with open(marker, "w") as f:
            json.dump({"root": gone, "skills": [], "agents": ["lead-prioritizer.md"], "commands": []}, f)
        real_move = shutil.move

        def flaky(src, dst):
            if src == link:
                raise PermissionError("denied")
            return real_move(src, dst)

        with mock.patch.object(m.shutil, "move", side_effect=flaky):
            code, out = self.run_in_process(m, "--apply", "--move-copies")
        self.assertEqual(code, 3)
        self.assertTrue(os.path.exists(marker), "the record must stay while a recorded link is still in place")
        self.assertTrue(os.path.islink(link))
        self.assertIn(marker + ": kept", out)
        self.assertIn("NOT moved (2)", out)

        code, out = self.run_in_process(m, "--apply", "--move-copies")  # the cause is fixed: run it again
        self.assertEqual(code, 0, out)
        self.assertFalse(os.path.lexists(link))
        self.assertFalse(os.path.exists(marker))
        self.assertIn("moved " + link, out)
        self.assertIn("moved " + marker, out)


if __name__ == "__main__":
    unittest.main()
