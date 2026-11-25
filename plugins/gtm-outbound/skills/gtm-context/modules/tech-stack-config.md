# Module: your tech stack

<!-- Drop this into the Tech Stack part of a template. It says which tools you run and the route Claude Code takes into each. It stores names and IDs, nothing secret: an API key, token or webhook URL never goes into CLAUDE.md or any file next to it. -->

## Ground rules for connecting a tool

Where the vendor publishes an **official MCP server**, use it. `docs/mcp-servers.md` in this repo has the command and sign-in method per vendor. The short version:

- OAuth first. You sign in once through `/mcp` and your project holds no key.
- A vendor with keys only: the key belongs in that server's own config (`claude mcp add ... --header`), and never in CLAUDE.md, a CSV or anything you commit.
- Run `claude mcp list` to see what is connected, and write down the server name you picked. Skills and gtm-guard address tools as `mcp__<server name>__<tool>`.
- Picked a name gtm-guard will not recognise, such as `crm-prod` or `outbound-eu`? List it in gtm-guard's `extra_servers` setting, so sends, record changes and credit spends on it still stop for your OK.
- No MCP server for a tool? Claude works from its CSV exports, saved in the folders listed under "Where local files go".

## Your stack at a glance

One row per job. Fill in what you actually use and delete the rest.

| Job | Your tool | Route into Claude Code | Server name you chose |
|-----|-----------|------------------------|-----------------------|
| Hold contacts, companies and deals | [HubSpot, Salesforce, Attio, ...] | [official MCP with OAuth, or CSV] | [hubspot] |
| Find people and fill in their data | [Apollo or Clay, or exports from another data provider] | [official MCP, or CSV] | [apollo] |
| Send email sequences | [Instantly, lemlist, Smartlead, ...] | [official MCP, or a CSV you upload yourself] | [instantly] |
| Work LinkedIn | [Sales Navigator] | [by hand; on Advanced Plus, CRM sync] | none |
| Look things up | [Claude's web search, or a research tool] | [built in, MCP, or by hand] | [name, or none] |
| Measure campaigns and product use | [Amplitude, Mixpanel, your CRM's reports] | [MCP, or CSV] | [name] |
| Store and report data centrally | [BigQuery, Snowflake, a spreadsheet] | [MCP, CSV, or by hand] | [name] |
| Tell the team | [Slack, Discord] | [gtm-notify plugin, or Slack's MCP server] | [name] |
| Glue tools together | [Zapier, Make, n8n] | [gtm-notify's generic webhook, or the vendor's MCP] | [name] |

## Settings per tool

### CRM: [tool name]

- Server name in Claude Code: `[hubspot]` (setup steps in `docs/mcp-servers.md`)
- Sign-in: `[OAuth through /mcp]`
- Records Claude works with: `[contacts, companies, deals, notes]`
- Your own fields Claude should understand:
  - `[priority_score: whole number from 0 to 100, the lead-prioritizer total]`
  - `[priority_tier: TIER_1 to TIER_4]`
  - `[signal_seen_on: date]`
- What Claude may change: `[it prepares edits; a person approves every new or changed record]`

### Data and enrichment: [tool name]

- Server name: `[apollo]`
- Spending rule: `[any lookup that costs credits waits for a person's OK]`
- Data points to fetch: `[work email, job title, headcount, industry, tools in use, latest funding]`
- Credits you allow per month: `[your number]`

### Sending: [tool name]

- Server name: `[instantly]`
- Who starts a campaign: `[Claude saves it as a draft; a person launches it]`
- Mailboxes:
  - How many, and on which domain: `[a handful of warmed inboxes on a separate domain]`
  - Cap per inbox per day: `[the limit you agreed with your deliverability provider]`
  - Warm-up finished on every inbox: `[yes/no]`
  - SPF, DKIM and DMARC on each sending domain: `[yes/no]`
  - One-click unsubscribe header switched on: `[yes/no]`

### LinkedIn: [tool name]

- How you work it: `[by hand in Sales Navigator]`
- Your activity caps: `[set your own; LinkedIn's rules vary by account type]`
- Saved searches Claude should know about: `[name each one and what it watches for]`
- How data leaves LinkedIn: `[Sales Navigator has no CSV export; on the Advanced Plus plan leads and accounts sync to Salesforce, Microsoft Dynamics or HubSpot; otherwise copy what you need by hand]`

### Analytics: [tool name]

- Where Claude reads it: `[server name, or the folder your exports land in]`
- Events that matter: `[signed_up, trial_started, teammate_invited, plan_upgraded]`
- Reports worth pointing Claude at: `[trial funnel, source attribution, deal velocity]`

### Research: [method]

- Route: `[Claude's built-in web search and fetch, or a research tool's MCP server]`
- What it is for:
  - Briefs on target accounts: stated strategy, earnings calls, who they compete with
  - Double-checking a signal another source raised: a new hire, a funding round, a tool they adopted
  - Background on the person: talks, articles, things they posted in public
  - Watching competitors: how they position and price, what they launched lately
- Rule: a fact that reaches a prospect keeps its link and the date someone checked it.

### Alerts: [Slack, Discord, ...]

- Route: `[gtm-notify plugin, with the webhook URL saved in its plugin settings as a sensitive value; or Slack's own MCP server]`
- A channel plan (pick your own names):
  - `#gtm-signals`: P0 rows from the signal-monitor skill
  - `#gtm-replies`: replies the reply-classifier marks interested or referral
  - `#gtm-pipeline`: the weekly pipeline review
  - `#gtm-campaigns`: a campaign went live or ended

### Inbox: [Google Workspace, Microsoft 365, ...]

- Route: `[your mail provider's MCP connector, or replies exported to CSV]`
- Jobs:
  - Sort incoming replies (this feeds the reply-classifier skill)
  - Draft follow-ups that a person reads, edits and sends
- Bulk sending stays on a sending platform. A personal inbox is for one-to-one follow-ups and founder outreach.

### Spreadsheets: [Google Sheets, Excel, ...]

- Route: `[server name, or the export folder]`
- Jobs:
  - Gather the results you export from the sending platform
  - Serve as the pipeline tracker until there is a CRM
  - Keep the team's weekly numbers in one place
- Freeze the column headers: Claude reads and writes by header name.

## Where local files go

- `./data/prospects/` (or yours): people to contact
- `./data/campaigns/` (or yours): campaign exports
- `./data/enriched/` (or yours): enrichment results kept for reuse
- `./data/crm/` (or yours): exports from the CRM

All of it is personal data about real people, so keep `data/` listed in `.gitignore`.

## Keys and secrets

This file holds none. Keys and webhook URLs sit in the MCP server's config, in plugin settings (gtm-notify stores its webhook URLs as sensitive values) or in a secret manager. A key that ever landed in a project file or a chat gets rotated.

---

## Two filled-in stacks

<!-- Both stacks are made up and only show the format. -->

**Stack A: an outbound team**
- Contacts and deals: HubSpot, through HubSpot's remote MCP server (OAuth); server name `hubspot`
- People data: Apollo, official MCP server, OAuth; `apollo`
- Sending: Instantly, official MCP server, API v2 key in the server's header config; `instantly`
- LinkedIn: Sales Navigator by hand (it has no CSV export); no server

**Stack B: a product-led team**
- Contacts and deals: Attio, official MCP server (OAuth only); `attio`
- Product usage: Amplitude, exports saved to `./data/product/`; no server
- People data: Clay, through Clay's hosted MCP server; `clay`
- Alerts: Slack, through the gtm-notify plugin; no server
