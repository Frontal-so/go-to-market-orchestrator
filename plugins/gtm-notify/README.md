# gtm-notify

Sends a short ping to Slack, Discord or any webhook when Claude finishes a turn, stops on an error, or is waiting for you. The ping carries Claude's actual last message (trimmed), so you can tell from your phone whether the list is scored or Claude is stuck on a permission prompt.

## Setup

1. Install: `claude plugin install gtm-notify@frontal-gtm`.
2. Give it at least one URL, when you enable it or later in `/plugin` (open the plugin and choose its options). From a terminal, pipe a JSON object to `claude plugin configure gtm-notify@frontal-gtm --values-stdin`; running it without the flag shows the options and which are unset:
   - **Slack**: create an incoming webhook for a channel (Slack: Apps, Incoming Webhooks, Add to channel).
   - **Discord**: channel settings, Integrations, Webhooks, New webhook, copy URL.
   - **Any other webhook** (Zapier, n8n, Make, Clay webhook table): receives the JSON below.
3. URLs are stored as sensitive values. With no URL set, the plugin does nothing.

| Option | Default | What it does |
|---|---|---|
| `slack_webhook_url` | empty | Slack incoming webhook. |
| `discord_webhook_url` | empty | Discord webhook. |
| `webhook_url` | empty | Any HTTPS endpoint. |
| `ping_on_stop` | on | Off: ping only when Claude is waiting for you or stopped on an error, not after every turn. |
| `max_chars` | 500 | How much of Claude's message goes in the ping (0 to 3000). 0 sends only the project and event. |

## When it fires

- **Stop**: Claude finished a turn. Uses the `last_assistant_message` field Claude Code sends (falls back to the last assistant text in the last 1 MB of the transcript on older versions). When another Stop hook made Claude continue, it pings again at each stop, so the latest ping matches the latest stop. If Claude Code reports background tasks or scheduled wakeups (`/loop`, cron tasks) still pending, the headline says "Claude paused in <project>, with 2 background tasks still pending" instead of "finished", and the JSON carries the counts (never the task descriptions or commands).
- **StopFailure**: the turn ended on an API error (rate limit, authentication, billing, server error and so on). The headline is "Claude stopped with an error in <project>", and the message is the error text Claude Code shows. Sent even when `ping_on_stop` is off.
- **Notification**: `permission_prompt`, `idle_prompt`, `elicitation_dialog`, `elicitation_url_dialog` (an MCP server wants you to open a link, for example to sign in) and `agent_needs_input`.

All three run with `async: true`, so the ping never slows Claude down, and a failed ping never fails your session. Claude Code does not enforce a hook timeout on async hooks, so the hooks set none: the limit that applies is notify.py's own, 6 seconds per request and 10 seconds for all targets together. Delivery is best effort, and a short `claude -p` run can exit before an async ping is sent. Errors go to `notify.log` in the plugin's data folder as the target and the HTTP status only; response bodies are never logged.

## Webhook JSON

```json
{
  "source": "claude-code",
  "event": "stop",
  "notification_type": null,
  "project": "northwind-outbound",
  "session_id": "…",
  "headline": "Claude finished in northwind-outbound",
  "error": null,
  "pending": { "background_tasks": 0, "session_crons": 0 },
  "message": "Scored 40 accounts. 6 are Tier 1, saved to output/scored.csv.",
  "timestamp": "2026-11-25T14:02:11+00:00"
}
```

`event` is `stop`, `stop_failure` or `notification`. `error` is the API error type on `stop_failure` (for example `rate_limit`) and null otherwise. `pending` is set on `stop` and null otherwise. `project` is the folder name only, never the full path, but the folder name itself is sent: if it names a client or a deal, rename the folder or set up the ping in a project whose name you are happy to share.

## Privacy

- Only the fields above are sent. No transcript file, file contents or tool payload is attached. But `message` is Claude's last message (up to `max_chars`), and whatever Claude wrote there goes to the webhook: if it quoted a file, a customer record or a tool result, that text is sent too.
- Before sending, anything that looks like a credential (API keys like `sk-...`, Slack tokens, GitHub tokens, AWS access key IDs, bearer tokens, Slack and Discord webhook URLs, and labelled secrets: a name with SECRET, TOKEN, PASSWORD, API_KEY, PRIVATE_KEY or ACCESS_KEY followed by `=` or `:`, such as `AWS_SECRET_ACCESS_KEY=...`) is replaced with `[redacted]`. The patterns catch common shapes (also JWTs, Basic auth, GitLab, Stripe, Google API, npm and Twilio keys, Zapier, Make and n8n hook URLs, Discord canary and PTB webhook URLs, `api_key=` or `token=` in URLs, `secret: ...` style pairs and private key blocks), and redaction runs before the message is trimmed. It is still pattern matching, not a guarantee: if your messages may contain customer data, set `max_chars` to 0.
- Only `https://` URLs to a public host are accepted: private, loopback and link-local IP addresses and names ending in `.local`, `.internal` or `.localhost` are refused (names are not looked up in DNS). The one exception is `http://localhost` and `http://127.0.0.1`, for local testing.
- Redirects are not followed: if a webhook answers with a 3xx, the ping is not sent on, and only the status code is logged.
- Discord pings have mentions turned off, so a message containing `@everyone` pings nobody.

## Without the plugin

`scripts/notify.py` also reads `SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL`, `GTM_WEBHOOK_URL`, `GTM_NOTIFY_PING_ON_STOP` and `GTM_NOTIFY_MAX_CHARS`, so you can wire it by hand (`python3 /path/to/notify.py stop` on Stop, `... stop_failure` on StopFailure, `... notification` on Notification). `GTM_NOTIFY_DRY_RUN=1` prints the requests instead of sending them. Python 3.9+, standard library only.
