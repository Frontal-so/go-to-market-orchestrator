# GTM context: Hollowpine Systems (filled example, named-account selling)

<!-- A filled-in version of templates/abm-enterprise.md. Hollowpine Systems, every target account, person, domain and number below are invented to show what a finished context looks like. Do not copy any of these facts into a real context. -->

## Approval rule

Nothing in this file lets Claude contact anyone or change any system by itself. Research, maps and drafts are Claude's to produce. Reaching outside this folder is not: enriching a contact, writing to HubSpot, loading people into a sequence, sending or scheduling an email or invitation, or booking a meeting. For each of those Claude shows the exact action and waits for a yes in the chat from the person running the session, and the account owner is told before anyone at their account is contacted.

## The account list

- File: `./data/accounts/target-list.csv` (account, domain, owner, tier, status)
- Size: 40 accounts, agreed by the VP Sales on 2026-01-08
- Changes to the list: VP Sales only; Claude may suggest additions with evidence
- Owners: column `owner`; three account executives split the list

## What makes an account a fit

| Factor | What we look for | Where the evidence comes from |
|---|---|---|
| Scale | Manufacturers or retailers with more than 2,000 direct suppliers | Annual report, sustainability report |
| Situation | Supplier checks still run on spreadsheets and yearly questionnaires | Job posts, conference talks, procurement news |
| Constraint | Subject to supply-chain due diligence laws in the markets they sell into | Filings, public policy pages |
| Not a fit | Companies whose purchasing is outsourced to a procurement services firm | Company site, news |

## The buying group

| Seat | Typical titles | What they care about | What we offer them first |
|---|---|---|---|
| Signs | Chief Procurement Officer, CFO | Disruption risk, audit exposure | A 30-minute briefing on their sector's recent disruptions |
| Pushes for it | Head of Supplier Risk, Director Procurement Operations | Hours lost chasing questionnaires | A working session on their current process |
| Tests it | Enterprise Architect, Data Platform Lead | Integration with the ERP, data residency | A technical review |
| Uses it | Category Managers | Alerts that are relevant to their categories | A walkthrough |
| Can stop it | Legal, Information Security | Contract terms, security review | Only after a sponsor is engaged |

## Events that open an account

- Strong: a new CPO or Head of Supplier Risk in the last 90 days; a public statement about rebuilding supplier oversight; a disruption at a named supplier reported in the press
- Useful: the sponsor spoke or wrote about supplier risk; job posts for supplier risk analysts
- Background only: a new due diligence regulation in one of their markets; an acquisition

Every event Claude reports has a link and a date, and Claude says when something is its inference rather than what the source states.

## Writing to senior people

- Voice: a peer who has read their annual report, not a vendor
- Each message carries one sourced fact about that account and is written for the reader's seat; no two people at one account get the same text
- Lengths: 70 words for the person who signs, 100 for the sponsor, 120 for the tester
- Never claim results we cannot show, or name a customer that has not agreed to it
- Banned words: "best-in-class", "end-to-end", "seamless", "unlock"

## Who is off limits

- Accounts not on the list
- Two accounts in contract talks (status `negotiating` in the list file)
- Opt-outs: HubSpot property `sales_opt_out`
- Competitors: rival-riskgraph.example, rival-supplierscan.example
- No one below manager level, except category managers invited to a walkthrough

## Tools

Setup: `docs/mcp-servers.md` in the go-to-market-orchestrator repo.

| Job | Tool | How Claude reaches it |
|---|---|---|
| CRM and owners | HubSpot | Official MCP server, OAuth (server `hubspot`) |
| Account scores | The team's intent platform | Weekly CSV export into `./data/intent/` |
| Contact data | Apollo | Official MCP server, OAuth (server `apollo`) |
| Sequences | The team's sales engagement tool | CSV import by the account executive |
| Research | Web search | Built in; every fact cited |
| Team alerts | Slack #abm | gtm-notify plugin |

## Files

- Account briefs: `./data/briefs/`
- Buying-group maps: `./data/maps/`
- Drafts: `./data/drafts/`
- Meeting packs: `./data/packs/`

## Plays

### Brief one account

For each account Claude writes `./data/briefs/[account].md`: what the company makes and sells, its latest public results, its stated priorities on suppliers, the systems it is known to use, who it already buys from in our space, our history with it from HubSpot, and three problems we could solve, each tied to a source. Unknowns are listed as unknowns.

### Map the buying group

1. People Claude can find per seat, with title, public profile link and confidence.
2. Suggested first contact and why.
3. Contact details from Apollo: count shown, **yes required**.

### Draft the approach

1. Per person: an email and a LinkedIn note; for the CPO, a briefing invitation.
2. Spacing over three weeks; never two people at one account on the same day.
3. Drafts go to the owner in `./data/drafts/[account]/`. The owner sends them, or Claude sends a named draft through a connected tool after a yes on the final text.

### Prepare for the first meeting

`./data/packs/[account]/`: one-page account plan, questions to ask, likely objections and honest answers, follow-up material. Any savings estimate shows its inputs and is labelled an estimate.

## Results log

### New procurement leaders, Q1 2026 (all numbers fictional)

| | Count |
|---|---|
| Accounts opened | 6 |
| People engaged | 14 |
| Replies | 5 |
| Meetings | 3 |
| Opportunities created | 2 |

- Learned: sponsors answered a question about their questionnaire process more often than an offer of a briefing.
- Learned: architects ignored email; the account executives will meet them at the two sector events instead.
- Next: try the disruption angle on accounts where a supplier made the news.
