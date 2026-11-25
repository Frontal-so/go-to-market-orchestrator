---
name: outbound-pipeline
description: Run the five-stage outbound pipeline on a CSV of companies - signals, lead scores, prospect profiles, opening lines and a 7-touch email plus LinkedIn sequence per company - using the gtm-outbound subagents, one after the other. Writes reviewable CSV files to output/ and sends nothing. Use when someone types /gtm-outbound:outbound-pipeline, or asks to "run the outbound pipeline on this list", "turn these accounts into sequences", "build cold outreach for these companies" or "score and write sequences for this CSV". Run it with no file to try it on the bundled sample companies.
argument-hint: "[companies.csv]"
disable-model-invocation: true
---

# Outbound pipeline

Run the five pipeline subagents in order on the CSV at `$ARGUMENTS` (or the bundled sample, see Step 1). Each stage reads the previous stage's file and writes its own file under `output/` in the current project. Nothing is sent, enrolled or written to any CRM or sending tool. Loading the finished sequences into a sending platform is a separate step the user takes (or approves) after reading them, for example with `/gtm-outbound:campaign-builder`.

## Step 1: Check the input

1. If `$ARGUMENTS` is empty, offer a demo run on the bundled sample: `${CLAUDE_SKILL_DIR}/samples/sample-companies.csv` (five fictional companies). Use it only if the user says yes.
2. Read the file. The only hard requirement is a company name column (`company_name`, or a variant such as `Company name`, `company`, `name`, `Company`). The signal scraper adds missing columns and fills gaps by web search.
3. Product context: if `input/icp-config.csv` does not exist in the project, copy `${CLAUDE_SKILL_DIR}/samples/icp-config.csv` there and tell the user: "Fill in input/icp-config.csv with what you sell, your value props and your real case studies, then re-run. Without it the copy is written in generic mode." Ask whether to continue in generic mode now or stop so they can fill it in.
4. Count the data rows and say: "Processing N companies through the pipeline." If most fields are empty, add: "The input is sparse, so the signal scraper will research each company by web search first."
5. Clear the way for this run. If any of `output/0-enriched.csv`, `output/1-signals.csv`, `output/2-prioritized.csv`, `output/2-excluded.csv`, `output/3-profiles.csv`, `output/4-hooks.csv` or `output/5-sequences.csv` already exists, tell the user which ones, then move them (never delete) into `output/archive/<YYYY-MM-DD-HHMM>/`, using the current local time. Say where they went. After this step every file under `output/` that a stage check finds was written by this run.

## Step 2: Run the stages

Start one stage at a time with the Agent tool, in the order below, never two at once. Claude Code usually starts a subagent in the background (https://code.claude.com/docs/en/sub-agents), so its report reaches you as a completion notice in a later turn. After you start a stage, tell the user which stage is running and end your turn. When the notice for that stage arrives, open its output file: it must be there and hold at least one data row. Only then start the next stage. If the user asks how it is going before the notice comes, say the stage is still running.

If a stage reports an error, or its file is missing or has no data rows, stop. Name the stage and the reason, and start no later stage, since each one reads the file before it.

A user who wants Claude to block on each stage instead can turn fork mode off: `"CLAUDE_CODE_FORK_SUBAGENT": "0"` under `env` in `settings.json`, then start Claude Code again (same page). In `claude -p`, Claude can wait for a subagent on its own.

### Stage 1: Signal scraper (with research when the input is thin)
Agent tool, `subagent_type: gtm-outbound:signal-scraper`:
- Prompt: "Read the CSV at `<the input file from Step 1>` and extract all buying signals. If columns are missing or fields are empty, research the companies by web search first. Write the researched data to `output/0-enriched.csv` (only if you researched anything) and the signals to `output/1-signals.csv`. Every signal must cite where it came from: a URL for anything you found, or `input CSV (not checked)` for a signal taken only from the input file, which is never presented as researched."
- If `output/0-enriched.csv` was written, say: "Researched N companies by web search → output/0-enriched.csv".

### Review stop (only when research happened)
If Stage 1 wrote `output/0-enriched.csv` (Step 1 moved any older copy to the archive, so a file there now is from this run):
1. Show a short table of each company and the fields that were filled in, with the source of each.
2. Ask: "These fields came from web search. Check them before I score the list: continue with this data, or stop so you can edit output/0-enriched.csv?"
3. Wait for the answer. Continue only on a clear yes. If the user wants to edit, stop and tell them to re-run after editing.

### Stage 2: Lead prioritizer
Agent tool, `subagent_type: gtm-outbound:lead-prioritizer`:
- Prompt: "Read `output/1-signals.csv`, plus `input/icp-config.csv` and `data/suppression.csv` if they exist. Score and tier every company. Write `output/2-prioritized.csv` and the set-aside companies to `output/2-excluded.csv`."

### Stage 3: Prospect profiler
Agent tool, `subagent_type: gtm-outbound:prospect-profiler`:
- Prompt: "Read `output/2-prioritized.csv` and build a prospect profile per company. Write `output/3-profiles.csv`."

### Stage 4: Hook writer
Agent tool, `subagent_type: gtm-outbound:hook-writer`:
- Prompt: "Read `output/3-profiles.csv` and `input/icp-config.csv` if it exists. Write one opening line per company. Write `output/4-hooks.csv`."

### Stage 5: Sequence builder
Agent tool, `subagent_type: gtm-outbound:sequence-builder`:
- Prompt: "Read `output/4-hooks.csv`, `output/3-profiles.csv` and `input/icp-config.csv` if it exists. Build the 7-touch sequence for each company. Write `output/5-sequences.csv`."

## Step 3: Report

Read each output file to get the real row counts, then report:

```
Pipeline complete. Nothing has been sent.

Stage 0 - Research:          N companies researched by web search → output/0-enriched.csv (only if it ran)
Stage 1 - Signal scraper:    X signals across N companies         → output/1-signals.csv
Stage 2 - Lead prioritizer:  N companies scored and tiered        → output/2-prioritized.csv (E excluded → output/2-excluded.csv)
Stage 3 - Prospect profiler: N profiles                           → output/3-profiles.csv
Stage 4 - Hook writer:       N opening lines (R flagged NEEDS_REVIEW) → output/4-hooks.csv
Stage 5 - Sequence builder:  X sequence steps                     → output/5-sequences.csv
```

Then list what the user should check before anything goes out: rows marked `NEEDS_REVIEW`, any signal without a source, every signal marked `input CSV (not checked)` that an opening line or email relies on, and the sender details in the sign-off.

Every stage that writes a CSV follows one rule for spreadsheet safety: a cell whose text starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading apostrophe (`'`), so a spreadsheet shows it as text and never runs it as a formula.

## After the pipeline

- To load the sequences into Instantly, lemlist, Smartlead or another sender, use `/gtm-outbound:campaign-builder` or import `output/5-sequences.csv` by hand. Create the campaign paused or as a draft and launch it yourself.
- Replies coming in: `/gtm-outbound:reply-classifier` (try it on `${CLAUDE_SKILL_DIR}/samples/sample-replies.csv`).
- Booked meetings: the `gtm-outbound:meeting-prep` subagent writes pre-call briefs (try it on `${CLAUDE_SKILL_DIR}/samples/sample-meetings.csv`).
- If your sales tools are connected as MCP servers, install the `gtm-guard` plugin from the same marketplace. It makes Claude ask before any send, launch, credit spend or CRM write.
