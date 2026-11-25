#!/usr/bin/env python3
"""gtm-notify: send a short, real ping to Slack, Discord or any webhook.

Called by the plugin's hooks with one argument, the event kind:
    notify.py stop           (Stop hook: Claude finished a turn)
    notify.py stop_failure   (StopFailure hook: the turn ended on an API error)
    notify.py notification   (Notification hook: Claude is waiting for you)

Reads the hook's JSON from stdin. Standard library only: it needs Python 3.9+
as a `python3` command on PATH (macOS, Linux, or WSL on Windows) and nothing else.

Settings come from the plugin's options (Claude Code exports them as
CLAUDE_PLUGIN_OPTION_<KEY>) and fall back to plain environment variables
(SLACK_WEBHOOK_URL, DISCORD_WEBHOOK_URL, GTM_WEBHOOK_URL, ...), so the script
also works when wired by hand in settings.json.

It never blocks or fails Claude: every error is logged and the exit code is 0.
Set GTM_NOTIFY_DRY_RUN=1 to print the requests instead of sending them.
"""

from __future__ import annotations

import datetime as _dt
import ipaddress
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

TIMEOUT_SECONDS = 6
DEADLINE_SECONDS = 10  # all targets together; async hooks get no timeout from Claude Code
TRANSCRIPT_TAIL_BYTES = 1_000_000  # the fallback reads only the end of the transcript
USER_AGENT = "gtm-notify/2.0 (+https://github.com/Frontal-so/go-to-market-orchestrator)"

# Strings that look like credentials are masked before anything leaves the
# machine. Cheap insurance: Claude's last message sometimes echoes a key.
_SECRET_PATTERNS = [
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{16,}"), "[redacted]"),
    (re.compile(r"\bxox[abprse]-[A-Za-z0-9\-]{10,}"), "[redacted]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "[redacted]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "[redacted]"),
    (re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}"), "[redacted]"),  # GitLab
    (re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}"), "[redacted]"),  # Stripe
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"), "[redacted]"),  # Google API key
    (re.compile(r"\bnpm_[A-Za-z0-9]{30,}"), "[redacted]"),  # npm token
    (re.compile(r"\bSK[0-9a-fA-F]{32}\b"), "[redacted]"),  # Twilio API key
    (re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA)[0-9A-Z]{16}\b"), "[redacted]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{4,}"), "[redacted]"),  # JWT
    (re.compile(r"\b(Bearer|Basic|Token)\s+[A-Za-z0-9._~+/=\-]{12,}", re.IGNORECASE), r"\1 [redacted]"),
    (re.compile(r"https://hooks\.slack\.com/[A-Za-z0-9/_\-]+"), "[redacted]"),
    (re.compile(r"https://(?:(?:canary|ptb)\.)?(?:discord|discordapp)\.com/api/webhooks/[A-Za-z0-9/_\-]+"), "[redacted]"),
    (re.compile(r"https://hooks\.zapier\.com/hooks/catch/[A-Za-z0-9/_\-]+"), "[redacted]"),
    (re.compile(r"https://hook\.[A-Za-z0-9\-]+\.make\.com/[A-Za-z0-9/_\-]+"), "[redacted]"),  # Make
    (re.compile(r"https?://[^\s/]+/webhook(?:-test)?/[A-Za-z0-9/_\-]+"), "[redacted]"),  # n8n and similar
    # ?api_key=..., &token=..., user_api_key=... in any URL or text
    (re.compile(r"((?:api[_\-]?key|apikey|access[_\-]?token|auth[_\-]?token|token|secret|password|passwd|"
                r"signature|sig|user_api_key|client_secret)=)[^&\s'\"]{4,}", re.IGNORECASE), r"\1[redacted]"),
    # API_KEY: abc..., "secret": "abc..."
    (re.compile(r"((?:api[_\-]?key|secret|token|password|passwd|client[_\-]?secret)['\"]?\s*[:=]\s*['\"]?)"
                r"[A-Za-z0-9._~+/=\-]{8,}", re.IGNORECASE), r"\1[redacted]"),
    # Any labelled secret: a name that contains SECRET, TOKEN, PASSWORD, API_KEY,
    # PRIVATE_KEY or ACCESS_KEY, then = or :, then the value. Catches
    # AWS_SECRET_ACCESS_KEY=..., aws_session_token = ..., "SecretAccessKey": "...".
    # The name parts are bounded so a long blob cannot make the match slow.
    (re.compile(r"(\b[A-Za-z0-9_\-]{0,40}?(?:secret|token|password|passwd|api[_\-]?key|apikey|"
                r"private[_\-]?key|access[_\-]?key)[A-Za-z0-9_\-]{0,40}['\"]?\s*[:=]\s*['\"]?)"
                r"[A-Za-z0-9._~+/=\-]{8,}", re.IGNORECASE), r"\1[redacted]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)"), "[redacted]"),
]

_NOTIFICATION_LABELS = {
    "permission_prompt": "needs your permission",
    "idle_prompt": "is waiting for your input",
    "elicitation_dialog": "has a question for you",
    "elicitation_url_dialog": "needs you to open a link",
    "agent_needs_input": "needs your input",
}


# ── settings ────────────────────────────────────────────────────────────────

def option(key: str, fallback_env: Optional[str] = None, default: str = "") -> str:
    value = os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}", "")
    if not value and fallback_env:
        value = os.environ.get(fallback_env, "")
    return value.strip() or default


def option_bool(key: str, fallback_env: str, default: bool) -> bool:
    raw = option(key, fallback_env)
    if not raw:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def option_int(key: str, fallback_env: str, default: int, lo: int, hi: int) -> int:
    raw = option(key, fallback_env)
    try:
        value = int(float(raw)) if raw else default
    except ValueError:
        value = default
    return max(lo, min(hi, value))


def data_dir() -> str:
    path = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(
        os.path.expanduser("~"), ".claude", "gtm-notify"
    )
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
    return path


def log(line: str) -> None:
    stamp = _dt.datetime.now().isoformat(timespec="seconds")
    try:
        with open(os.path.join(data_dir(), "notify.log"), "a", encoding="utf-8") as f:
            f.write(f"{stamp} {line}\n")
    except OSError:
        pass
    print(f"gtm-notify: {line}", file=sys.stderr)


# ── message building ────────────────────────────────────────────────────────

def redact(text: str) -> str:
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def excerpt(text: str, max_chars: int) -> str:
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    if max_chars <= 0 or not text:
        return ""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    space = cut.rfind(" ")
    if space > max_chars * 0.6:
        cut = cut[:space]
    return cut.rstrip() + " …"


def last_assistant_text_from_transcript(path: str) -> str:
    """Fallback for Claude Code versions that do not send last_assistant_message."""
    if not path or not os.path.isfile(path):
        return ""
    last = ""
    try:
        with open(path, "rb") as f:
            size = os.fstat(f.fileno()).st_size
            start = max(0, size - TRANSCRIPT_TAIL_BYTES)
            f.seek(start)
            lines = f.read().decode("utf-8", errors="replace").splitlines()
        if start > 0 and lines:
            lines = lines[1:]  # the first line is cut mid-way
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict) or entry.get("type") != "assistant":
                continue
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str):
                texts = [content]
            elif isinstance(content, list):
                texts = [c.get("text", "") for c in content
                         if isinstance(c, dict) and c.get("type") == "text"]
            else:
                texts = []
            joined = "\n".join(t for t in texts if t).strip()
            if joined:
                last = joined
    except OSError:
        return ""
    return last


def build_event(kind: str, payload: dict, max_chars: int) -> Optional[dict]:
    """Return a neutral event dict, or None when nothing should be sent."""
    cwd = payload.get("cwd") or os.getcwd()
    project = os.path.basename(os.path.normpath(cwd)) or cwd

    pending = None
    error = None
    if kind == "stop":
        # stop_hook_active means this stop comes after a continuation another Stop
        # hook asked for. We still ping, so the latest ping matches the latest stop.
        # Whether work is still running is read from background_tasks and session_crons.
        text = payload.get("last_assistant_message")
        if not isinstance(text, str):
            text = last_assistant_text_from_transcript(payload.get("transcript_path", ""))
        tasks = payload.get("background_tasks")
        crons = payload.get("session_crons")
        pending = {"background_tasks": len(tasks) if isinstance(tasks, list) else 0,
                   "session_crons": len(crons) if isinstance(crons, list) else 0}
        parts = []
        if pending["background_tasks"]:
            n = pending["background_tasks"]
            parts.append(f"{n} background task{'s' if n != 1 else ''}")
        if pending["session_crons"]:
            n = pending["session_crons"]
            parts.append(f"{n} scheduled wakeup{'s' if n != 1 else ''}")
        if parts:
            headline = f"Claude paused in {project}, with {' and '.join(parts)} still pending"
        else:
            headline = f"Claude finished in {project}"
        notification_type = None
    elif kind == "stop_failure":
        # last_assistant_message holds the API error text here, not Claude's reply
        error = payload.get("error") or "unknown"
        text = payload.get("last_assistant_message") or payload.get("error_details") or error
        headline = f"Claude stopped with an error in {project}"
        notification_type = None
    elif kind == "notification":
        notification_type = payload.get("notification_type") or ""
        label = _NOTIFICATION_LABELS.get(notification_type, "needs you")
        headline = f"Claude {label} in {project}"
        text = payload.get("message") or payload.get("title") or ""
    else:
        return None

    return {
        "source": "claude-code",
        "event": kind,
        "notification_type": notification_type,
        "project": project,  # folder name only: the full path can contain your user name
        "session_id": payload.get("session_id"),
        "headline": headline,
        "error": error,  # API error type, only for stop_failure
        "pending": pending,  # counts only, never task descriptions or commands
        "message": excerpt(redact(text if isinstance(text, str) else ""), max_chars),  # redact first: a cut key would slip past
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }


def slack_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slack_body(event: dict) -> dict:
    headline = slack_escape(event["headline"])
    text = f"*{headline}*"
    if event["message"]:
        quoted = "\n".join("> " + line if line else ">" for line in
                           slack_escape(event["message"]).splitlines())
        text += "\n" + quoted
    return {"text": text, "unfurl_links": False, "unfurl_media": False}


def discord_body(event: dict) -> dict:
    content = f"**{event['headline']}**"
    if event["message"]:
        content += "\n" + "\n".join("> " + line for line in event["message"].splitlines())
    # allowed_mentions with an empty parse list stops @everyone / @here / role pings
    return {"content": content[:2000], "allowed_mentions": {"parse": []}}


# ── sending ─────────────────────────────────────────────────────────────────

_PRIVATE_SUFFIXES = (".local", ".internal", ".localhost")


def host_is_private(host: str) -> bool:
    """True for loopback, private, link-local and similar IP literals, and for
    names like printer.local or db.internal. Names are not resolved."""
    host = (host or "").lower().rstrip(".")
    if not host or host == "localhost" or host.endswith(_PRIVATE_SUFFIXES):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
            or ip.is_unspecified or ip.is_multicast)


def url_is_allowed(url: str) -> bool:
    if re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?/", url):
        return True  # local testing only
    if not url.startswith("https://"):
        return False
    try:
        host = urllib.parse.urlsplit(url).hostname
    except ValueError:
        return False
    return not host_is_private(host)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A webhook that answers with a redirect is not followed: the ping goes
    only to the URL you configured, and the 3xx status is logged."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def post_json(url: str, body: dict, label: str) -> None:
    if not url_is_allowed(url):
        log(f"{label}: skipped, the URL must be https:// to a public host")
        return
    if os.environ.get("GTM_NOTIFY_DRY_RUN"):
        print(json.dumps({"target": label, "body": body}, ensure_ascii=False))
        return
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with _OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status >= 300:
                log(f"{label}: HTTP {response.status}")
    except urllib.error.HTTPError as e:
        log(f"{label}: HTTP {e.code}")  # never the body: a server can echo anything back
    except (urllib.error.URLError, OSError) as e:
        log(f"{label}: {type(e).__name__}")


def main(argv: list) -> int:
    kind = argv[1] if len(argv) > 1 else ""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        payload = {}

    if kind == "stop" and not option_bool("ping_on_stop", "GTM_NOTIFY_PING_ON_STOP", True):
        return 0

    targets = {
        "slack": option("slack_webhook_url", "SLACK_WEBHOOK_URL"),
        "discord": option("discord_webhook_url", "DISCORD_WEBHOOK_URL"),
        "webhook": option("webhook_url", "GTM_WEBHOOK_URL"),
    }
    if not any(targets.values()):
        return 0  # nothing configured: stay silent

    max_chars = option_int("max_chars", "GTM_NOTIFY_MAX_CHARS", 500, 0, 3000)
    event = build_event(kind, payload, max_chars)
    if event is None:
        return 0

    jobs = []
    if targets["slack"]:
        jobs.append((targets["slack"], slack_body(event), "slack"))
    if targets["discord"]:
        jobs.append((targets["discord"], discord_body(event), "discord"))
    if targets["webhook"]:
        jobs.append((targets["webhook"], event, "webhook"))
    send_all(jobs)
    return 0


def send_all(jobs: list) -> None:
    """Send to every target at once and give up after DEADLINE_SECONDS in total."""
    if len(jobs) == 1 or os.environ.get("GTM_NOTIFY_DRY_RUN"):
        for job in jobs:
            post_json(*job)
        return
    threads = [threading.Thread(target=post_json, args=job, daemon=True) for job in jobs]
    for t in threads:
        t.start()
    stop_at = time.monotonic() + DEADLINE_SECONDS
    for t in threads:
        t.join(max(0.0, stop_at - time.monotonic()))
    for t, job in zip(threads, jobs):
        if t.is_alive():
            log(f"{job[2]}: gave up after {DEADLINE_SECONDS}s")


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:  # never break the user's session over a ping
        log(f"unexpected error: {e!r}")
        sys.exit(0)
