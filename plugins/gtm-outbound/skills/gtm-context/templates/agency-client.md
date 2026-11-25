# GTM context: agency running outbound for a client

<!-- One copy per client, saved as that client's folder CLAUDE.md (for instance clients/[client-slug]/CLAUDE.md). Start Claude Code inside the client folder so only this client's lists and rules are loaded. Keep client details out of any CLAUDE.md in a parent folder. Fill the [BRACKETS]. -->

## Two different approvals

They are not the same thing, and one never replaces the other.

1. **Client sign-off** (a business step). The client approves copy, segments and proof points before a campaign is built. The client's contact and turnaround are below. Copy the client has signed off can be reused without going back to them for each campaign, if the client agreed to that in writing.
2. **The yes in the chat** (always, every time). Before Claude reaches outside this folder (enriching or importing contacts, writing to the client's CRM, creating or changing a campaign, scheduling or sending anything, deleting anything), it shows the exact action and waits for a yes from the agency person running this session. Client sign-off does not count as this yes, and no step in this file skips it.

## The client

- Client: [CLIENT_NAME], [CLIENT_SITE]
- What they sell: [ONE_LINE]
- Why buyers choose them, in their words: [QUOTE_FROM_ONBOARDING]
- Sign-off contact: [NAME, ROLE] (contact details live in the agency CRM, not in this file)
- Turnaround they promised: [FOR_INSTANCE two working days]
- Contract scope: [CHANNELS, VOLUME_CAP, START_AND_END_DATES]

## Their market

| | Target | Avoid |
|---|---|---|
| Industries | [LIST] | [LIST] |
| Company size | [RANGE] | [RANGE] |
| Regions | [LIST] | [LIST, with the reason, for instance consent rules] |
| Titles | [PRIMARY_TITLES], then [SECONDARY_TITLES] | [TITLES] |

Ranking: [CLIENT_SPECIFIC_RULE, for instance "A = fit plus a hiring trigger in the last 60 days"].

Triggers the client cares about: [TRIGGER_1], [TRIGGER_2], [TRIGGER_3]. Each one Claude reports comes with a source link and date.

## Their voice

- Tone: [SUMMARY_OF_THEIR_BRAND_GUIDE]
- Product name exactly as written: [NAME]
- Words they use and words they never use: [LISTS]
- Proof points they have cleared for use: [LIST, each with the date the client cleared it]
- Things we must never say: [FOR_INSTANCE naming a competitor, quoting a customer not on the cleared list]
- Sender identity: [CLIENT_DOMAIN / AGENCY_DOMAIN / ALIAS], signed as [NAME]
- Copy the client has signed off for reuse: `[./approved-copy/]` (each file dated and named after the campaign it was approved for)

## Who is off limits

- The client's customers: `[./data/exclusions/customers.csv]`
- The client's open deals: `[./data/exclusions/open-deals.csv]`
- The client's do-not-contact list: `[./data/exclusions/dnc.csv]`
- Their competitors: [DOMAINS, for instance rival-one.example]
- Agency-wide: anyone who unsubscribed from any of our campaigns for this client, addresses that bounced before, personal mailboxes unless the client sells to individuals

## Tools

Setup: `docs/mcp-servers.md` in the go-to-market-orchestrator repo. Server names here, never keys or passwords. Use names that include the client (for instance `hubspot-[client]`, `instantly-[client]`) and add them to gtm-guard's `extra_servers` setting so their write calls are checked too.

| Job | Tool | How Claude reaches it | Belongs to |
|---|---|---|---|
| Contacts | [FOR_INSTANCE Apollo] | Official MCP server where one exists / CSV export (server `[NAME]`) | Agency |
| Enrichment | [FOR_INSTANCE Clay] | Clay MCP server / CSV export | Agency |
| Sending | [FOR_INSTANCE Instantly, lemlist, Smartlead] | Official MCP server where one exists / CSV import (server `[NAME]`) | Agency |
| CRM | [CLIENT_CRM] | Official MCP server where one exists, signed in with the account the client gave us | Client |
| Reporting | [FOR_INSTANCE a shared sheet] | CSV | Both |
| Alerts | [FOR_INSTANCE a shared Slack channel] | gtm-notify plugin | Both |

Mailboxes: [NUMBER] on [DOMAINS], warm-up status [STATUS], daily limit [N] per mailbox.

## Files (inside this client's folder)

- Lists: `./data/lists/`
- Drafts sent for sign-off: `./data/for-review/`
- Client sign-off records: `./data/sign-off/` (who approved what, when, by which channel)
- Weekly reports: `./data/reports/`

## Plays

### Onboarding

1. Collect from the client: ICP notes, brand guide, cleared proof points, competitor list, customer and open-deal exports, do-not-contact list, sending domains, any legal or sector rules.
2. Claude fills this file from those, lists what is still missing, and drafts a one-page summary for the client to confirm.
3. CRM access is set up through the vendor's MCP server sign-in; no password goes into any file.

### Build a campaign

1. Claude drafts the segment, the list (after removing everyone off limits) and the sequence, and saves a review pack to `./data/for-review/`: [N] sample rows, the full sequence, the planned schedule and volume.
2. You send the pack to the client. Their sign-off is recorded in `./data/sign-off/`.
3. When signed off, Claude prepares the import and the campaign settings and shows them. **Waits for your yes** before creating anything, and creates the campaign paused.
4. Starting the campaign is its own step with its own yes, or you start it in the tool yourself.

### Weekly report

Claude writes `./data/reports/[week].md` from the sending tool's and CRM's numbers: contacted, replies, positive replies, meetings, how many replies fit the ICP, deliverability warnings (bounces, complaints), best and worst performing step, and what to test next. It reads data only; any fix it suggests in a tool is listed for a yes.

### Tune after [N] weeks

1. Claude compares results with the targets agreed with the client: reply rate [TARGET], meetings [TARGET].
2. It names the likeliest cause for a gap (list, angle, copy, timing, deliverability) and proposes one test at a time.
3. Changes to copy go back through client sign-off; changes to campaigns need the yes in the chat.

## Results log

_Nothing logged yet._ Per campaign: dates, segment, volume, sign-off date, replies, meetings, client feedback, what changes next.
