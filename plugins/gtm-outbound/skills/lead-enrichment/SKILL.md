---
name: lead-enrichment
description: Enrich a CSV of companies or contacts with firmographics (size, industry, location), funding, tech stack, recent news and, if an enrichment tool is connected, work emails and titles; score each row against your ICP, apply your exclusion lists, and write a clean enriched CSV. Asks before any step that spends enrichment or verification credits. Use when someone says "enrich this list", "add employee count and funding to these accounts", "find emails for these contacts", "score this list against our ICP", "clean up this lead list" or "which of these are Tier 1".
argument-hint: "[file.csv] [basic|full]"
---

# Lead enrichment

## Task

Start from a bare list of accounts or people. Add the same set of fields to every record, score each one against the ICP, and set aside whatever the exclusion rules forbid. The result is one CSV the user can sort and read.

## Input

- A CSV or JSON file with at least one of: company names or domains, contact name plus company, LinkedIn profile URLs.
- Level: `basic` (company data only, from public web pages, no credits) or `full` (company plus contact data, usually from a paid enrichment tool).
- Your ICP and exclusion rules from CLAUDE.md. If there is no GTM context yet, suggest `/gtm-outbound:gtm-context` or ask for the ICP in one message.

## Where the data comes from

- **Company facts:** a web search tool and web fetch (company site, press releases, job posts, public profiles). Free.
- **Contact data (emails, phones, titles):** an enrichment MCP server the user has connected, such as Apollo, Clay or another provider. These calls usually spend credits.
- Never guess an email from a name pattern and present it as found. Never fill a field you did not read somewhere; leave it empty and note why.

## Before spending credits

Before the first call that enriches contacts, reveals emails or phones, or verifies emails, show the user:
- how many records you are about to send, and which fields you will request;
- which tool you will use, and the cost per record if the tool states one (otherwise say you do not know it).

Wait for a yes. Run a small batch first (about 10 records) and show the result before running the rest. If the `gtm-guard` plugin is installed it will also ask at each credit-spending call.

## Instructions

1. **Read the input** and check the format. List rows missing the fields you need.
2. **Apply exclusions first** (so you do not pay to enrich records you will drop): competitor domains, existing customers, open deals owned by someone else, do-not-contact and unsubscribe lists (including `./data/suppression.csv` if it exists), and any territory rules in CLAUDE.md. Record the reason per excluded row.
3. **For each company:** employee count, industry, headquarters, founding year, funding (total, last round, date), tech stack (from job posts or public pages), recent news with dates, LinkedIn company page URL. Note the source for anything non-obvious.
4. **For Tier 1 candidates, go deeper:** recent news, executive interviews, stated priorities, competitive moves, using web search or a connected research MCP server. This is what makes personalization specific.
5. **For each contact (`full` only, after the yes above):** work email and its verification status as reported by the tool, current title, seniority, LinkedIn URL, time in role.
6. **Score** each record against the ICP rubric in CLAUDE.md: Tier 1 / Tier 2 / Tier 3, and flag records below the ICP minimum.
7. **Add a `personalization_note`** to the records in the top two tiers: a single sentence naming the best sourced signal for that record.

## Output

CSV at `./data/enriched/[INPUT_FILENAME]_enriched.csv` (spreadsheet safety: a cell whose text starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading apostrophe (`'`), so it opens as text, never as a formula):

```
company_name, company_domain, industry, employee_count, revenue, revenue_source, revenue_date, funding_stage, last_funding_date, tech_stack, hq_location, contact_name, contact_email, email_status, contact_title, contact_linkedin, seniority, signal, signal_source, tier_score, personalization_note, exclude_reason
```

`revenue` stays empty unless a source states a figure; then `revenue_source` holds its URL and `revenue_date` the date of the figure. Never estimate it.

Summary in the chat: records processed, enriched, excluded (by reason), tier counts, and credits used if the tool reported them.

The file stays in the project. Pushing records into a CRM or a sending tool is a separate step that the user approves.

## Example

```
/gtm-outbound:lead-enrichment ./data/prospects/saas_companies_march.csv full
```

What a run might report (made-up numbers): `./data/enriched/logistics_accounts_enriched.csv` written; 80 records read; 9 set aside (2 competitors, 4 current customers, 3 under the ICP size floor); 71 enriched, of which 15 are Tier 1, 38 Tier 2 and 18 Tier 3.
