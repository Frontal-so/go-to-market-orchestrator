# gtm-guard

A best-effort check that makes Claude stop and ask before calls that look like something you cannot take back in your sales tools. It matches known tool names and API hosts, so treat it as a safety net, not a guarantee:

| Category | Examples of tool calls it catches |
|---|---|
| Send | `send_email`, `reply_to_thread`, `activate_campaign`, `enable_campaign`, `resume_sequence`, `dispatch_message`, `post_tweet`, `queue_post`, `add_leads_to_campaign` and `add_to_sequence` (adding someone can start emails), `schedule_draft` on a social publisher such as Typefully (scheduling is the go-live step there) |
| Spend | `people_enrichment`, `reveal_phone`, `verify_email`, `find_email`, `email_finder`, `lookup_email` (credits) |
| Write | `create_contact`, `update_deal`, `upsert_company`, `bulk_import` (CRM and sequencer records) |
| Delete | `delete_lead`, `archive_record`, `remove_contact` |

Reads (`get_`, `list_`, `search_`, ...) usually pass straight through, including `get_reply_status`, `list_posts` and report names such as `get_send_status` or `list_archive_records`, and so does every tool that is not a sales tool. For those, Claude Code's normal permission rules apply. A read-looking name that still holds an action word in another place (`get_or_create_contact`, `search_and_send`) asks, and so does a paid email or phone lookup, because the guard errs toward asking.

Generic API tools that reach any endpoint, such as lemlist's `call_api` (lemlist: "anything outside your bucket stays reachable through `call_api`", developer.lemlist.com/mcp/setup), are judged by the HTTP method in the call: `GET`, `HEAD` and `OPTIONS` pass, `DELETE` is a delete, `POST`, `PUT` and `PATCH` are writes (a send when the path starts or resumes a campaign, or, on a sequencer, a `POST` adds leads or contacts into a campaign or sequence, meaning the path ends at its `leads` part, optionally followed by `add`, `bulk`, `batch`, `import` or one id; updating or searching leads is a write that asks), and a call with no method it can read asks.

It asks **even if you allowed the tool before**: a PreToolUse hook that returns `ask` shows the permission prompt again for that one call, with a line saying what the call does and how big the lists in it are ("Lists in this call: leads: 1,240 items").

## Install

```
/plugin marketplace add Frontal-so/go-to-market-orchestrator
/plugin install gtm-guard@frontal-gtm
```

or, in a terminal, `claude plugin marketplace add Frontal-so/go-to-market-orchestrator`, then `claude plugin install gtm-guard@frontal-gtm`. Install it before you connect any sales tool's MCP server.

## What it looks at

1. **MCP tools** of sales tools. A tool is checked when its server name contains a known token: `apollo`, `attio`, `hubspot`, `salesforce`, `pipedrive`, `close`, `instantly`, `lemlist` (and `lm`: lemlist's developer page, developer.lemlist.com/mcp/setup, names the server `lm` for OAuth, while its help center article names it `lemlist`; both are caught), `smartlead`, `heyreach`, `outreach`, `salesloft`, `clay`, `fullenrich`, `typefully` and others (full list at the top of `scripts/guard.py`). This covers servers you added yourself (`mcp__apollo__...`), Claude's built-in connectors (`mcp__claude_ai_HubSpot__...`) and plugin servers (`mcp__plugin_x_lemlist__...`).
2. **Bash and PowerShell commands** that call a sales tool's REST API with a write method: `curl -X POST https://api.instantly.ai/...`, `curl -d ...`, `wget --method=POST`, `requests.post(...)`, `fetch(..., {method: "POST"})`, `Invoke-RestMethod -Method Post`, HTTPie, Ruby `Net::HTTP`, to the hosts listed in `GTM_API_HOSTS` (whole host names, so lookalike domains do not match). The method is not tied to its URL: a command that names a sales-tool host anywhere and a write method anywhere asks, which errs toward asking in multi-line scripts. A method it cannot read (`-X "$METHOD"`, `wget --method=$M`, `{method: process.env.M}`, `{method}`, `"method": m`, `requests.request(m, url)`, PowerShell `@{Method=$env:M}`) or curl options from a config file (`curl -K file`) on a sales-tool host count as a write, and so does a body sent with `--form-string`. On a sequencer's API host, a `POST` that adds leads into a campaign (the same path rule as above) is a send. A command that only prints text (`echo`, `printf`, or `python3 -c 'print("...")'` of one plain string) is not a call.

   Known limits: it reads the command text, so a request built in an unusual way (a method or body assembled across several lines, an alias, a client it does not know) can pass without a question. `-d` counts as a body for every client, so `wget -d` (debug) and `http -d` (download) also ask.

Named your server something else (`acme-crm`, `outbound-prod`)? Add it under **Extra MCP server names to guard**. The name also matches when it is a whole part of a longer server name, so `acme-crm` covers `mcp__plugin_x_acme-crm__...` and `mcp__claude_ai_Acme_CRM__...`. An extra server whose name says sequencer, sequence, campaign, cadence, outbound or outreach is treated as a sequencer, so adding leads on it counts as a send.

## Settings

Set them when you enable the plugin, or later in `/plugin` (open the plugin and choose its options). From a terminal, `claude plugin configure gtm-guard@frontal-gtm` shows them and `claude plugin configure gtm-guard@frontal-gtm --values-stdin` saves a JSON object you pipe in, for example `echo '{"mode":"block-sends"}' | claude plugin configure gtm-guard@frontal-gtm --values-stdin`.

| Option | Default | What it does |
|---|---|---|
| `mode` | `ask` | `ask`: every risky call asks. `block-sends`: sends, launches and deletes are refused outright (Claude is told to show you the call so you can run it yourself); writes and credit spends still ask. |
| `extra_servers` | empty | Comma-separated server names to treat as sales tools. |
| `log_calls` | on | Appends one JSON line per guarded call to `guard-log.jsonl` in the plugin's data folder (`$CLAUDE_PLUGIN_DATA`): time, session id, project folder name, tool, target (server or API host), category, decision, input field names (identifier-like keys only, at most 50), list sizes (also one level down, such as `request.leads`), and a count of the other fields; for a generic API tool such as `call_api`, also the HTTP method and the path without its query string, keeping only route words such as `api`, `v3`, `campaigns`, `leads` or `start`, and never the part right after a collection noun, which is an id slot (`/campaigns/launch` logs `/campaigns/*`); every other part (a name, a slug, an id, an email, a number) is shown as `*`. The method is logged only when it is an HTTP method name, otherwise as `unknown`. Bodies, field values and path values are never logged. Key names are, so if one of your tools uses a person's or customer's name as a key, that name can land in the log. The log is capped at 5 MB: it then becomes `guard-log.1.jsonl` (one old file is kept) and a new one starts. The size check, the rotation and the append run under one lock (`guard-log.lock`), so two calls at once cannot lose the old file; if the lock is busy for more than half a second, the line is skipped so the call is never held up. |

## Limits (read these)

- **It is a seatbelt, not a sandbox.** It reads tool names and command text. A script that calls an API from inside its own code (`python3 push_leads.py`) is not caught. Neither is a command whose host sits in a variable (`curl -X POST "$HUBSPOT_BASE/crm/v3/objects/contacts"`), a URL built at run time, or a sales tool whose MCP tool names do not use the usual verbs.
- **Some reads ask too.** Read-only endpoints that use POST, such as CRM search APIs and GraphQL queries, are treated as writes and ask. A command that only prints text (`echo 'curl -X POST ...'`) does not ask; anything chained, piped or substituted after it does.
- **Bypass-permissions mode.** Tested on 2026-11-25 with Claude Code 2.1.332 in headless mode (`claude -p --permission-mode bypassPermissions`): a hook `deny` blocked the call, and a hook `ask` also blocked it, because a headless run has nobody to ask. We did not test an interactive session in bypass mode, so do not rely on `ask` there; use `mode: block-sends` if you run with bypass on.
- The word lists are heuristics. If a tool is classified wrongly, open an issue with the tool name.

## Without the plugin

The script reads plain environment variables too (`GTM_GUARD_MODE`, `GTM_GUARD_EXTRA_SERVERS`, `GTM_GUARD_LOG`), so you can wire it by hand in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "mcp__.*", "hooks": [{ "type": "command", "command": "python3 /path/to/guard.py", "timeout": 10 }] },
      { "matcher": "Bash|PowerShell", "hooks": [{ "type": "command", "command": "python3 /path/to/guard.py", "timeout": 10 }] }
    ]
  }
}
```

Python 3.9+, standard library only. It fails open: on any internal error it writes a one-line note to stderr (`gtm-guard: internal error ...`), prints no decision and exits 0, so a guard bug never blocks your session, and a crash lets the call through to the normal permission rules. A fail-closed guard would block every MCP call whenever it had a bug, which is why we chose this.
