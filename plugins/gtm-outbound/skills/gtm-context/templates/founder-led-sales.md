# GTM context: founder doing the selling

<!-- For a founder who sells personally, with a few hours a week and a small toolset. The goal is good conversations per hour spent, not volume. Fill the [BRACKETS]; leave unknowns as brackets. -->

## Approval rule

Claude helps me find people and draft messages. It never acts in my name on its own. Before it looks someone up in a paid tool, adds or changes a CRM record, schedules or sends an email, or prepares a LinkedIn message to send, it shows me the exact thing and waits for my yes in the chat. Read every step below with that in mind, even the ones written as if they just happen.

## Me and the company

- Founder: [YOUR_NAME], [ROLE]
- Company: [COMPANY_NAME], [ONE_LINE_ON_WHAT_YOU_DO]
- Why I started it (the short, true version I can use in a message): [STORY_IN_ONE_LINE]
- Time I give to prospecting each week: [HOURS]

## Who I want to talk to

- Companies: [INDUSTRY], [HEADCOUNT_RANGE], [STAGE], [REGION]
- People: [TITLE_1] first, [TITLE_2] if [TITLE_1] is not reachable
- Signs a company is ready: [FOR_INSTANCE "just hired its first salesperson"], [ANOTHER_SIGN]
- Signs it is not: [FOR_INSTANCE "fewer than N staff"], [FOR_INSTANCE "already signed with a larger vendor"]

### What my real customers have in common

<!-- Fill this from closed deals, not from hopes. Update after every few new customers. -->

| Customer (or code name) | Size | How they found me | What made them buy | Deal size | Days to close |
|---|---|---|---|---|---|
| [CUSTOMER] | [SIZE] | [SOURCE] | [TRIGGER] | [AMOUNT] | [DAYS] |

Patterns so far: [THREE_LINES_ONCE_THERE_ARE_ENOUGH_DEALS]

## Good reasons to write this week

- They talked publicly about the problem I solve: [WHERE, for instance LinkedIn, a podcast, a community]
- Someone we both know could introduce me: [HOW_I_TRACK_THIS]
- They reacted to something I posted
- Funding, hiring or a new leader in the last [N] days
- [YOUR_OWN_TRIGGER]

## How I write

- Voice: [FOR_INSTANCE "short, first person, like a note to a peer"]
- Length: [N] words at most
- First line is about them, never about me or the company
- The ask: [FOR_INSTANCE "a question they can answer in one line"]
- Sign-off: [FIRST_NAME_ONLY or FULL_SIGNATURE]
- Never: [PHRASES_I_DISLIKE]

## People I never contact

- Customers and anyone in an open deal (from the CRM or `[./data/customers.csv]`)
- Anyone who said no: `[./data/do-not-contact.csv]`; anyone who asked not to be contacted: `./data/suppression.csv`
- Competitors: [DOMAINS, for instance rival-one.example]
- [COMPANIES_OUTSIDE_MY_SIZE_RANGE]

## Tools

Setup: `docs/mcp-servers.md` in the go-to-market-orchestrator repo. Names here, never keys.

| Job | Tool | How Claude reaches it |
|---|---|---|
| Finding people | [FOR_INSTANCE Apollo, or LinkedIn by hand] | Official MCP server where one exists / CSV export / by hand |
| Email | [FOR_INSTANCE my own mailbox] | Claude drafts; I send |
| CRM | [FOR_INSTANCE Attio, a spreadsheet] | Official MCP server where one exists / CSV |
| Enrichment, if any | [FOR_INSTANCE Clay] | Clay MCP server / CSV export |
| Booking | [FOR_INSTANCE a calendar link] | Link in my signature |

## Files

- People to contact: `./data/prospects.csv`
- Drafts waiting for me: `./data/drafts/`

## My weekly routine

### Monday: pick this week's people

1. Claude checks the triggers above for the accounts in `./data/prospects.csv` and lists the ones with something new, each with a link and a date.
2. Claude suggests the [N] best for this week and says why for each, in one line.
3. If an email address needs a paid lookup, Claude says which tool and how many lookups, and **waits for my yes**.

### Tuesday: drafts

1. Claude writes one draft per person into `./data/drafts/`, each built on the fact it found.
2. If it has no real fact for someone, it says so instead of writing a generic line.
3. I edit and send them myself, or tell Claude in the chat to send a named draft through a connected tool, after it shows me the final text.

### Follow-ups

1. Claude keeps a follow-up list: who, last touch, next touch date, and what new thing to say.
2. Suggested spacing: [FOR_INSTANCE "about a week, then a last short note"]. I adjust it from my own replies.
3. A reply asking me to stop goes straight to the do-not-contact file; no further follow-up.
4. CRM updates (stage, notes, next step) are listed for me to approve, then written.

### Once a month: check the pattern

1. I drop an export of closed and lost deals in `./data/`.
2. Claude updates the "what my real customers have in common" table and proposes changes to who I target. I decide.

## Results

_Nothing logged yet._ After each week: people contacted, replies, conversations booked, and one thing to change.
