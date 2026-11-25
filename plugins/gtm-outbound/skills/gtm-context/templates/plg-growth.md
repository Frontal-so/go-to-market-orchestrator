# GTM context: product-led (free plan or trial to paid)

<!-- For teams whose buyers start in the product. Outreach follows what accounts do in the product, not a calendar. Fill the [BRACKETS]; unknowns stay as brackets. -->

## Approval rule

This file tells Claude what good product signals look like and how we talk to users. It does not let Claude message anyone or change any system on its own. Querying a paid enrichment tool, writing to the CRM, adding users to an email or in-app campaign, routing an account to a rep, and sending any message each need the same thing first: Claude shows the exact action (who, how many, what text, which tool) and the person running the session says yes in the chat.

## Product and plans

- Product: [PRODUCT_NAME], [WHAT_IT_DOES]
- Plans: [FREE_OR_TRIAL_TERMS], [PAID_TIERS_AND_WHAT_EACH_UNLOCKS]
- The moment users usually "get it": [ACTIVATION_EVENT, for instance "first report shared with a teammate"]

## Accounts worth a human conversation

| Signal type | Counts when | Where the data lives |
|---|---|---|
| Fit | [INDUSTRY], [HEADCOUNT_RANGE], [REGION] | [ENRICHMENT_SOURCE] |
| Breadth | [N]+ active users from one company domain in [N] days | [ANALYTICS_TOOL] |
| Depth | used [CORE_FEATURE] [N]+ times, or connected [INTEGRATION] | [ANALYTICS_TOOL] |
| Ceiling | reached a free-plan limit: [WHICH_LIMIT] | [BILLING_OR_PRODUCT_DB] |
| Intent | admin viewed pricing or billing [N]+ times | [WEB_ANALYTICS] |

An account is **product-qualified** when it meets fit plus [N] of the other rows. Write your own rule here: [YOUR_RULE].

## Who to talk to inside an account

| Person | How to spot them | Why they matter |
|---|---|---|
| The heavy user | most active in the last [N] days | knows the value first-hand |
| The admin or account owner | created the workspace or holds billing | can upgrade |
| The budget holder | [TITLES] | signs for a team plan |
| A neighbour team | users from a new department | expansion |

## When to reach out

- Now: [FOR_INSTANCE "hit the limit on a team workspace"], [FOR_INSTANCE "several new users from one company this week"]
- This week: [FOR_INSTANCE "steady daily use for two weeks"], [FOR_INSTANCE "second integration connected"]
- Existing customers: [FOR_INSTANCE "usage near plan ceiling"], [FOR_INSTANCE "new department started using it"]

## How we talk to users

- Voice: [FOR_INSTANCE "a helpful product person, never a closer"]
- Each message mentions one real thing the account did in the product, in words the user would recognise
- Offer help or a shortcut before offering a call
- Length: [N] words
- Do not: [FOR_INSTANCE "pretend a human noticed something an automated rule found"], [OTHER_RULES]

## Who is off limits

- Accounts already in a sales cycle (CRM stage [STAGE_NAMES])
- Accounts with an open support escalation ([SUPPORT_TOOL])
- Users who opted out of sales contact (field `[FIELD]`)
- Accounts owned by a named rep, unless that rep agrees
- Competitors' staff: [DOMAINS, for instance rival-one.example]
- Personal mailboxes for team-plan outreach, unless the plan is for individuals

## Tools

Setup: `docs/mcp-servers.md` in the go-to-market-orchestrator repo. Server names only, never keys.

| Job | Tool | How Claude reaches it |
|---|---|---|
| Product usage | [FOR_INSTANCE your analytics tool or warehouse] | CSV export into `./data/usage/`, or an MCP server you have connected |
| CRM | [FOR_INSTANCE HubSpot, Attio, Salesforce] | Official MCP server where one exists / CSV export |
| Enrichment | [FOR_INSTANCE Apollo, Clay] | Official MCP server where one exists / Clay MCP server / CSV export |
| Lifecycle email or in-app | [FOR_INSTANCE your messaging tool] | Claude drafts; the team loads it |
| Alerts | [FOR_INSTANCE Slack] | gtm-notify plugin |

## Files

- Usage exports: `./data/usage/`
- Product-qualified lists: `./data/pql/[date].csv`
- Drafts: `./data/drafts/`

## Plays

### Find this week's product-qualified accounts

1. Claude reads the latest usage export and applies the rule above, then the off-limits list.
2. For each account: company, plan, active users, the signal that qualified it, the people from the table above, and a suggested owner (rep, product team, or automated email).
3. Missing company details may be filled by enrichment only after Claude names the tool and record count and gets a **yes**.
4. Output: `./data/pql/[date].csv`.

### Trials that have not converted

1. From the export, Claude lists trials past day [N] without payment and the most telling thing each one did.
2. It drafts a short series built on that usage: [FOR_INSTANCE help with the next step, a feature they have not found, an offer to set it up, the trial end].
3. Accounts suggested for a rep are listed for the rep; accounts suggested for automated email are listed with the exact draft. Loading either into a tool **waits for a yes**.

### Grow existing customers

1. Claude flags customers near a plan limit or with a new team using the product.
2. It identifies the likely decision maker and drafts a note that starts from what the current team achieved.
3. It checks with the customer's success manager field `[FIELD]` first and says so if someone owns the account.

## Results log

_Nothing logged yet._ Per play: accounts contacted, replies, upgrades, revenue added if known, and which signal predicted conversion best.
