# Best-fit customer definition

One page that sales, marketing and product can all point to when they ask "is this account a fit?". It names the segment, the reasons it buys, the people involved, and the signals for chasing or dropping an account. Under 400 words.

## Prompt

```
Brief: write a one-page definition of our best-fit customer. Use only the material below; a gap becomes [ASK: what is missing].

- Us: [company or product name, and what the product does in one sentence]
- Our best customers so far: [two or three examples by type and size, and what makes them good: they stay, they expand, they get value fast]
- Customers who were a poor fit: [who struggled or left, and why, if known]
- Hard filters:
  - sectors: [list]
  - size: [headcount or revenue band]
  - regions: [list, or "global"]
  - business model: [for example B2B subscription, marketplace, services]
- Tools they tend to run: [CRM, data stack, other telling tools, or "not yet known"]
- Events that tend to come before a purchase: [for example a funding round, a new sales leader, a hiring burst]
- The person who feels the pain: [title and team]
- The person who signs: [title and team]
- The problem, in their language: [the business problem as a customer would describe it]
- Fit versus ready: [what separates an account that could buy from one that will buy soon]

Lay out the page:
- A short name for the segment. Example: "Scaling B2B software, first RevOps hire".
- Profile: the hard filters and tools as a compact list a list-builder could use.
- Why they buy: problem, trigger, desired outcome.
- Buying group: who feels it, who signs, who could block it.
- Chase signals: three to five checkable reasons to prioritise an account now.
- Drop signals: three to five checkable reasons to walk away early.
- First line: one sentence that would make this buyer stop scrolling, in their words.

Every signal must be something a person or a filter can verify: a number, a range, a named tool, a dated event. No feelings.
```

## Rules for this draft

- The profile is built from the best and worst customers supplied. If none were supplied, the first line says it is a hypothesis, and the page ends with the data that would test it (for example win rate, sales cycle length and retention by segment from the CRM).
- Do not borrow industry averages or market statistics unless the user supplied them with a source.

## Check before handing back

- Could a rep decide in under a minute whether a new account qualifies?
- Are the drop signals as concrete as the chase signals?
- Does the first line use the customer's words rather than our product's?

## Hand back

The file path, the segment name, and the gaps. If the user runs the gtm-outbound plugin, its `gtm-context` skill can fold this definition into the project's GTM context so the outbound skills apply it.
