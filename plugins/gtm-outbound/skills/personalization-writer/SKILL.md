---
name: personalization-writer
description: Write personalized cold email first lines, full cold emails, LinkedIn connection notes, LinkedIn DMs or follow-ups for a list of prospects, from their signals and your copy frameworks, each with the source of its personal detail and a confidence score. Use when someone asks to "write first lines for this list", "personalize these cold emails", "write LinkedIn connection notes", "draft follow-ups for these prospects", "write icebreakers" or "make this outreach less generic". Writes drafts to a file; never sends.
argument-hint: "[prospects.csv] [first_line|full_email|linkedin_connection|linkedin_dm|follow_up]"
---

# Personalization writer

Turns a prospect list into draft messages that each say something true about one person. The drafts go to a CSV that a person reads and edits. This skill sends nothing and loads nothing into a sending tool.

## Before you start

Collect four things. If any is missing, ask for all the gaps together in a single message.

| What | Accepted values |
|------|-----------------|
| The list | A CSV or JSON file. Each row needs `contact_name`, `company_name`, `contact_title`, `signal` and `personalization_note`. A file from `/gtm-outbound:lead-enrichment` already has them. |
| What to write | `first_line`, `full_email`, `linkedin_connection`, `linkedin_dm` or `follow_up` |
| The angle | `signal_based`, `problem_led`, `social_proof` or `content_based` |
| Follow-up slot (follow-ups only) | `follow_up_1`, `follow_up_2` or `breakup` |

Then open CLAUDE.md for the copy frameworks, the tone rules and the proof points, and `input/icp-config.csv` when the project has one. No frameworks in CLAUDE.md? Offer `/gtm-outbound:gtm-context` to set them up, or go ahead in a plain, direct style and apply the checks further down.

## Writing one message

Work row by row.

1. Choose the one signal that gives the best reason to write today: a new role, a funding round, a tool they adopted, something they published.
2. Find the template in the copy frameworks that fits that signal and the angle.
3. If the row says too little to be personal, you may run one web search for a fresher detail, such as a post they wrote last week or a company announcement. Record the page you took it from.
   A detail that comes only from the user's file and was never checked (in the pipeline it is marked `input CSV (not checked)`) is the user's claim, not a fact you found. Do not state it to the prospect as fact until the user confirms it: prefer a sourced detail, or mark the row for review and say which detail needs confirming.
4. Draft the message inside the tone rules and the length limit for its type.

Proof is borrowed, never made up. A customer name, a result or a quote may appear only if CLAUDE.md or the ICP config states it. When there is nothing to borrow, the message goes out without proof.

## Checks on every draft

Read each draft back and fix it until all of these hold:

- Read aloud, it could pass for a note one colleague sends another; nothing in it smells of a mail merge.
- Put another prospect's name on it and it falls apart, because one detail fits this person only.
- What it asks for is small: a reply to a question, or a yes to receiving something. A meeting request is too big for a first message.
- Plain words throughout. Sales jargon, `!` and emoji are cut.
- It fits the length limit for its type.

When the row is too thin for a real personal line, do not write a fake one. Score it `low` and say in the source column what is missing.

## LinkedIn connection notes

How many invitations may carry a note depends on the sender's account. Premium members can add a note to every request. On a free (Basic) account the allowance is only a few a month, and LinkedIn's own help pages disagree on the figure: three at https://www.linkedin.com/help/linkedin/answer/a563153 and five at https://www.linkedin.com/help/linkedin/answer/a550555. Ask the sender to check their account. Whatever the account, a note can be up to 200 characters, spaces included (https://www.linkedin.com/help/linkedin/answer/a563153): count, do not estimate. For a free account, write notes for the best prospects only and put `send_without_note` on every other row.

## What you hand back

Save the drafts to `./data/outreach/[YYYY-MM-DD]_[MESSAGE_TYPE]_personalized.csv`. One row per prospect (spreadsheet safety: a cell whose text starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading apostrophe (`'`), so it opens as text, never as a formula), in this column order:

1. `contact_name`
2. `contact_email`
3. `company_name`
4. `message_type`
5. `subject_line`
6. `message_body`
7. `personalization_source`: where the personal detail came from: a URL, or `input: <column> (not checked)` for a detail taken only from the user's file
8. `confidence_score`: `high` when the signal is strong and the detail is specific, `medium` when the context is fair, `low` when it is thin and needs a person to look before it is used

In the chat, show three drafts: the best, a middle one and the weakest. Loading the file into Instantly, lemlist or any other sender is left to the user.

## Sample

```
/gtm-outbound:personalization-writer ./data/enriched/fintech_q2_enriched.csv full_email
```

One row of the result (all names invented):

```
contact_name: Priya Ramos
company_name: Fennimarch Ledger
subject_line: The revenue ops lead you are hiring
message_body: Priya, a first revenue ops hire tends to inherit the CRM
cleanup nobody had time for. If that is on the list for Fennimarch, I can
send a short checklist for that first month.
[ONE PROOF POINT FROM YOUR CASE STUDIES]
personalization_source: Fennimarch careers page, Revenue Operations Lead role, posted 4 days ago
confidence_score: high
```
