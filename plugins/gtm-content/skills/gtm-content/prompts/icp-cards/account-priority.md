# Target account brief

One page on one named company: why it deserves attention this month, what we think its problem is, and how to open the conversation. Used before account planning, before a sequence goes out, or to prepare a rep for a first call. Under 400 words.

## Prompt

```
Brief: build a one-page brief on a single target account. Work only from the material below and from facts you looked up on the user's request, each with its URL and the date read. Anything unknown becomes [RESEARCH NEEDED: what to find out]. Keep what is known clearly apart from what is assumed.

- Company: [name and website]
- Sector, size and stage: [industry; headcount or revenue with its source; funding stage or public]
- Recent events that make now the moment: [each event with date and source: a raise, a leadership hire, a hiring burst, an expansion, a product launch]
- Who we would talk to: [name, title and profile link if known, or "to be identified"]
- What we can see about how they work: [tools, initiatives, complaints in reviews or job posts, each with where it came from]
- Our guess at their problem: [the pain we believe they have and why]
- What they likely use instead of us: [named tools or vendors, or "unknown"]
- Why we would win here: [the difference that matters for this account]
- What a good first conversation leads to: [intro call / demo / pilot / referral]
- Proof we are allowed to share: [case studies, customer names cleared for use, comparable results]

Lay out the brief as:
1. At a glance: name, sector, size, stage, website.
2. Why this month: the dated triggers, each with its source. Example: "Hired a VP of Revenue Operations, announced on the company blog on 4 November (northpeak.example/blog)".
3. Working theory: two or three sentences, cause then effect, labelled as a theory.
4. People: known contacts with titles, or the profile of the person to find.
5. What they have today: likely current solution and its gaps.
6. Our way in: one message, one proof point, one reason we are different.
7. Opening move: channel, format and the first message type.
8. Questions for the first call: three to five.

Specific to this one account throughout. If a sentence would be true of any company, cut it.
```

## Rules for this draft

- Research happens only when the user asks for it. Cite each fact found with its URL and the date read. An event older than about three months goes under background, not under "why this month".
- Do not guess an email address, phone number or reporting line. Leave contact details to the user's own data tools.
- Proof points must be cleared for external use. When unsure: `[ASK: are we allowed to cite this customer?]`.

## Check before handing back

- Does every trigger carry a date and a source?
- Is the working theory labelled as a theory rather than stated as fact?
- Is the opening move concrete enough that a rep could do it today?

## Hand back

The file path, the working theory in one line, and the open research items. Nothing is sent to the account from this skill. If the user wants outreach next, the gtm-outbound plugin's personalization or campaign skills can take the brief as input, and gtm-guard asks before any CRM write or send.
