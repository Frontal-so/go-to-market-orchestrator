# What we watch for

A signal is something that happened at an account that might make our message more relevant this month than last month. The signal-monitor skill and the signal-scraper subagent use this page to decide what to look for, where, and how much weight to give it.

Treat every row as a **hypothesis**. A signal earns its weight when campaigns built on it get more replies and meetings than campaigns without it. Until then, it is a guess worth testing.

## Our signals

| Signal | What exactly counts | Where Claude can check it | Our guess about why it matters | Weight (start) | Tested? |
|---|---|---|---|---|---|
| [e.g., Hiring for the team that uses us] | [e.g., an open role with "SRE" in the title, posted in the last 30 days] | [careers page, job boards] | [e.g., the team is growing faster than its process] | [high / medium / low] | [not yet / date and result] |
| [e.g., New leader in the buying team] | [e.g., VP or Head of the department started in the last 90 days] | [the person's public profile, company announcement] | [e.g., new leaders often review the tool stack early; test whether that holds for us] | | |
| [e.g., Funding announced] | [round size, date] | [the company's own announcement or press release] | [e.g., may open budget; test against reply rates] | | |
| [e.g., A tool change we can see] | [added or dropped a tool that sits next to ours] | [job posts naming the tool, public integration pages] | | | |
| [e.g., Public talk about the problem] | [a post, talk or article by someone at the account about the pain we solve] | [the post or article URL] | | | |
| [e.g., First-party interest] | [visited pricing, signed up, opened a trial] | [your own product or web analytics, only if you have it] | | | |

## Rules for every signal

- **Source and date, always.** Each signal Claude reports carries the link where it was seen and the date it happened. A signal without both is dropped, not guessed.
- **Freshness.** Say how old a signal may be before it stops counting: [e.g., 30 days for hiring, 90 days for a new leader].
- **One signal, one angle.** Note what the message should say when this signal fires ([ANGLE]), and what it must not say (never imply we watch them; refer to public facts the way a well-read peer would).
- **Stacking.** Decide whether two signals at once raise the priority: [RULE].

## Keeping it honest

After each campaign, fill the "Tested?" column from campaign-history.md: which signal the campaign used, how many were contacted, how many replied and booked. Lower or drop signals that do not beat your baseline; raise the ones that do. Small samples prove little, so note the count next to the result.

## Fictional example (Pagelorn, a made-up incident-review tool)

| Signal | What counts | Where | Guess | Weight | Tested? |
|---|---|---|---|---|---|
| SRE or platform hiring | open role, last 30 days | careers page | on-call load is rising | high | Q1: 60 contacted, 7 replies, 3 meetings |
| New VP Engineering | started in last 90 days | company post, public profile | may revisit incident process | medium | not yet |
| Public postmortem | blog post about an outage, last 60 days | engineering blog | they already value learning from incidents | medium | Q1: 25 contacted, 4 replies, 1 meeting |
