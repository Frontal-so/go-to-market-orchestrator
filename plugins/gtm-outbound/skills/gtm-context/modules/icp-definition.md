# Who we sell to

Fill this in once. Every gtm-outbound skill reads it before it scores, researches or writes, so a vague answer here turns into vague lists and vague emails everywhere else.

Write it the way you would brief a new SDR on their first day: concrete, with the reasons.

## 1. The account

**One sentence:** We sell to [KIND OF COMPANY] that [SITUATION THEY ARE IN], because [WHY THAT SITUATION MAKES OUR PRODUCT MATTER].

| Filter | Our answer | Hard rule or preference? |
|---|---|---|
| Headcount | [RANGE] | [hard / preference] |
| Industry or vertical | [LIST] | |
| Business model | [B2B SaaS, marketplace, services...] | |
| Funding or revenue stage | [STAGE] | |
| Regions we can serve | [COUNTRIES OR TIME ZONES] | |
| Tools they must already use | [e.g., a CRM we integrate with] | |
| Team that must exist | [e.g., at least three people in sales] | |

A **hard rule** removes an account from every list. A **preference** only moves it up or down the score.

## 2. The people

List the people who feel the problem, the people who sign, and anyone who can block the deal.

| Role in the deal | Titles we search for | Why they care | Contact them? |
|---|---|---|---|
| Feels the pain | [TITLES] | [WHAT IS HARD FOR THEM TODAY] | [first / later / never] |
| Signs the budget | [TITLES] | [WHAT THEY ARE MEASURED ON] | |
| Can block | [TITLES, e.g., security, procurement] | [THEIR CONCERN] | |

Titles drift. Add the variants you see in real exports ("Revenue Operations Lead", "RevOps Manager", "Head of Sales Ops") so searches do not miss them.

## 3. Reasons to walk away

Accounts that match on paper but never buy. Be specific; each line should come from a deal you lost or a call that went nowhere.

- [e.g., They build the same thing in house and have a team for it]
- [e.g., Fewer than N people would use the product]
- [e.g., Regulated in a way we cannot support yet]

## 4. How a skill should score an account

Keep the score simple enough that a person can check it by hand. Each line is something Claude can read from a source and cite.

| Evidence | Points | Where it comes from |
|---|---|---|
| Meets every hard rule | required, otherwise the account is out | the filters above |
| [STRONGEST FIT SIGNAL] | [POINTS] | [SOURCE] |
| [SECOND SIGNAL] | [POINTS] | [SOURCE] |
| [A RECENT EVENT, see signal-map.md] | [POINTS] | [SOURCE] |
| A walk-away reason | minus [POINTS] | section 3 |

Tiers: [e.g., Tier 1 at X points or more, Tier 2 from Y, the rest wait].

Review the weights after every campaign against who actually replied and booked (see campaign-history.md). The first version is a guess.

## Fictional example (Pagelorn, a made-up incident-review tool)

> We sell to software companies with 80 to 600 people whose engineering teams are on call, because once a team passes about six rotations, nobody can remember what was learned in the last incident.

- Hard rules: B2B software, 80 to 600 people, North America or Europe, uses PagerDuty or Opsgenie.
- Feels the pain: Engineering Manager, Staff Engineer, SRE Lead. Signs: VP Engineering, CTO. Can block: Security Lead.
- Walk away: fewer than three on-call rotations; an internal postmortem tool with a named owner.
- Score: 3 points for an open SRE role, 2 for a public postmortem in the last 90 days, 2 for a new VP Engineering, minus 4 for an internal tool. Tier 1 at 5 or more.
