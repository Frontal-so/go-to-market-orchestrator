# Never contact

The list every skill checks before it puts a name on a list, writes a line of copy or suggests an action. If an account or person is here, they are dropped, and the output says why.

Keep the lists as files (CSV or one domain per line) and point to them from here, so they can be refreshed without editing this page.

## The lists

| List | What goes on it | File | Who keeps it current | How often |
|---|---|---|---|---|
| Unsubscribed and opted out | Anyone who asked not to be contacted, by any channel | [e.g., data/suppression.csv] | [OWNER] | the same day it happens |
| Do not contact | Legal requests, partners' staff, investors, people a founder asked us to leave alone | [FILE] | [OWNER] | when it changes |
| Customers | Current customer domains, so outbound does not hit them | [FILE or CRM export] | [OWNER] | weekly |
| Open deals | Accounts already in an active opportunity | [CRM VIEW] | [OWNER] | before each campaign |
| Competitors | Their domains and staff | [FILE] | [OWNER] | quarterly |
| Bounced | Addresses that hard bounced | [FILE] | [OWNER] | after each send |

The first two lists always win. Nothing in a later rule, a template or a request in the chat puts someone back on a list after they opted out. If a user asks for that, Claude says it cannot and points to this section.

## Rules by attribute

Fill only the ones that apply.

- **Countries or regions we do not contact:** [LIST, and the reason, e.g., no legal basis yet, no support hours]
- **Industries we skip:** [LIST]
- **Titles we never email:** [e.g., students, interns, recruiters, unless the campaign targets them]
- **Email domains we do not send to:** [e.g., free webmail addresses, unless we target freelancers; role addresses like info@ or sales@]
- **Company size or stage outside our reach:** [RULE]

## How a skill applies it

1. Before research or enrichment, remove anything on the lists above, so no credits are spent on people we will never contact.
2. Before writing copy, check again (a list may have changed since the file was built).
3. Write the removed rows to a separate file with the reason (`excluded.csv`, column `reason`), so the user can see what was dropped and why.
4. If a list file is missing or older than its refresh window, say so before going on.

## Fictional example (Quorvane Data, a made-up data quality vendor)

- Unsubscribed: `data/suppression.csv`, updated by the reply-classifier skill whenever a reply asks to stop.
- Customers: weekly export of closed-won accounts from the CRM into `gtm/customers.csv`.
- Competitors: `rival-observe.example`, `rival-lineage.example`, `rival-quality.example`.
- Regions: none excluded; Europe only with a documented legitimate-interest assessment on file.
- Titles: no interns, students or recruiters.
- Domains: no free webmail; no role addresses.
