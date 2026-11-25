---
name: pipeline-reviewer
description: Read-only review of open deals from a CRM export or a connected CRM (HubSpot, Attio, Salesforce, Pipedrive and the like). Finds deals that went quiet, missed or are about to miss their close date, sit too long in one stage, rest on one contact or have no next step; marks each Red, Yellow or Green with one next move; writes a weekly pipeline note with coverage and weighted value when the data allows. Use for "pipeline review", "weekly pipeline report", "which deals are at risk", "forecast check", "deal hygiene", "what should I chase this week" or "prep my pipeline meeting". Changes nothing in the CRM; suggested updates wait for a yes.
argument-hint: "[pipeline_export.csv | crm] [all|my_deals|team:NAME]"
---

# Pipeline reviewer

A weekly read of the open pipeline: which deals need attention, what to do about each one, and how the whole book looks. The skill reads and reports. A change to a CRM record stays a suggestion until the user approves it.

## Before you start

Collect four things. Take each from the GTM context in CLAUDE.md when it is there, and ask once for whatever is missing.

1. **Where the deals live.** A CSV export, or a CRM connected as an MCP server (call its read and search tools only). A CSV needs one row per deal with these fields; other column names are fine when the meaning is plain:

   | Field | What it feeds |
   |---|---|
   | `deal_name`, `company`, `owner` | Naming the deal, filtering by scope |
   | `amount`, `stage` | Value per stage, coverage, weighting |
   | `created_date`, `close_date`, `last_activity_date` | Age, slippage, silence |
   | `next_step` | Whether anyone has a plan |
   | `contacts` | How many people are involved |

2. **Stage order** from first to last, plus the win probability the user gives each stage, if they have one.
3. **Scope:** every deal (`all`), the user's own (`my_deals`), or one team (`team:NAME`).
4. **Quota for the period**, only when they want a coverage figure.

## What to look for in each open deal

The limits below are defaults. A value written in CLAUDE.md replaces the default.

- **Gone quiet:** 14 days or more since the last logged activity. Note the exact count of days.
- **Close date at risk:** the date is already behind us, or it falls in the next 7 days while the deal has gone quiet.
- **Parked in a stage:** time in the current stage is more than double the usual time for that stage, worked out from the data or taken from CLAUDE.md.
- **One thread:** a single engaged contact. The bigger the deal, the more this matters.
- **No real plan:** `next_step` is blank or says nothing concrete ("follow up", "check in").
- **Light for its stage:** the amount sits far under what deals at that stage usually carry, so the effort may not pay back. Worth a question to the owner.

## Colour each deal

- **Red:** two or more of the flags above, or quiet for 21 days or more, or a close date already passed.
- **Yellow:** exactly one flag, or close to the limit for its stage.
- **Green:** none of that. Recent activity, a dated next step, more than one person involved.

## One next move for every Red or Yellow deal

Choose the move that answers the main flag, and fill in the person or the meeting:

| Main flag | Move to suggest |
|---|---|
| Gone quiet | Give [CONTACT_NAME] a reason to write back: a short note carrying something useful to them. |
| One thread | Ask the current contact to bring in a second person; propose a [TITLE]. |
| Close date at risk | Agree a written list of remaining steps with the buyer, ending on a new date. |
| No real plan | Put a [MEETING_TYPE] in the calendar for [DATE]. |
| Parked in a stage | Find out whether the champion is still active: when did you last speak properly? |

## The weekly picture

Work every figure out from the data. When one needs something the data lacks, print "not available" and the reason.

- Open pipeline: total value and number of deals, then per stage the count, value and average days in stage.
- Weighted value: amount times stage probability, only when probabilities were given. Say where they came from.
- Coverage: open value divided by quota, only when a quota was given.
- Speed: average days per stage, and average days from created to closed for the deals that closed.
- Movement this week: created, moved forward, won, lost. This needs stage history or last week's export; without either, say so.
- Risk: how many deals are Red, Yellow and Green, and the value sitting in Red and Yellow.

## The report

Save it as `./data/reports/pipeline_review_[YYYY-MM-DD].md`, sections in this order:

1. **Headline numbers:** open value and deal count, weighted value, coverage against the quota, value at risk.
2. **Red deals**, then **Yellow deals**, one entry each:
   ```
   - [DEAL_NAME] | [COMPANY] | $[AMOUNT] | [FLAGS] | Move: [NEXT_MOVE]
   ```
3. **By stage:** a table with stage, deals, value and average days.
4. **Closed this week:** won, and lost with the reason recorded in the CRM.
5. **Three moves for this week:** the three that protect the most value.
6. **CRM changes to consider (not made):** deal, field, proposed value.

## Applying the CRM changes

Only when the user asks to apply the listed changes through a connected CRM: show every change exactly as it will be written, wait for a yes, then write those and nothing else. If the `gtm-guard` plugin is installed, it asks once more before each write.

## Fictional example

```
/gtm-outbound:pipeline-reviewer crm my_deals
```

```
Pipeline review, 2026-03-15
Open: $940K across 16 deals | weighted $371K | coverage 2.8:1

Red
- Tavrocott Analytics | $85K | quiet 23 days, one thread
  Move: send the champion a short note with something useful, and ask to include the VP Engineering.
- Tailspin Robotics | $120K | close date of 10 March passed, no next step
  Move: agree a written list of remaining steps ending on a 28 March close.

Yellow
- Fabrikam Cloud | $45K | 18 days in Demo, usual time 10
  Move: offer a technical deep-dive to reach Proposal.
```
