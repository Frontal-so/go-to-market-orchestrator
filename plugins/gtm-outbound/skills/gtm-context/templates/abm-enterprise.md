# GTM context: named-account (ABM) selling

<!-- For a team working a fixed list of large target accounts, several people per account, few messages, each one researched. Fill the [BRACKETS]; unknowns stay as brackets. -->

## Approval rule

Nothing in this file lets Claude contact anyone or change any system by itself. Research, maps and drafts are Claude's to produce. Reaching outside this folder is not: enriching a contact, writing to the CRM, loading people into a sequence tool, sending or scheduling an email or invitation, or booking a meeting. For each of those Claude shows the exact action and waits for a yes in the chat from the person running the session, and the account owner named below is told before anyone at their account is contacted.

## The account list

- File: `[./data/accounts/target-list.csv]` with account name, domain, owner, tier, status
- Size: [NUMBER] accounts, agreed by [WHO_SIGNED_IT_OFF] on [DATE]
- Changes to the list: only [ROLE]; Claude may suggest additions but never adds them
- Account owners: column `owner` in the file; Claude reads it before drafting anything for an account

## What makes an account a fit

| Factor | What we look for | Where the evidence comes from |
|---|---|---|
| Scale | [FOR_INSTANCE revenue or headcount band] | [ANNUAL_REPORT, COMPANY_SITE] |
| Situation | [FOR_INSTANCE "replacing a system we compete with"] | [NEWS, JOB_POSTS, CALLS] |
| Constraint | [FOR_INSTANCE "regulated, must keep data in region"] | [FILINGS, POLICY_PAGES] |
| Not a fit | [FOR_INSTANCE "public sector, served by a partner"] | |

## The buying group

| Seat | Typical titles | What they care about | What we offer them first |
|---|---|---|---|
| Signs | [TITLES] | [RISK, COST, STRATEGY] | [FOR_INSTANCE a short briefing] |
| Pushes for it | [TITLES] | [DAILY_PAIN] | [FOR_INSTANCE a working session] |
| Tests it | [TITLES] | [ARCHITECTURE, SECURITY] | [FOR_INSTANCE a technical review] |
| Uses it | [TITLES] | [EFFORT, WORKFLOW] | [FOR_INSTANCE a walkthrough] |
| Can stop it | [TITLES] | [CONTRACT, COMPLIANCE] | Only after a sponsor is engaged |

## Events that open an account

Each must come with a source link and a date. Claude separates what it read from what it infers.

- Strong: [FOR_INSTANCE "new head of the buying function"], [FOR_INSTANCE "a public programme our product supports"], [FOR_INSTANCE "an incumbent contract coming up for renewal, if we know it"]
- Useful: [FOR_INSTANCE "a sponsor wrote or spoke publicly about the problem"], [FOR_INSTANCE "relevant roles posted"]
- Background only: [FOR_INSTANCE "sector regulation change", "acquisition"]

## Writing to senior people

- Voice: [FOR_INSTANCE "an informed peer who has read their filings, not a vendor"]
- Each message carries at least one fact about that account with a link, and is written for that person's seat; no two people at one account get the same text
- Lengths: [N] words for the person who signs, [N] for the sponsor, [N] for the tester
- What we never claim: results we cannot show, customer names we have no permission to use
- Banned words: [LIST]

## Who is off limits

- Accounts not on the list
- Anyone at an account in active contract or legal talks, unless the owner says otherwise
- Anyone who opted out (CRM field `[FIELD_NAME]`, and `./data/suppression.csv`, which the reply-classifier writes)
- Competitors: [DOMAINS, for instance rival-one.example]
- [TITLE_FLOOR, for instance "no one below manager level"]

## Tools

Setup: `docs/mcp-servers.md` in the go-to-market-orchestrator repo. Server names only, never keys.

| Job | Tool | How Claude reaches it |
|---|---|---|
| CRM and account owners | [FOR_INSTANCE Salesforce, HubSpot] | Official MCP server where one exists / CSV export |
| Intent or account scores | [FOR_INSTANCE your ABM platform] | CSV export into `./data/intent/` |
| Contact data | [FOR_INSTANCE Apollo] | Official MCP server where one exists / CSV export |
| Sequences | [FOR_INSTANCE your sales engagement tool] | CSV import by the account owner |
| Research | Web search | Built in; every fact cited |
| Team alerts | [FOR_INSTANCE Slack] | gtm-notify plugin |

## Files

- Account briefs: `./data/briefs/[account].md`
- Buying-group maps: `./data/maps/[account].md`
- Drafts: `./data/drafts/[account]/`
- Meeting packs: `./data/packs/[account]/`

## Plays

### Brief one account

Claude writes `./data/briefs/[account].md` with: what the company does and how it is doing (latest public figures, with sources), the three priorities its leaders talk about publicly, the systems it is known to run, our competitive position there, the CRM history with us, and three problems we could plausibly solve, each tied to evidence. Gaps are listed as gaps.

### Map the buying group

1. Claude lists the people it can find for each seat, with title, public profile link and how sure it is of the seat.
2. It suggests the first person to approach and why.
3. Paid lookups of contact details: tool and count shown, **yes required**.

### Draft the approach

1. Claude drafts per person: an email, a LinkedIn note, and for the person who signs, an invitation to a briefing instead of a cold pitch.
2. It proposes an order and spacing over [N] weeks so no two people at the account hear from us on the same day.
3. Drafts go to the owner for review in `./data/drafts/[account]/`. Sending is done by the owner, or by Claude through a connected tool after a yes on the final text in the chat.

### Prepare for the first meeting

Claude assembles `./data/packs/[account]/`: a one-page account plan, the questions to ask, likely objections with answers we can stand behind, and the material to share afterwards. It invents no figures; any ROI estimate shows its inputs.

## Results log

_Nothing logged yet._ Per play: accounts opened, people engaged by seat, replies, meetings, opportunities created, what we learned about this kind of account.
