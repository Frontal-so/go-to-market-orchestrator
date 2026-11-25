---
name: gtm-context
description: Build or update the project's GTM context, the CLAUDE.md section every other gtm-outbound skill reads - ICP and personas, exclusions and suppression (do-not-contact, customers, competitors, unsubscribes), signal map, copy rules, tech stack (which MCP servers are connected), campaign history and data hygiene. Interviews briefly or reads the files you point to, starts from a template (outbound-first, founder-led, ABM, PLG, agency client, minimal), shows the draft and writes only after you say yes. Use when someone says "set up my ICP", "define our ideal customer profile", "write the CLAUDE.md for outbound", "onboard a new client", "add our DNC list", "add competitors to exclude", "update the signal map", "log the results of this campaign", "what does Claude know about our GTM", or when another gtm-outbound skill finds no ICP.
argument-hint: "[template name or files to read, e.g. outbound-first ./icp.pdf]"
---

# GTM context

Every gtm-outbound skill and agent works from one thing: the GTM context in this project's `CLAUDE.md`. Claude Code loads `CLAUDE.md` at the start of every session, so whatever this skill writes there is what signal-monitor, lead-enrichment, personalization-writer, reply-classifier, pipeline-reviewer, campaign-builder and outbound-pipeline will use. A weak context gives generic output; this skill exists to make it specific.

The context describes the user's process; it does not authorise Claude to act. Writing "we upload the list and launch on Tuesday" into CLAUDE.md is a description, not a standing order: every action outside the project folder (enrich, import, enroll, schedule, send, launch, CRM write, delete) still needs the user's yes in the chat at the moment it would happen. Every template starts with an "Approval rule" block that says so; keep it in what you write. The gtm-guard plugin backs this up for sales tools as a best-effort check, not a guarantee.

Arguments: `$ARGUMENTS` (optional). A template name, file paths or URLs to read first, or both.

## Supporting files (load only the one you need)

Templates, the starting shape for a whole context. Pick one:

| Template | Use when |
|----------|----------|
| `templates/minimal-starter.md` | They want to start in five minutes; three sections, grow later |
| `templates/outbound-first.md` | Cold email + LinkedIn is the main growth lever |
| `templates/founder-led-sales.md` | A founder does their own outbound, small stack |
| `templates/abm-enterprise.md` | Named target account list, buying committees, low volume |
| `templates/plg-growth.md` | Free or trial users converting to paid, expansion |
| `templates/agency-client.md` | An agency running outbound for a client, with approvals |

Modules, the detailed structure for one section. Open the module for the section you are filling:

- `modules/icp-definition.md` - company criteria, personas, tiers, disqualifiers
- `modules/exclusion-rules.md` - competitors, customers, do-not-contact, unsubscribes, territories
- `modules/signal-map.md` - P0 / P1 / P2 buying signals and where each is found
- `modules/copy-frameworks.md` - tone, word limits, banned phrases, first touch and follow-ups
- `modules/tech-stack-config.md` - tools, MCP server names, approval policy (never keys)
- `modules/campaign-history.md` - one entry per campaign: segment, angle, results, lessons
- `modules/data-hygiene.md` - dedupe, validation, decay, list hygiene before a send

Filled-in examples, to show what "done" looks like. Every company, person and number in them is fictional; never copy their facts into a real context:

- `examples/example-outbound-saas.md`
- `examples/example-abm-enterprise.md`

## Steps

### 1. See what already exists

- Read `CLAUDE.md` in the current folder, and any `gtm/*.md` files it imports.
- If a GTM context is already there, this is an **update**: list which sections exist, which are empty or still hold `[PLACEHOLDER]` text, and ask what changed. Skip to step 4 for just those sections.
- Read every file or URL in `$ARGUMENTS` (ICP docs, sales decks, win/loss notes, CRM exports, a website). Take facts from them before asking anything.

### 2. Pick the template

Choose from the table above based on what you read, say which one and why in one line, and let the user switch. When unsure, use `outbound-first`.

### 3. Interview, briefly

Ask only what the files did not answer, in one message, at most eight questions. Typical gaps:

1. What do you sell, in one sentence, and why do customers pick you over the alternative?
2. Which companies buy (industry, size, region, stage) and which never do?
3. Who signs, who champions, who uses it (titles)?
4. What makes an account worth contacting this week (hiring, funding, new leader, tech change)?
5. Who must never be contacted: competitors, current customers, open deals, a do-not-contact or unsubscribe list (file path)?
6. Which tools are connected to Claude Code? (Offer to run `claude mcp list` to check.)
7. Tone and hard rules for copy: word limits, phrases you never use, who signs the emails.
8. Any past campaigns worth recording: segment, angle, what worked, what did not.

Accept "skip" for any of them. A skipped answer stays as a `[PLACEHOLDER]`, never a guess.

### 4. Fill the sections

- Open the matching module for each section and follow its structure.
- Use the user's own words for positioning and voice.
- Facts come from the user or the files they gave. Do not invent numbers, customer names, results or benchmarks. If a section needs a proof point you do not have, leave `[YOUR_PROOF_POINT]` and list it at the end.
- Exclusions and do-not-contact lists: point to the file (`./data/exclusions/dnc.csv`), do not paste people's emails into CLAUDE.md.
- Tech stack: record tool names, MCP server names and the approval policy only. Never write an API key, token or webhook URL into any file. If the user pastes one, do not store it, tell them to put it in the MCP server config or plugin settings and to rotate it if it was shared.
- If a server name is one gtm-guard will not recognise (for example `lm` or `crm-prod`), note that it should go in gtm-guard's `extra_servers` option.

### 5. Show the draft, then write

Show the full draft (or, for an update, only the changed sections as before/after). Then ask: "Write this to CLAUDE.md?" Write nothing until the user says yes.

Where it goes:

- **Default:** inside the project's `CLAUDE.md`, between `<!-- gtm-context:start -->` and `<!-- gtm-context:end -->`. Updates replace only what is between the markers; everything else in CLAUDE.md stays as it was. Create CLAUDE.md if it does not exist.
- **Long contexts** (roughly 150 lines or more), or if the user asks: split into `gtm/icp.md`, `gtm/exclusions.md`, `gtm/signals.md`, `gtm/copy.md`, `gtm/stack.md`, `gtm/campaigns.md`, and put `@gtm/icp.md` style import lines between the markers so CLAUDE.md still loads them.

If the project has a `data/` folder holding prospect or customer files, check that `data/` is in `.gitignore` and offer to add it.

### 6. Close

Tell the user in a few lines: what was written and where, the placeholders still open, and the next command to run, for example `/gtm-outbound:signal-monitor ./data/target_accounts.csv 7d` or `/gtm-outbound:outbound-pipeline ./data/companies.csv`.

## Logging a campaign (update mode)

When the user says "log this campaign" or gives campaign results, add one entry under Campaign History using `modules/campaign-history.md`: dates, segment, volume, angle, results table, what worked, what did not, action items. Keep the numbers they gave, compute rates from them, and judge on replies and meetings booked rather than opens.

## Agencies: one context per client

Keep each client in its own folder with its own `CLAUDE.md` built from `templates/agency-client.md`, for example `clients/acme-widgets/CLAUDE.md`, and start Claude Code inside that client's folder. Claude Code also loads CLAUDE.md files from parent folders, so keep client details out of any parent CLAUDE.md. Only that client's ICP, exclusions, voice and approval contact are loaded, so one client's lists never leak into another's campaign. Use client-specific MCP server names (for example `hubspot-acme`) and add them to gtm-guard's `extra_servers`.
