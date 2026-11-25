import http.server
import json
import os
import tempfile
import threading
import unittest
from unittest import mock

from helpers import NOTIFY, load, run_script

HOOKS_JSON = os.path.join(os.path.dirname(NOTIFY), "..", "hooks", "hooks.json")

notify = load(NOTIFY, "notify")

STOP = {"session_id": "s1", "cwd": "/Users/someone/clients/northwind", "hook_event_name": "Stop",
        "stop_hook_active": False, "last_assistant_message": "Scored 40 accounts. 6 are Tier 1."}


class BuildEvent(unittest.TestCase):
    def test_stop_uses_the_real_last_message(self):
        event = notify.build_event("stop", STOP, 500)
        self.assertEqual(event["headline"], "Claude finished in northwind")
        self.assertEqual(event["message"], "Scored 40 accounts. 6 are Tier 1.")
        self.assertNotIn("cwd", event)  # the full path can hold the user's name
        self.assertNotIn("/Users/someone", json.dumps(event))

    def test_stop_after_a_continuation_still_pings(self):
        self.assertIsNotNone(notify.build_event("stop", dict(STOP, stop_hook_active=True), 500))

    def test_a_key_cut_by_the_length_limit_is_still_redacted(self):
        secret = "sk-" + "b" * 40
        text = "x" * 90 + " " + secret
        message = notify.build_event("stop", dict(STOP, last_assistant_message=text), 110)["message"]
        self.assertNotIn("bbbb", message)

    def test_more_secret_shapes(self):
        jwt = "eyJ" + "a" * 20 + "." + "b" * 20 + "." + "c" * 10
        text = (f"jwt {jwt} url https://x.example/api?api_key=abcd1234efgh&x=1 "
                "header Basic " + "Q" * 20 + " cfg password: hunter2hunter2")
        message = notify.build_event("stop", dict(STOP, last_assistant_message=text), 3000)["message"]
        for leaked in ("aaaa", "abcd1234", "QQQQ", "hunter2"):
            self.assertNotIn(leaked, message)

    def test_transcript_fallback(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "first"}]}}) + "\n")
            f.write("not json\n")
            f.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Read"}, {"type": "text", "text": "second"}]}}) + "\n")
        try:
            payload = {k: v for k, v in STOP.items() if k != "last_assistant_message"}
            payload["transcript_path"] = f.name
            self.assertEqual(notify.build_event("stop", payload, 500)["message"], "second")
        finally:
            os.unlink(f.name)

    def test_newer_secret_shapes(self):
        samples = {
            "gitlab": "glpat-" + "g" * 20,
            "stripe live": "sk_live_" + "s" * 24,
            "stripe restricted": "rk_live_" + "r" * 24,
            "stripe test": "sk_test_" + "t" * 24,
            "google": "AIza" + "G" * 35,
            "npm": "npm_" + "n" * 36,
            "twilio": "SK" + "0123456789abcdef" * 2,
            "discord canary": "https://canary.discord.com/api/webhooks/1/" + "d" * 12,
            "discord ptb": "https://ptb.discord.com/api/webhooks/1/" + "p" * 12,
            "make": "https://hook.eu1.make.com/" + "m" * 20,
            "n8n": "https://acme.app.n8n.cloud/webhook/" + "w" * 20,
            "n8n test": "https://n8n.acme.example/webhook-test/" + "v" * 20,
        }
        for name, secret in samples.items():
            message = notify.build_event("stop", dict(STOP, last_assistant_message=f"see {secret} ok"), 3000)["message"]
            self.assertNotIn(secret, message, name)
            self.assertIn("[redacted]", message, name)

    def test_labelled_secrets_are_masked(self):
        value = "A1b2C3d4" * 5  # 40 characters, the length of an AWS secret access key
        samples = {
            "aws env": f"AWS_SECRET_ACCESS_KEY={value}",
            "aws ini": f"aws_secret_access_key = {value}",
            "aws json": f'"SecretAccessKey": "{value}"',
            "session env": f"AWS_SESSION_TOKEN={value}",
            "session ini": f"aws_session_token = {value}",
            "private key": f"PRIVATE_KEY: {value}",
            "db password": f"DB_PASSWORD={value}",
        }
        for name, text in samples.items():
            message = notify.build_event("stop", dict(STOP, last_assistant_message=f"set {text} then retry"), 3000)["message"]
            self.assertNotIn(value, message, name)
            self.assertIn("[redacted]", message, name)

    def test_prose_is_not_masked(self):
        for text in ("The token budget is 500 per run.",
                     "Reset the password before Friday and tell the secret santa group.",
                     "We send 40 emails a day from the access list."):
            message = notify.build_event("stop", dict(STOP, last_assistant_message=text), 3000)["message"]
            self.assertEqual(message, text)

    def test_long_blob_redacts_quickly(self):
        import time
        blob = ("a_" * 200000) + "x"
        start = time.monotonic()
        notify.redact(blob)
        self.assertLess(time.monotonic() - start, 2.0)

    def test_url_dialog_has_its_own_label(self):
        event = notify.build_event("notification", {"cwd": "/x/northwind",
                                                    "notification_type": "elicitation_url_dialog"}, 500)
        self.assertEqual(event["headline"], "Claude needs you to open a link in northwind")

    def test_stop_failure_names_the_error(self):
        event = notify.build_event("stop_failure", {
            "cwd": "/x/northwind", "hook_event_name": "StopFailure", "error": "rate_limit",
            "error_details": "429 Too Many Requests", "last_assistant_message": "API Error: Rate limit reached"}, 500)
        self.assertEqual(event["event"], "stop_failure")
        self.assertEqual(event["headline"], "Claude stopped with an error in northwind")
        self.assertEqual(event["error"], "rate_limit")
        self.assertEqual(event["message"], "API Error: Rate limit reached")

    def test_stop_with_work_still_running_says_paused(self):
        payload = dict(STOP, background_tasks=[{"id": "t1", "type": "shell", "command": "secret-cmd"},
                                               {"id": "t2", "type": "subagent"}],
                       session_crons=[{"id": "c1", "schedule": "0 9 * * 1"}])
        event = notify.build_event("stop", payload, 500)
        self.assertEqual(event["headline"],
                         "Claude paused in northwind, with 2 background tasks and 1 scheduled wakeup still pending")
        self.assertEqual(event["pending"], {"background_tasks": 2, "session_crons": 1})
        self.assertNotIn("secret-cmd", json.dumps(event))  # counts only, never commands

    def test_stop_with_empty_arrays_says_finished(self):
        event = notify.build_event("stop", dict(STOP, background_tasks=[], session_crons=[]), 500)
        self.assertEqual(event["headline"], "Claude finished in northwind")
        self.assertEqual(event["pending"], {"background_tasks": 0, "session_crons": 0})

    def test_transcript_fallback_reads_only_the_tail(self):
        filler = json.dumps({"type": "user", "message": {"content": "z" * 1000}}) + "\n"
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"type": "assistant", "message": {"content": "early"}}) + "\n")
            f.write(filler * 1100)  # about 1.1 MB, pushes "early" out of the window
            f.write("[1, 2]\n")  # valid JSON that is not an object
        try:
            self.assertEqual(notify.last_assistant_text_from_transcript(f.name), "")
            with open(f.name, "a") as g:
                g.write(json.dumps({"type": "assistant", "message": {"content": "late"}}) + "\n")
            self.assertEqual(notify.last_assistant_text_from_transcript(f.name), "late")
        finally:
            os.unlink(f.name)

    def test_notification_labels(self):
        event = notify.build_event("notification", {
            "cwd": "/x/northwind", "notification_type": "permission_prompt",
            "message": "Claude needs your permission to use Bash"}, 500)
        self.assertEqual(event["headline"], "Claude needs your permission in northwind")
        self.assertEqual(event["message"], "Claude needs your permission to use Bash")

    def test_max_chars(self):
        long = dict(STOP, last_assistant_message="word " * 400)
        message = notify.build_event("stop", long, 100)["message"]
        self.assertLessEqual(len(message), 102)
        self.assertTrue(message.endswith("…"))
        self.assertEqual(notify.build_event("stop", STOP, 0)["message"], "")

    def test_secrets_are_redacted(self):
        text = ("key sk-" + "a" * 20 + " hook https://hooks.slack.com/services/T0/B0/xyz "
                "token xox" + "b-1234567890-abcdef")
        event = notify.build_event("stop", dict(STOP, last_assistant_message=text), 3000)
        self.assertNotIn("sk-abc", event["message"])
        self.assertNotIn("hooks.slack.com", event["message"])
        self.assertNotIn("xoxb-", event["message"])


class Bodies(unittest.TestCase):
    def test_slack_escapes_and_quotes(self):
        event = notify.build_event("stop", dict(STOP, last_assistant_message="<b> & c\nline 2"), 500)
        body = notify.slack_body(event)
        self.assertIn("&lt;b&gt; &amp; c", body["text"])
        self.assertIn("> line 2", body["text"])
        self.assertFalse(body["unfurl_links"])

    def test_discord_never_pings_everyone(self):
        event = notify.build_event("stop", dict(STOP, last_assistant_message="@everyone " + "x" * 3000), 3000)
        body = notify.discord_body(event)
        self.assertEqual(body["allowed_mentions"], {"parse": []})
        self.assertLessEqual(len(body["content"]), 2000)

    def test_only_https_or_localhost(self):
        self.assertTrue(notify.url_is_allowed("https://hooks.slack.com/services/x"))
        self.assertTrue(notify.url_is_allowed("http://localhost:5678/webhook/x"))
        self.assertFalse(notify.url_is_allowed("http://example.com/hook"))
        self.assertFalse(notify.url_is_allowed("file:///etc/passwd"))

    def test_private_hosts_are_refused(self):
        for url in ("https://10.0.0.5/hook", "https://192.168.1.20/hook", "https://127.0.0.1/hook",
                    "https://169.254.169.254/latest", "https://[::1]/hook", "https://[fe80::1]/hook",
                    "https://printer.local/hook", "https://db.internal/hook", "https://localhost/hook",
                    "https://0.0.0.0/hook", "https:///nohost"):
            self.assertFalse(notify.url_is_allowed(url), url)
        self.assertTrue(notify.url_is_allowed("https://hooks.zapier.com/hooks/catch/1/x"))
        self.assertTrue(notify.url_is_allowed("https://8.8.8.8/hook"))
        self.assertTrue(notify.url_is_allowed("http://127.0.0.1:8080/test"))  # local testing


class Hooks(unittest.TestCase):
    def setUp(self):
        with open(HOOKS_JSON, encoding="utf-8") as f:
            self.hooks = json.load(f)["hooks"]

    def test_async_hooks_carry_no_timeout(self):
        for event, groups in self.hooks.items():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertTrue(hook.get("async"), event)
                    self.assertNotIn("timeout", hook, event)

    def test_stop_failure_and_url_dialogs_are_registered(self):
        self.assertIn("stop_failure", self.hooks["StopFailure"][0]["hooks"][0]["command"])
        matcher = self.hooks["Notification"][0]["matcher"].split("|")
        self.assertIn("elicitation_url_dialog", matcher)
        for kind in matcher:
            self.assertIn(kind, notify._NOTIFICATION_LABELS)


class NoRedirects(unittest.TestCase):
    def test_a_redirect_is_not_followed(self):
        hits = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                hits.append(self.path)
                self.send_response(302 if self.path == "/hook" else 200)
                if self.path == "/hook":
                    self.send_header("Location", "/elsewhere")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_GET(self):
                self.do_POST()

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as data, \
                    mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": data}), \
                    mock.patch("sys.stderr"):
                os.environ.pop("GTM_NOTIFY_DRY_RUN", None)
                notify.post_json(f"http://127.0.0.1:{server.server_port}/hook", {"text": "hi"}, "webhook")
                with open(os.path.join(data, "notify.log"), encoding="utf-8") as f:
                    logged = f.read()
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(hits, ["/hook"])
        self.assertIn("webhook: HTTP 302", logged)


class EndToEnd(unittest.TestCase):
    def run_notify(self, kind, payload, **env):
        with tempfile.TemporaryDirectory() as data:
            return run_script(NOTIFY, json.dumps(payload), [kind], GTM_NOTIFY_DRY_RUN="1",
                              CLAUDE_PLUGIN_DATA=data, **env)

    def sent(self, result):
        return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]

    def test_nothing_configured_is_silent(self):
        result = self.run_notify("stop", STOP)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_each_configured_target_gets_one_request(self):
        result = self.run_notify("stop", STOP,
                                 CLAUDE_PLUGIN_OPTION_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T/B/x",
                                 CLAUDE_PLUGIN_OPTION_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1/x",
                                 CLAUDE_PLUGIN_OPTION_WEBHOOK_URL="https://hooks.zapier.com/hooks/catch/1/x")
        sent = {item["target"]: item["body"] for item in self.sent(result)}
        self.assertEqual(set(sent), {"slack", "discord", "webhook"})
        self.assertIn("Scored 40 accounts", sent["slack"]["text"])
        self.assertIn("Scored 40 accounts", sent["discord"]["content"])
        self.assertEqual(sent["webhook"]["event"], "stop")
        self.assertEqual(sent["webhook"]["project"], "northwind")

    def test_plain_env_vars_work_when_wired_by_hand(self):
        result = self.run_notify("stop", STOP, SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T/B/x")
        self.assertEqual([item["target"] for item in self.sent(result)], ["slack"])

    def test_ping_on_stop_off_still_sends_notifications(self):
        env = {"CLAUDE_PLUGIN_OPTION_SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/T/B/x",
               "CLAUDE_PLUGIN_OPTION_PING_ON_STOP": "false"}
        self.assertEqual(self.sent(self.run_notify("stop", STOP, **env)), [])
        sent = self.sent(self.run_notify("notification", {"cwd": "/x/y", "notification_type": "idle_prompt",
                                                          "message": "Claude is waiting for your input"}, **env))
        self.assertEqual(len(sent), 1)

    def test_stop_failure_pings_even_with_ping_on_stop_off(self):
        env = {"CLAUDE_PLUGIN_OPTION_SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/T/B/x",
               "CLAUDE_PLUGIN_OPTION_PING_ON_STOP": "false"}
        sent = self.sent(self.run_notify("stop_failure", {"cwd": "/x/northwind", "error": "server_error",
                                                          "last_assistant_message": "API Error: overloaded"}, **env))
        self.assertEqual(len(sent), 1)
        self.assertIn("stopped with an error", sent[0]["body"]["text"])

    def test_bad_input_never_fails(self):
        result = run_script(NOTIFY, "not json", ["stop"], GTM_NOTIFY_DRY_RUN="1",
                            SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T/B/x")
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
