# Moving from v1 (April 2026) to v2

v1 was installed with `scripts/install.sh`, which copied skills, agents and a command into `~/.claude/` and merged up to 30 hooks into your **global** `~/.claude/settings.json`. Those hooks call `$CLAUDE_GTM_DIR/orchestrator/run.sh` and fire in every project, on every turn or every tool call, whether or not you are doing GTM work.

v2 is a set of plugins. Nothing is merged into your settings, and you can enable or remove each plugin on its own.

## 1. Remove the v1 hooks

From a clone of this repo:

```bash
python3 scripts/remove-v1-hooks.py            # dry run: lists what it would remove
python3 scripts/remove-v1-hooks.py --apply    # removes them, after a timestamped backup
```

It removes only hooks whose whole command is v1's own form, `bash "$CLAUDE_GTM_DIR/orchestrator/run.sh" <tool> <action>` (quoted or not, `$CLAUDE_GTM_DIR` or `${CLAUDE_GTM_DIR}`), and keeps every other hook as it was, including your own hooks that happen to mention the same words. It refuses to touch a settings file it cannot parse, edits a symlinked settings file where it really lives, and writes a backup with a unique name first; the backup and the new file keep the settings file's mode, so a `0600` file stays `0600`. The new file is written to an exclusive temporary file and swapped in. Right before the swap it reads the file once more and changes nothing if it was modified while it ran (close Claude Code and run it again); a write in the last microseconds before the swap would still be lost, and the backup holds the file as it was read. Commands it prints have tokens, webhook URLs and `key=value` secrets masked. Use `--settings path/to/settings.json` for a project settings file.

## 2. Move the v1 copies out of the way

v1 copied `campaign-builder`, `lead-enrichment`, `personalization-writer`, `pipeline-reviewer`, `reply-classifier` and `signal-monitor` into `~/.claude/skills/`, seven agents into `~/.claude/agents/` and `outbound-pipeline.md` into `~/.claude/commands/`. With the v2 plugins installed you would have both versions.

```bash
python3 scripts/remove-v1-hooks.py --apply --move-copies
```

This moves a copy only when there is evidence it came from v1: the file is byte for byte one of v1's files (matched by sha256), or it is a symlink to the same file inside a v1 clone (a folder holding `orchestrator/run.sh`, or, for a link left dangling by a deleted clone, the folder v1's install record `~/.claude/.gtm-installed.json` names as its root). Being listed in the install record is not enough on its own: a file you replaced since, or a v1 copy you edited, is left alone and listed as such. Moved files go into `~/.claude/gtm-v1-backup-<date>/`. Nothing is deleted. If a move fails, the report lists what moved and what is still in place, and you can run it again: v1's install record stays until everything else has moved, so a second run still recognises the same files.

## 3. Clean up by hand

- Remove the `export CLAUDE_GTM_DIR=...` line from your shell profile.
- v1 kept API keys in a `.env` file inside the clone and printed vendor responses into hook output. If you ever shared those logs or ran v1 with real keys, rotate the keys. In v2, connect each tool's official MCP server instead (see [mcp-servers.md](mcp-servers.md)); most use OAuth, so there is no key file at all.
- Restart Claude Code.

## 4. Install v2

```bash
claude plugin marketplace add Frontal-so/go-to-market-orchestrator
claude plugin install gtm-guard@frontal-gtm
claude plugin install gtm-outbound@frontal-gtm
claude plugin install gtm-content@frontal-gtm
claude plugin install gtm-notify@frontal-gtm     # optional
```

## What changed, and why

| v1 | v2 |
|---|---|
| 30 hooks posting to 17 tools' REST APIs | Removed. In our test, feeding each v1 hook the JSON Claude Code sends with HTTP stubbed, most handlers sent empty fields (blank Slack messages, blank CRM records on every tool call, blank Notion pages every turn). Instantly API v1 and Typefully v1, which it called, are retired, and Apollo has replaced `mixed_people/search`. Official MCP servers now cover these tools with OAuth and real actions. |
| `.env` file sourced as shell code on every hook | Gone. MCP servers handle auth; gtm-notify keeps its URLs in Claude Code's plugin settings, marked sensitive. |
| Slack "approve / deny" buttons | Gone (they could not approve anything). gtm-guard uses Claude Code's own permission prompt instead. |
| `/outbound-pipeline` command | `/gtm-outbound:outbound-pipeline` skill, same five steps, run by plugin subagents. |
| Six skills, seven agents | Same skills and agents, rewritten: clearer triggers, drafts only, approval before anything is sent, enrolled, enriched or written to a CRM, current deliverability rules. |
| `skills/modules`, `templates`, `examples` | Now the `/gtm-outbound:gtm-context` skill, which writes your GTM context file from them. |
| `gtm-content-prompts/` | The `gtm-content` plugin: one skill that picks the right prompt. |
| Slack/Discord Stop pings | `gtm-notify`, which sends Claude's real message and never blocks. |
