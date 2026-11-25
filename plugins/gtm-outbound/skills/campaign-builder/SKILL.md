---
name: campaign-builder
description: Build a complete outbound micro-campaign from a segment definition - prospect list, exclusions, enrichment and scoring, a personalized email (and optional LinkedIn) sequence, a deliverability check and import-ready files for Instantly, lemlist, Smartlead or another sender - packaged in one folder for review. Asks before spending credits and never launches a campaign. Use when someone says "build a campaign for", "spin up a micro-campaign", "campaign for Series B companies hiring SDRs", "get this segment ready for Instantly/lemlist/Smartlead", "build a cold email campaign" or "package this list and sequence for import".
argument-hint: "[segment description]"
---

# Campaign builder

## Task

Take one segment from an idea to a folder the user's sending tool can import. Along the way you pick the accounts and the people, drop everyone who must not be contacted, add data and a score, write the copy and check the sending basics. Everything lands in that folder for the user to read; only the user launches.

## Input

Ask for anything missing in one message:
- **Segment:** ICP tier, signal and filters (for example "Tier 1 logistics software firms in Canada, 50 to 250 staff, with an open RevOps role").
- **Goal:** what a reply should lead to, such as a booked call, a seat at an event or a download.
- **Volume:** for example 100 prospects.
- **Channel:** `email` | `linkedin` | `multi_channel`.
- **Sequence length:** for example 3 emails over 14 days.
- **Angle:** `signal_based` | `problem_led` | `social_proof`.
- **Sending platform:** for example Instantly, lemlist, Smartlead.

Uses the ICP, exclusion rules, copy frameworks and proof points in CLAUDE.md (see `/gtm-outbound:gtm-context`).

## Phase 1: Prospect list

1. Find companies and contacts for the segment with what is connected: a prospecting MCP server (for example Apollo or Clay) or a list the user provides. What costs credits depends on the vendor and the action. On Apollo, for example, people search is free, while company search and enrichment spend credits (https://docs.apollo.io/docs/apollo-mcp, checked 2026-11-25). Read the tool's stated cost before each call, and treat any call whose cost you cannot see as one that spends credits.
2. **Before any credit-spending call**, show how many records, which fields, which tool and the cost per record if the tool states it. Wait for a yes. Start with a batch of about 10.
3. Keep 2-3 contacts per company that match the target personas.
4. Apply exclusions: competitors, customers, open deals, do-not-contact and suppression lists (including `./data/suppression.csv` if it exists), territory rules.
5. Output: `prospects_raw.csv` and `exclusions_applied.log` (what was removed and why).

## Phase 2: Enrichment and scoring

1. Add company data, tech stack, funding and recent news, with sources (see `/gtm-outbound:lead-enrichment`).
2. Pick the primary sourced signal per prospect.
3. Score Tier 1 / 2 / 3. Drop Tier 3 unless the volume target needs them, and say so.
4. Write a one-sentence personalization note per prospect.

## Phase 3: Copy

1. Pick templates from the copy frameworks for the angle.
2. Write the sequence, for example:
   - Email 1: first touch (signal or problem).
   - Email 2: value follow-up (day 3-4).
   - Email 3: proof (day 7-8), using only proof points from CLAUDE.md.
   - Email 4 (optional): breakup (day 14).
3. Personalize each email per prospect with their signal and note.
4. Multi-channel: a LinkedIn connection note (200 characters at most, LinkedIn's limit) and a DM. A free LinkedIn account can add a note to only a few invitations a month (see below), so write notes for the top prospects and plan the rest without one.
5. Check every message: one prospect-specific detail, within the word limit, soft ask, a plain opt-out line in every email.

## Phase 4: Deliverability check

Before packaging, check the sending setup against the rules below and list any gap in `campaign_summary.md`. Ask the user what you cannot see (DNS records, daily volume per domain).

### Deliverability and opt-outs (2026)

- **Gmail** (Google's email sender guidelines): every sender to Gmail accounts needs SPF or DKIM, valid forward and reverse DNS (PTR) for sending IPs, TLS, messages formatted per RFC 5322, and a spam rate in Postmaster Tools below 0.3%. Senders of more than 5,000 messages a day to Gmail accounts also need SPF and DKIM, a DMARC record (the policy can be none) with the From domain aligned to SPF or DKIM, and, for marketing and subscribed messages, one-click unsubscribe (List-Unsubscribe headers per RFC 8058) plus a visible unsubscribe link. Google advises keeping the spam rate below 0.10% and never reaching 0.30%.
- **Yahoo** (sender best practices): all senders need SPF or DKIM, a spam rate below 0.3%, valid forward and reverse DNS, and RFC 5321 and 5322 compliance. Bulk senders also need SPF and DKIM, a passing DMARC policy of at least p=none, From alignment, one-click unsubscribe for marketing and subscribed messages (the RFC 8058 POST method is recommended), a visible unsubscribe link, and unsubscribes honored within 2 days.
- **Outlook.com** (Microsoft, domains sending over 5,000 emails a day): SPF and DKIM must pass and DMARC must be at least p=none, aligned with SPF or DKIM. Enforcement started on 5 May 2025; failing messages can be rejected with "550; 5.7.515 Access denied". Microsoft also asks for a valid From or Reply-To address, a working unsubscribe link and regular removal of invalid addresses.
- **LinkedIn:** free (Basic) accounts can add a personal note to only a few invitations a month (LinkedIn's help pages give three in one place and five in another), so check your own account; Premium members can add one to every request. Each note can be up to 200 characters. Invitations are limited for every account, and reaching the limit can stop you sending invitations for a while. Sources: https://www.linkedin.com/help/linkedin/answer/a563153 and https://www.linkedin.com/help/linkedin/answer/a550555
- Rules on contacting people differ by country, and this skill cannot tell you which apply. Before any list is used, settle these with the user and write the answers in `campaign_summary.md`:
  1. Which countries are the recipients in?
  2. What legal basis does the user rely on to contact them, and has their own legal or privacy contact agreed?
  3. Where did each contact's data come from (an enrichment tool, an event list, a form, an export), and may it be used for outreach?
  4. How long will the data be kept, and where?
  5. How is an opt-out honoured across every tool that holds the contact (sender, CRM, `data/suppression.csv`)?
  6. Does the user's own company policy add rules for outbound?
- SPF, DKIM and DMARC are deliverability rules set by mailbox providers. Passing them says nothing about whether you may contact someone.

Sources (fetched 2026-11-25): https://support.google.com/a/answer/81126 · https://senders.yahooinc.com/best-practices/ · https://techcommunity.microsoft.com/blog/microsoftdefenderforoffice365blog/strengthening-email-ecosystem-outlook%E2%80%99s-new-requirements-for-high%E2%80%90volume-senders/4399730 · https://www.linkedin.com/help/linkedin/answer/a550555

## Phase 5: Package

1. Format the prospects for the platform's import: one row per contact with `email, first_name, last_name, company_name` plus one column per personalized field (for example `first_line`, `signal_note`). Map these columns to the platform's fields or custom variables on its import screen; check the platform's own docs for the variable syntax.
2. Write the sequence with its timing in `sequence.csv`.
3. Write `campaign_summary.md`: segment, volume and tier counts, sequence outline and timing, angle, planned send dates, deliverability gaps, three sample emails (strongest, middle, weakest personalization), and "Ready for approval: yes/no".
4. Stop and show the summary.

If the user then asks to create the campaign in their sending tool through a connected MCP server, show exactly what will be created, wait for a yes, create it **paused or as a draft**, and tell the user to review and launch it in the platform themselves. Do not activate, start or schedule sending. To post the summary to Slack or add a row to a tracking sheet through a connected MCP server, draft it and do it after a yes. The `gtm-guard` plugin, if installed, also asks at each of these calls.

## Output

Folder `./data/campaigns/[CAMPAIGN_NAME]/`:

```
[CAMPAIGN_NAME]/
├── prospects.csv              # import-ready prospect list
├── sequence.csv               # sequence steps with personalization
├── linkedin_messages.csv      # LinkedIn notes and DMs (multi-channel only)
├── campaign_summary.md        # overview, deliverability gaps, samples, approval line
└── exclusions_applied.log     # what was excluded and why
```

Spreadsheet safety: a cell whose text starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading apostrophe (`'`), so it opens as text, never as a formula. This applies to every CSV in the folder.

## Example

```
/gtm-outbound:campaign-builder Series B SaaS, 100-500 employees, hiring SDRs, US; book meetings; 100 prospects; email; 3 emails over 14 days; signal_based; Instantly
```

Output: `./data/campaigns/series_b_sdr_hiring_march/` with 100 prospects, a 3-step personalized sequence, a deliverability check, and import files for Instantly. Nothing is created in Instantly until the user says so.
