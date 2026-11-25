# GTM context: Kestrovane (filled example, outbound-led)

<!-- A filled-in version of templates/outbound-first.md. Kestrovane, its customers, its competitors, every person, domain and number below are invented to show what a finished context looks like. Do not copy any of these facts into a real context. -->

## Approval rule

This file is a description of our outbound process, not a set of standing orders. Every step that reaches outside this folder needs a fresh yes: looking up or enriching a contact, importing a list into Instantly, adding people to a sequence, setting a send schedule, sending an email, sending a LinkedIn invitation, starting a campaign, or writing to or deleting from HubSpot. For each one Claude prepares the action, shows exactly what will happen, and waits for the person running this session to say yes. This applies to every play below, however it is worded.

## What we sell and why it wins

- Company: Kestrovane (kestrovane.example)
- In one line: scheduling and dispatch software for heating, cooling and plumbing companies with 20 to 200 field technicians.
- Why buyers switch to us: "the board finally matches what the vans are doing" (a fictional customer, quoted from a fictional call).
- What we are not: an accounting package, or a marketplace that sends jobs to contractors.

## Accounts we go after

| Attribute | In | Out |
|---|---|---|
| Industry | Residential and light commercial HVAC, plumbing, electrical service | New-build construction, single-trade sole traders |
| Headcount | 30 to 300 staff | Under 15, over 1,000 |
| Region | US and Canada | Everywhere else, for now |
| Ownership | Owner-run or private-equity backed groups | Franchise units that must use the franchisor's system |
| Must have | Its own dispatch team (at least two dispatchers) | |

### People inside those accounts

| Role in the deal | Titles to look for | Reach out |
|---|---|---|
| Owns the budget | Owner, General Manager, COO | First |
| Feels the pain every day | Dispatch Manager, Service Manager | Alongside |
| Can block it | Office Manager or Controller (owns the current tool contract) | Only once a champion is engaged |

### How we rank accounts

- **A accounts:** every "In" row, plus a trigger below seen in the last 45 days.
- **B accounts:** good fit, no live trigger. Re-check monthly.
- **C accounts:** partial fit. No paid lookups.

## Reasons to reach out now

1. Job post for a dispatcher or service coordinator (source: the company's careers page or a job board)
2. Acquired another local service company in the last six months (source: local business news, the company's own announcement)
3. Opened a new branch or service area (source: company site, Google Business profile)
4. Context only: seasonal hiring of technicians before summer or winter

## How our emails read

- Voice: an ex-dispatcher talking shop. No adjectives about Kestrovane.
- Length: first email under 90 words, LinkedIn note under 200 characters (LinkedIn's limit for a note).
- Every email names one checkable fact about the recipient's company, and Claude keeps the link in the research file.
- The ask: a yes/no question about their dispatch board. No calendar link in the first email.
- Never write: "streamline", "revolutionise", "quick question", "hope this finds you well".
- Angles:
  - "Second branch, same board?" when they opened a branch or acquired a company
  - "Hiring a dispatcher usually means the board stopped scaling" when they post a dispatcher role
- Proof points we may quote: Marrowgill Heating (fictional), "dispatch calls per job went from three to one" (fictional, cleared by the fictional customer on 2026-02-10).

## Who is off limits

- Customers: `./data/exclusions/customers.csv` (exported from HubSpot every Monday)
- Open deals: checked in HubSpot before every list
- Do-not-contact: `./data/exclusions/dnc.csv`; unsubscribes from replies: `./data/suppression.csv`
- Competitors: rival-dispatch.example, rival-fieldops.example
- Personal mailboxes (gmail.com, yahoo.com, outlook.com, hotmail.com)
- Quebec, until we have French copy

## Tools Claude can reach

Setup for each: `docs/mcp-servers.md` in the go-to-market-orchestrator repo.

| Job | Tool | How Claude reaches it | Server name |
|---|---|---|---|
| Finding contacts | Apollo | Official MCP server, OAuth | apollo |
| Enrichment | Clay | Clay MCP server | clay |
| Sending | Instantly (four warmed mailboxes) | Official MCP server, key in the server's header config | instantly |
| CRM | HubSpot | Official MCP server, OAuth | hubspot |
| LinkedIn | Sales Navigator | By hand; Claude drafts the notes | n/a |
| Team pings | Slack #outbound | gtm-notify plugin | n/a |

## Where files live

- Raw lists: `./data/lists/`
- Scored and enriched lists: `./data/scored/`
- Drafted sequences: `./data/sequences/`
- Suppression files: `./data/exclusions/`

`data/` is in `.gitignore`.

## Plays

### Play 1: a list for one segment

1. Claude writes down the segment, for instance "A accounts with a dispatcher job post".
2. Claude drafts the Apollo search (filters, expected count) and shows it. **Wait for yes**, since revealing emails can spend credits.
3. Two people per account: the owner or GM, and the dispatch manager.
4. Claude removes customers, open deals, the DNC file and competitors, and reports how many it removed.
5. Output: `./data/lists/dispatcher-posts-2026-03-02.csv`.

### Play 2: research and score

1. For each account: branch count, technician headcount, recent acquisitions, the job post link and date.
2. Rank A, B or C, with one sentence on why now.
3. Empty fields stay empty.
4. Clay enrichment: Claude names the table, the rows and the columns, and **waits for yes**, starting with 10 rows.

### Play 3: write the sequence

1. Four emails on day 0, 3, 8 and 15, plus one LinkedIn note.
2. Each email's personal line comes from the research file; prospects without a usable fact are listed instead of getting a vague line.
3. Every email ends with an opt-out line.
4. Output: `./data/sequences/dispatcher-posts-2026-03-02.md`.

### Play 4: put it live

1. Claude prepares the Instantly import and a summary: campaign name, 64 people, four mailboxes, 30 a day per mailbox, Tuesday to Thursday 8:00 to 11:00 in the prospect's time zone.
2. It shows the summary and **waits for yes**, then creates the campaign paused.
3. Starting it is a separate yes.
4. LinkedIn notes are sent by the sales lead by hand.

## Results log

### Dispatcher job posts, March 2026 (all numbers fictional)

| | Count |
|---|---|
| Contacted | 64 |
| Replied | 8 |
| Positive | 5 |
| Meetings | 3 |

- Repeat: naming the exact job title from their post in the subject line.
- Drop: the day-15 email; no reply came from it.
- Next: test the acquisition angle on B accounts that bought a competitor in the last year.
