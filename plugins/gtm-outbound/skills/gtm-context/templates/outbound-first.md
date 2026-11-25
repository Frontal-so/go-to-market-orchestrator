# GTM context: outbound-led

<!-- For teams whose pipeline comes mainly from cold email and LinkedIn. Replace every [BRACKET]. Anything you cannot answer yet stays a [BRACKET]; never let Claude guess it. -->

## Approval rule

This file is a description of our outbound process, not a set of standing orders. Every step that reaches outside this folder needs a fresh yes: looking up or enriching a contact, importing a list into a tool, adding people to a sequence, setting a send schedule, sending an email, sending a LinkedIn invitation, starting a campaign, or writing to or deleting from the CRM. For each one Claude prepares the action, shows exactly what will happen (tool, list size, message), and waits for the person running this session to say yes. This applies to every play below, however it is worded.

## What we sell and why it wins

- Company: [COMPANY_NAME]
- In one line: [WHAT_IT_DOES_FOR_WHOM]
- Why buyers switch to us: [REASON, ideally a phrase a customer used]
- What we are not: [ADJACENT_THINGS_PEOPLE_CONFUSE_US_WITH]

## Accounts we go after

| Attribute | In | Out |
|---|---|---|
| Industry | [INDUSTRIES] | [INDUSTRIES_WE_SKIP] |
| Headcount | [RANGE] | [TOO_SMALL / TOO_BIG] |
| Region | [COUNTRIES] | [COUNTRIES_WE_CANNOT_SERVE] |
| Stage or funding | [STAGES] | [STAGES] |
| Must have | [FOR_INSTANCE "runs its own sales team"] | |

### People inside those accounts

| Role in the deal | Titles to look for | Reach out |
|---|---|---|
| Owns the budget | [TITLES] | First |
| Feels the pain every day | [TITLES] | Alongside |
| Can block it | [TITLES] | Only once a champion is engaged |

### How we rank accounts

- **A accounts:** fit on every "In" row and at least one trigger from the next section in the last [N] days.
- **B accounts:** good fit, no live trigger. Nurture, re-check monthly.
- **C accounts:** partial fit. Do not spend credits on them.

## Reasons to reach out now

Ranked strongest first. Each needs a source link and a date when Claude reports it.

1. [TRIGGER, for instance "job post for a role our product supports"] (where to find it: [SOURCE])
2. [TRIGGER, for instance "new leader in the buying team in the last 90 days"] ([SOURCE])
3. [TRIGGER] ([SOURCE])
4. [WEAKER_CONTEXT_ONLY_TRIGGER] (use as colour in the email, never as the reason alone)

## How our emails read

- Voice: [FOR_INSTANCE "one operator writing to another; no adjectives about ourselves"]
- Length: first email under [N] words, LinkedIn note under [N] characters, 200 at most (LinkedIn's limit for a note).
- Every message names one specific thing about the recipient's company that we found and can link to.
- The ask: [FOR_INSTANCE "a yes/no question about their problem, no calendar link in the first email"]
- Never write: [BANNED_PHRASES]
- Angles we use, with the trigger each one fits:
  - [ANGLE] when [TRIGGER]
  - [ANGLE] when [TRIGGER]
- Proof points we may quote (real, approved): [PROOF] or leave blank.

## Who is off limits

- Customers: `[./data/exclusions/customers.csv]`
- Open deals: `[./data/exclusions/open-deals.csv]` or "check the CRM before every list"
- Do-not-contact: `[./data/exclusions/dnc.csv]`; unsubscribes: `./data/suppression.csv` (the reply-classifier adds anyone who opts out the same day)
- Competitors and their staff: [DOMAINS, for instance rival-one.example]
- Personal mailboxes (gmail.com, yahoo.com, outlook.com, hotmail.com) unless we sell to individuals
- [ANY_REGION_OR_SECTOR_RULE, for instance "no outreach into countries where we have not checked the local consent rules"]

## Tools Claude can reach

Setup for each: `docs/mcp-servers.md` in the go-to-market-orchestrator repo. Write server names here, never keys.

| Job | Tool | How Claude reaches it | Server name |
|---|---|---|---|
| Finding contacts | [FOR_INSTANCE Apollo] | Official MCP server where one exists / CSV export | [NAME] |
| Enrichment | [FOR_INSTANCE Clay] | Clay MCP server / CSV export | [NAME] |
| Sending | [FOR_INSTANCE Instantly, lemlist, Smartlead] | Official MCP server where one exists / CSV import by hand | [NAME] |
| CRM | [FOR_INSTANCE HubSpot, Attio] | Official MCP server where one exists / CSV export | [NAME] |
| LinkedIn | [FOR_INSTANCE Sales Navigator] | By hand; Claude drafts the notes | n/a |
| Team pings | [FOR_INSTANCE Slack] | gtm-notify plugin | n/a |

If a server name is unusual (for instance `crm-prod`), add it to gtm-guard's `extra_servers` setting so its write calls are checked too.

## Where files live

- Raw lists: `./data/lists/`
- Scored and enriched lists: `./data/scored/`
- Drafted sequences: `./data/sequences/`
- Suppression files: `./data/exclusions/`

Keep `data/` in `.gitignore`: it holds people's personal data.

## Plays

### Play 1: a list for one segment

1. Claude writes down the segment: one rank (A or B) and one trigger.
2. Claude drafts the search (filters, expected size) for [CONTACT_TOOL] and shows it. **Wait for yes** before running it, because searches that reveal emails or phones can spend credits.
3. Claude picks [N] people per account by the role table above.
4. Claude removes everyone on the off-limits lists and says how many were removed and why.
5. Output: `./data/lists/[segment]-[date].csv` with name, title, company, domain, LinkedIn URL, trigger, trigger source, rank.

### Play 2: research and score

1. For each account Claude collects size, funding, tools in use, recent news and open roles, each with a source link and date.
2. Claude ranks each account A, B or C by the rules above, and writes one sentence on why it is worth a message now.
3. Fields Claude could not find stay empty; Claude never fills a gap with a guess.
4. Any paid enrichment: Claude names the tool, the number of records and the fields, and **waits for yes**, starting with a test batch of about 10.
5. Output: `./data/scored/[segment]-[date].csv`.

### Play 3: write the sequence

1. Claude picks the angle that matches the segment's trigger.
2. Claude drafts [N] emails and the LinkedIn note, with the spacing you choose: [FOR_INSTANCE day 0, 3, 8, 15].
3. Each email gets its personal line from the research file; Claude marks any prospect without a usable fact instead of writing a vague line.
4. Every email carries an opt-out line.
5. Output: `./data/sequences/[segment]-[date].md` for review.

### Play 4: put it live

1. Claude prepares the import file for [SENDING_TOOL] and a summary: campaign name, number of people, mailboxes, daily limit [N per mailbox], send window, first send date.
2. Claude shows the summary and **waits for yes** before importing or creating anything, and creates the campaign paused.
3. Starting the campaign is a separate step: Claude asks again, or you start it in the tool yourself.
4. LinkedIn invitations are sent by you; Claude only drafts them.
5. After the last step of the sequence, Claude adds a results entry below.

To keep checking the A accounts for new triggers while a session stays open: `/loop [INTERVAL] /gtm-outbound:signal-monitor ./data/scored/[FILE].csv`. New matches go to a file for review; nobody is added to a campaign without a yes.

## Results log

<!-- One entry per campaign. Use the numbers from the sending tool; judge on replies and meetings rather than opens. -->

_Nothing logged yet._

Entry shape: name and dates, segment and rank, trigger used, number contacted, replies, positive replies, meetings, what to repeat, what to drop.
