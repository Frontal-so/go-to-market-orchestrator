---
name: signal-monitor
description: Check target accounts for fresh buying signals (hiring, funding, leadership changes, tech stack changes, company or executive posts, competitor moves) and write a prioritized P0/P1/P2 alert list with a suggested contact and outreach angle for each, every signal with its source link and date. Use when someone asks "any new signals on my accounts?", "what changed at my target accounts this week", "scan these accounts for triggers", "weekly signal digest", "who should we reach out to now", or wants trigger-based timing for outbound. Works with /loop for a daily or weekly re-scan.
argument-hint: "[accounts.csv] [24h|7d|30d]"
---

# Signal monitor

## Task

Look through the user's target accounts for anything new that makes now a good time to reach out, and rank what you find so the team starts with the strongest reason. Read-only: it researches and writes a file, it does not contact anyone.

## Input

- A target account CSV with at least `company_name` and `company_domain`.
- Signal categories, from the signal map in your CLAUDE.md if you have one: `hiring` | `funding` | `leadership` | `tech_adoption` | `content_social` | `intent` | `competitive` | `timing` | `all` (default `all`).
- Lookback window: `24h` | `7d` | `30d` (default `7d`).

If no file is given, ask for one. If the user has no CLAUDE.md GTM context yet, suggest `/gtm-outbound:gtm-context` first, or continue with general B2B signal rules.

## Where the signals come from

Use what this session can actually reach:
- A web search tool and web fetch, for public pages: careers pages and job boards, press releases and news, company blogs, public posts.
- Any data or intent MCP server the user has connected (for example Apollo, Clay, or an intent data provider). Use its read and search tools only.

Claude cannot log in to LinkedIn, Crunchbase, BuiltWith or G2 by itself. If a category needs one of those and nothing connected covers it, say so in the summary instead of guessing.

## Instructions

1. **Load** the account list and the signal map from CLAUDE.md (if present).
2. **For each account, look for signals inside the lookback window:**
   - **Hiring:** new roles that match the personas or teams in your ICP.
   - **Funding:** a new round, with amount and date from the announcement.
   - **Leadership:** a new executive in a target department.
   - **Tech stack:** a tool added or dropped (often visible in job posts that name tools).
   - **Content/social:** the company or an executive published something on a topic you solve.
   - **Intent:** only if an intent data source is connected.
   - **Competitive:** a competitor's customer complaining publicly, a contract renewal window, a competitor price change.
3. **Source every signal.** Each row needs the page it came from (`source_url`) and the date on that page (`detected_date`). If you cannot find a date, mark it `undated` and rank it P2. Never write a signal you did not read on a page or in a connected tool.
4. **Re-check P0 signals:** open the source again and confirm it still holds (the job post is still live, the funding announcement has a date and amount).
5. **Prioritize** (adjust to your own sales cycle):
   - P0: act within 48 hours (new funding, hiring for the exact role you sell to, a competitor's customer in trouble).
   - P1: act within a week (tech adoption, relevant content, a leadership change).
   - P2: use as context in the next outreach (milestones, older or undated signals).
6. **Deduplicate:** the same event found on several pages is one row; keep the best source.
7. **Suggest the contact and angle** for P0 rows: the best-fit role from your ICP and one sentence linking the signal to your offer. Name a person only if you found them on a public page or in a connected tool, and give that source too.

## Output

CSV at `./data/signals/signal_scan_[YYYY-MM-DD].csv` (spreadsheet safety: a cell whose text starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading apostrophe (`'`), so it opens as text, never as a formula):

```
priority, company_name, signal_type, signal_detail, source_url, detected_date, suggested_contact, contact_source, suggested_angle, action_deadline
```

Then a short summary in the chat: accounts scanned, accounts with new signals, P0/P1/P2 counts, and any category you could not check.

### Sharing the alerts

- If the `gtm-notify` plugin is installed, its end-of-turn ping already carries the summary to Slack, Discord or a webhook.
- If a Slack MCP server is connected and the user wants P0 alerts posted, draft the message (company, signal, source, suggested contact and angle), show it, and post only after the user says yes.

## Example

```
/gtm-outbound:signal-monitor ./data/target_accounts.csv 7d
```

Output (fictional companies):
```
P0 (act within 48h):
- Tavrocott Analytics - HIRING - 3 data engineer roles posted 2 days ago - careers page
  → Contact: Maya Chen (VP Engineering, from the company's team page) - Angle: "scaling the data team"
- Tailspin Robotics - FUNDING - Series B announced yesterday - company press release
  → Contact: Sarah Kim (CTO) - Angle: "infrastructure after the raise"

P1 (act within a week):
- Fabrikam Cloud - TECH_ADOPTION - job posts now ask for Snowflake experience
  → Contact: Mike Johnson (Head of Data) - Angle: "Snowflake pipeline monitoring"

Summary: 50 accounts scanned, 8 with new signals (3 P0, 3 P1, 2 P2). Not checked: intent (no intent source connected).
```

## Running it on a schedule

`/loop` re-runs a prompt or skill while the Claude Code session stays open:

```
/loop 1d /gtm-outbound:signal-monitor ./data/target_accounts.csv 24h
```

A `/loop` stops when the session closes and ends by itself after 30 days. For a scan that runs with no session open, use a Desktop scheduled task (your machine must be on) or a cloud scheduled task (runs on a fresh clone of your repository, so the account list must be committed there and local files are not available). See https://code.claude.com/docs/en/scheduled-tasks.
