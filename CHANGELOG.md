# Changelog

## 2.0.0 (2026-11-25)

A rewrite as a Claude Code plugin marketplace (`frontal-gtm`) with four plugins.

### Added
- `gtm-guard`: a best-effort check (a safety net, not a guarantee) that asks before sales-tool calls that look like sending, launching, spending credits, writing to a CRM or deleting, over MCP or direct API calls from Bash or PowerShell; optional `block-sends` mode; fails open on its own errors; local log of field names, list sizes, a count of other fields and, for generic API tools, the method and a path of route words only (other path parts shown as `*`); no bodies, field values or path values.
- `gtm-notify`: Slack, Discord and generic webhook pings on Stop (also after a continuation) and Notification, carrying Claude's real last message, with secret masking before trimming, best-effort async delivery with a 10 second deadline, HTTPS only, and response bodies never logged.
- `/gtm-outbound:gtm-context`: writes the project's GTM context from the v1 modules, templates and examples.
- `/gtm-content:gtm-content`: one skill over the 17 content prompts.
- `docs/mcp-servers.md`: setup for the official MCP servers of the common GTM tools.
- `scripts/remove-v1-hooks.py` and `docs/migrating-from-v1.md`.
- `scripts/remove-v1-hooks.py` moves a v1 copy only with evidence (v1's install record, an exact v1 file by sha256, or a link into a v1 clone).
- A "Your prospect data" section in the README; `.gitignore` now covers `input/`, `output/`, `data/` and `content/`.
- Unit tests for every script, structure tests for manifests and frontmatter, CI on pushes to main and on pull requests, pinned to Claude Code 2.1.332 (the version v2 was tested with). Python 3.9+.

### Changed
- `/outbound-pipeline` command is now the `/gtm-outbound:outbound-pipeline` skill (only runs when you call it) and spawns the plugin's subagents with the Agent tool.
- Every v1 skill, subagent, GTM context file and content prompt is written anew in our own words; the ideas and the pipeline design come from v1.
- Every skill and subagent: clearer trigger descriptions, `argument-hint`, drafts only, an explicit yes before anything is sent, enrolled, enriched or written to a CRM, source links and dates for every signal.
- Reply triage: a new unsubscribe category that goes to a suppression list, never to a nurture.
- Sequences and campaigns: current Google, Yahoo and Microsoft bulk-sender requirements and LinkedIn's limit on personalised invitation notes for free accounts, each with its source.
- All examples use fictional companies, people and `.example` domains.

### Removed
- The 30 hooks, the REST handlers in `orchestrator/` and the `.env` file: they sent empty data with the payloads Claude Code sends, ran on every tool call or turn, and several APIs they used are retired.
- `install.sh`, `uninstall.sh`, `sync-skills.sh` and `install-mcps.sh`: plugins replace them.
- The Slack approve and deny buttons and the Notion cost tracker.

### Review fixes before release
- `outbound-pipeline`: one stage at a time; Claude ends its turn after starting a stage and starts the next only after that stage's completion notice arrives and its file has rows, since Claude Code starts subagents in the background by default.
- `gtm-guard`: generic API tools such as lemlist's `call_api` are judged by their HTTP method; variable methods, `curl --config` and Ruby `Net::HTTP` writes now ask; a Python one-line print is not a call; read names such as `get_send_status` pass; one lock covers log rotation and append.
- `gtm-notify`: the privacy note now says Claude's last message is sent as written; labelled secrets (names with SECRET, TOKEN, PASSWORD, API_KEY and similar) are masked.
- `remove-v1-hooks.py`: v1's install record moves last, only after every other move succeeded.
- `campaign-builder`: credit costs are checked per vendor and action; `docs/mcp-servers.md`: Apollo's ban on model training and lemlist's `call_api`.

## 1.0.0 (2026-04-27)

First release.
