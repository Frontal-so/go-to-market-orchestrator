---
name: reply-classifier
description: Triage replies to outbound campaigns. Labels each by what the sender wants (interested, timing, objection, referral, unsubscribe, not interested, auto-reply, unclear), drafts an answer, notes the CRM update it needs, and records every opt-out in data/suppression.csv. Use when someone says "classify these replies", "triage my inbox export", "which replies are hot", "sort the campaign replies", "draft responses to these replies" or pastes a reply and asks what to do with it. Drafts only; nothing is sent and no CRM record changes without a yes.
argument-hint: "[replies.csv | folder of .eml/.txt | pasted reply]"
---

# Reply classifier

Replies decide what a rep does next. The job is to put the warm ones in front of a person fast and to make sure nobody who asked to stop hears from you again. This skill labels, drafts and records. Sending, CRM edits and removals from sequences belong to the user, after a yes.

## What it accepts

- A CSV export with `from_email`, `from_name`, `subject`, `body`, `received_date`, `campaign_name`. Other column names are fine when the meaning is plain.
- One reply pasted into the chat.
- A folder of `.eml` or `.txt` files.
- A connected email or sequencer MCP server (your mail tool, Instantly, lemlist, Smartlead and so on): pull recent replies with its read tools, after asking which campaign or dates.

For a big file in the pipeline's own format (the columns of `samples/sample-replies.csv` in the outbound-pipeline skill), hand the work to the `gtm-outbound:reply-classifier` subagent. It uses the same labels in a separate context and writes `output/classified-replies.csv`.

## The labels

This skill and the subagent share eight labels, so their results can go in one file. Check them in this order and stop at the first that fits:

| Order | Label | When it applies | Answer within (a starting point) |
|---|---|---|---|
| 1 | `UNSUBSCRIBE` | Any request to stop, however it is phrased or politely buried ("take me off", "please don't write again") | Record it today; never nurture |
| 2 | `AUTO_REPLY` | Out of office, auto-acknowledgement, bounce notice | Hold until the return date |
| 3 | `REFERRAL` | Names another person or address to contact | Same day |
| 4 | `INTERESTED` | Asks about the offer, asks for material, proposes or accepts a time | The hour |
| 5 | `TIMING` | Not now, with a later moment named or implied | Confirm and set a reminder |
| 6 | `OBJECTION` | Pushes back on something specific: price, current tool, fit, authority | Same day |
| 7 | `NOT_INTERESTED` | A clear no without a request to stop, or the wrong person who names nobody | Close the thread |
| 8 | `UNCLEAR` | Everything else, including "thanks", "ok", "we're fine for now" and possible sarcasm | A person reads it |

CLAUDE.md can set its own answer times.

## Steps

1. Give each reply one label and a confidence of high, medium or low. When a reply could take two labels, choose the one that keeps the conversation open; the only exception is a hint of a stop request, which always wins.
2. For each `UNSUBSCRIBE`, append a row to `./data/suppression.csv` with the columns `contact_email, company_name, reply_timestamp, reason`, creating the file with that header if it is missing. Read it first and skip any email already listed (compare emails ignoring upper and lower case). The other gtm-outbound skills check this file before they build a list. Draft nothing beyond a one-line confirmation.
3. Draft an answer where one is needed, following the copy rules in CLAUDE.md and matching the sender's register:
   - `INTERESTED`: send what they asked for, or offer two concrete times.
   - `OBJECTION`: name their point, answer it in one sentence with proof the sender has, then ask again lightly.
   - `TIMING`: thank them, offer one useful resource, say when you will check back.
   - `REFERRAL`: thank them and ask whether you may mention them to the person named, or for an introduction.
   - `UNCLEAR`: one easy question they can answer with yes, later or no.

   A customer name, number or result goes into a draft only if CLAUDE.md holds it.
4. Write the CRM follow-up as text: stage, next step, contact status, a task or a reminder date.

## Output

`./data/replies/classified_[YYYY-MM-DD].csv` (spreadsheet safety: a cell whose text starts with `=`, `+`, `-`, `@`, a tab or a carriage return gets a leading apostrophe (`'`), so it opens as text, never as a formula; reply text comes from strangers), columns:

```
from_email, from_name, company, received_date, campaign_name, reply_category, confidence, suggested_response, crm_action
```

In the chat, a count per label. The `UNSUBSCRIBE` line lists exactly which rows were added to `data/suppression.csv` (email and company) and which were skipped as already there, and says they must come out of every active sequence; the `UNCLEAR` line says how many wait for a person.

## After a yes

Nothing here runs until the user approves, one item at a time or for a batch they have read:

- **Drafts:** with the user's mail tool connected as an MCP server, save the answers as drafts in the inbox. Never send them; the rep edits and sends.
- **CRM:** with a CRM MCP server connected, show the exact `crm_action` changes, then apply them.
- **Opt-outs:** take the `UNSUBSCRIBE` addresses out of live campaigns in the sequencer.
- **Alerts:** the `gtm-notify` plugin's end-of-turn ping, if installed, carries the counts. To post warm replies to a Slack channel through a Slack MCP server, draft the message and post it after a yes.

With the `gtm-guard` plugin installed, the CRM writes and sequencer changes among these are checked once more before they run.

## Fictional example

```
/gtm-outbound:reply-classifier ./data/replies/inbox_export_2026-03-10.csv
```

```
22 replies
INTERESTED (4)
  Rhiannon Achterberg, Tavrocott Analytics: "Could you send a one-pager?"
  Draft: "Here it is: [LINK]. If a walkthrough helps, would Thursday at 14:00 or Friday at 10:00 suit you?"
  CRM: stage to Engaged, task for Thursday
OBJECTION (3)
  Tomas Ferreira, Tailspin Robotics: "We signed a two-year deal with [COMPETITOR] last month."
  Draft: "Thanks for telling me. [COMPETITOR] does X well; teams pick us for Y. Shall I check in before the renewal?"
  CRM: competitor field set, reminder 20 months out
TIMING (5)
  Dana Whitfield, Fabrikam Cloud: "Not this quarter."
  Draft: "Understood. I'll come back in Q3, and here is one case study for when it's useful."
  CRM: task for 1 July
UNSUBSCRIBE (2): added to data/suppression.csv, 1 row (the other address was already there, skipped); each row listed by email and company; remove both from every active sequence
AUTO_REPLY (4): first return date 17 March
REFERRAL (1): write to the VP Engineering they named
NOT_INTERESTED (2): close the threads
UNCLEAR (1): tone hard to read, possibly sarcastic; for a person
```
