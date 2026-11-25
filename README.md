# Go-to-market orchestrator

Claude Code plugins for outbound and GTM work: find buying signals, score accounts, research prospects, write first lines and sequences, sort replies, prep meetings, review pipeline and draft sales collateral. Your sales tools plug in through their official MCP servers, and a guard adds a best-effort check that makes Claude ask before calls that look like sending, enrolling, enriching or writing to your CRM.

Free and MIT licensed. Version 2, November 2026.

## What's inside

| Plugin | What you get |
|---|---|
| **gtm-outbound** | 8 skills and 7 subagents: the five-stage outbound pipeline, signal monitoring, lead enrichment, personalization, reply triage, campaign building, pipeline review, meeting prep, and a skill that writes your GTM context (ICP, exclusions, signals, copy rules) once so every other skill uses it. |
| **gtm-content** | One skill over 17 prompts: case studies, buyer persona and account cards, LinkedIn carousels, one-pagers, pitch decks, proposals, pricing pages, scopes of work. Written only from facts you give it; gaps come back as `[ASK: ...]`. |
| **gtm-guard** | A best-effort PreToolUse check that asks before sales-tool calls that look like they send, launch, spend credits, change CRM records or delete data, through MCP or `curl`. It matches known tool names and API hosts, so it is a safety net, not a guarantee. Logs field names, list sizes and, for a generic API tool, the method and a path of route words only; never a body, a field value or a path value (a key name can still carry a name if your tools use names as keys). [README](plugins/gtm-guard/README.md) |
| **gtm-notify** | Pings Slack, Discord or any webhook (Zapier, n8n, Make, Clay) when Claude finishes or needs you, with Claude's real message in the ping. [README](plugins/gtm-notify/README.md) |

Everything the skills produce is a file in your project (CSV or markdown) that you read before anything goes out. No skill sends an email, launches a campaign or writes to a CRM without your yes in the chat, and gtm-guard adds a best-effort check at the tool level on top of that.

## Your prospect data

gtm-outbound reads from `input/` and writes to `output/` and `data/` (the suppression list is `data/suppression.csv`); gtm-content saves drafts in `content/`. Those folders hold names, emails, deal notes and customer facts, so keep them out of git: the `.gitignore` in this repo excludes all four, and you should add the same lines to your own project's `.gitignore`.

## Install

In a terminal:

```bash
claude plugin marketplace add Frontal-so/go-to-market-orchestrator
claude plugin install gtm-guard@frontal-gtm
claude plugin install gtm-outbound@frontal-gtm
claude plugin install gtm-content@frontal-gtm
claude plugin install gtm-notify@frontal-gtm      # optional
```

Or inside Claude Code: `/plugin marketplace add Frontal-so/go-to-market-orchestrator`, then `/plugin install gtm-outbound@frontal-gtm`. Update later with `claude plugin marketplace update frontal-gtm`, then `claude plugin update gtm-outbound@frontal-gtm`; remove one with `claude plugin uninstall gtm-notify@frontal-gtm`.

Install **gtm-guard first**, before you connect any sales tool.

## Quick start

1. **Try it on fictional data.** In an empty folder, run `/gtm-outbound:outbound-pipeline` with no file and accept the demo: it runs the five stages one at a time on five made-up companies and writes the results to `output/`. Each stage runs as a subagent, which Claude Code starts in the background, so Claude tells you which stage is running and picks up when it finishes.
2. **Write your GTM context.** `/gtm-outbound:gtm-context` asks a few questions (or reads your ICP doc), starts from a template (outbound-first, ABM enterprise, PLG, founder-led, agency client, minimal) and writes the context into your project's `CLAUDE.md` after you approve it.
3. **Connect your tools.** Add the official MCP servers you use (Apollo, HubSpot, Attio, lemlist, Instantly, Smartlead, Clay, Notion, Linear...). Commands and auth for each: [docs/mcp-servers.md](docs/mcp-servers.md). None of the skills need a tool connected; without one they work from CSVs you export.
4. **Run it on your list.** `/gtm-outbound:outbound-pipeline accounts.csv`.

## The skills

| Skill | Use it to |
|---|---|
| `/gtm-outbound:outbound-pipeline <companies.csv>` | Run signals, scoring, profiles, first lines and a 7-touch email plus LinkedIn sequence, one subagent per stage, each started only after the one before has finished and its file is checked. Only runs when you call it. |
| `/gtm-outbound:gtm-context` | Write or update the GTM context every other skill reads. One per client folder if you are an agency. |
| `/gtm-outbound:signal-monitor <accounts.csv> [7d]` | Scan accounts for hiring, funding, leadership, tech stack and competitor signals, each with a source link and date. |
| `/gtm-outbound:lead-enrichment <file.csv>` | Add firmographics, funding, tech stack and news; asks before any call that spends credits and tests on about 10 rows first. |
| `/gtm-outbound:personalization-writer <prospects.csv>` | First lines, full cold emails, LinkedIn notes, DMs and follow-ups. |
| `/gtm-outbound:campaign-builder <segment>` | A whole micro-campaign: list, exclusions, scoring, copy, deliverability check. Campaigns are created paused or as drafts, never launched. |
| `/gtm-outbound:reply-classifier <replies.csv>` | Sort replies by intent, draft answers, and put unsubscribes on a suppression list (never into a nurture). |
| `/gtm-outbound:pipeline-reviewer <export.csv or crm>` | Flag stale, slipping and at-risk deals, read-only; lists suggested CRM updates instead of making them. |
| `/gtm-content:gtm-content <asset> <notes>` | Draft one of the 17 content assets. |

Claude also picks the right skill on its own when you describe the job ("score these accounts", "draft a case study from this call"), except the pipeline, which you start yourself because it can run long.

To run the signal monitor on a schedule while a session is open: `/loop 1d /gtm-outbound:signal-monitor accounts.csv`. For a weekly run that does not need an open session, use a cloud or Desktop scheduled task ([scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)). A scheduled run cannot start `outbound-pipeline`, because that skill only runs when you call it.

## Moving from v1

Version 1 (April 2026) installed 30 hooks into your global settings that posted to 17 tools' REST APIs. In our test, feeding each v1 hook the JSON Claude Code sends with HTTP stubbed, most handlers sent empty fields; Instantly API v1 and Typefully v1, which it called, are retired. v2 drops that layer for official MCP servers and keeps and rewrites the parts that worked: the pipeline, the skills, the subagents and the content prompts. If you installed v1, run `python3 scripts/remove-v1-hooks.py` first: [docs/migrating-from-v1.md](docs/migrating-from-v1.md).

## Development

```bash
python -m unittest discover -s tests -v     # hook scripts, migration script, manifests, frontmatter
claude plugin validate --strict .           # marketplace (then each folder in plugins/)
```

The hook scripts are Python 3.9+ with the standard library only, and the hooks call `python3`, so it must be on your PATH: true on macOS and Linux; on Windows, use WSL or make a `python3` command available. CI runs both checks on pushes to main and on pull requests. Tested with Claude Code 2.1.332.

## Credits

Built by [Mai-Lan Khong](https://github.com/mailankhong) at [Frontal](https://frontal.so). All companies, people and numbers in the examples are made up; any match with a real company or person is a coincidence.

## Licence

[MIT](LICENSE).
