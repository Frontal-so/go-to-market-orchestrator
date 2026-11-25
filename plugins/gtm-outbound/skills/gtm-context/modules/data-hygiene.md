# Keeping lists clean

Bad rows waste credits, bounce, and hurt your sending reputation. This page sets the checks Claude runs on a list before it is used, and the routine clean-ups for your CRM.

One rule covers everything below: **Claude may read, check and report on its own. It never merges, archives, deletes, enriches or writes to a tool on its own.** For each of those, it shows the exact action first (which tool, which records, which fields, the credit cost if the tool states one) and waits for your yes in the chat. A yes covers that one action, not the next one.

## Checks before a list is used

Claude runs these on the file and writes the results to new files; the original file is left as it was.

| Check | What fails | What Claude does |
|---|---|---|
| Duplicates | Same email, or same person at the same company spelled two ways | Keeps one row, lists the others in `duplicates.csv` |
| Missing basics | No email (for email campaigns), no company domain, no first name | Moves the row to `needs-data.csv` |
| Placeholder values | "Unknown", "N/A", "test", a title like "Employee" | Moves the row to `needs-data.csv` |
| Domain mismatch | The email domain and the company website do not belong together | Flags it for review |
| Role or free addresses | info@, sales@, free webmail (unless your ICP allows it) | Moves the row to `excluded.csv` with the reason |
| On a never-contact list | See exclusion-rules.md | Moves the row to `excluded.csv` with the reason |
| Formatting | Mixed case names, stray spaces, country spelled five ways | Normalises in the cleaned copy and says what it changed |

At the end, Claude reports: rows in, rows ready, rows moved and why.

## Filling gaps

If rows in `needs-data.csv` could be completed by an enrichment tool, Claude says how many rows, which fields, which tool, and the credit cost if known, then waits for your yes. Without a yes, the rows stay where they are.

## Routine CRM clean-ups

Decide which of these you want and how often. Each one starts as a read-only report; any change to the CRM needs your yes for that batch.

| Clean-up | How often | What Claude reports | The change it may propose |
|---|---|---|---|
| Duplicate contacts and companies | [e.g., monthly] | Pairs that look like the same record, and why | A merge list for you to approve |
| Hard bounces | [after each send] | Addresses that bounced | Marking them as bounced and adding them to the bounce list |
| People who changed jobs | [e.g., quarterly] | Contacts whose public profile shows a new company | Updating the record, or a fresh contact at the old account |
| Stale records | [e.g., quarterly] | Contacts with no activity in [N] months | Archiving them, as a list for you to approve |
| Customer list for exclusions | [e.g., weekly] | Current customer domains | Refreshing the exclusion file (a local file, no CRM write) |

## Fictional example (Quorvane Data)

A list of 1,000 rows from a conference export:

- 38 duplicates kept once; 61 rows without a usable email moved to `needs-data.csv`; 24 free-webmail rows and 9 competitor rows moved to `excluded.csv`.
- Claude asks: "61 rows are missing an email. Filling them through your enrichment tool spends its credits (its pricing page sets the cost per record). Run it on all 61, or test 10 first?" The user says yes to a test of 10.
- 868 rows are ready in `clean.csv`. Nothing was written to the CRM.
