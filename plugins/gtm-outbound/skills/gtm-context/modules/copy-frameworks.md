# How we write

The rules the writing skills and subagents follow (personalization-writer, the hook-writer and sequence-builder subagents, campaign-builder). Fill in your voice once; the skills apply it to every first line, email, note and reply draft.

## Our voice

| Question | Our answer |
|---|---|
| Who does the email come from? | [NAME, ROLE], writing as [themselves / the team] |
| Three words for how we sound | [e.g., direct, curious, plain] |
| Words and phrases we never use | [e.g., "synergy", "quick question", "hope this finds you well"] |
| How long a first email may be | [e.g., under 90 words] |
| How we ask for the next step | [e.g., a yes/no question, never a calendar link in the first email] |
| What we may claim | [only results we can name a source for; see the proof list below] |

## Proof we are allowed to use

Copy may only use proof that is on this list. If a draft needs proof that is not here, Claude leaves `[PROOF NEEDED]` instead of inventing a number or a customer.

| Proof | Exact wording we may use | Approved by | Can we name the customer? |
|---|---|---|---|
| [e.g., a customer result] | [THE LINE] | [PERSON] | [yes / no, describe as "a 200-person fintech"] |

## Shapes that work for us

Pick two or three. Each is a structure, not a script; the content comes from the prospect's signal and our proof.

- **Observation, implication, question.** Something true and public about them, what it usually leads to, and a low-effort question. Good for signal-led first touches.
- **Problem, agitate, solve (PAS).** Name the problem in their words, show what it costs them, offer one way out. Good when the pain is well known in the role.
- **Before, after, bridge.** Where they are, where they could be, what gets them there. Good for follow-ups with a short example.
- **Peer proof.** A short story about a similar company, using only approved proof.

## The touches

Describe what each touch is for; the sequence-builder subagent writes them.

| Touch | Day | Channel | Its job | Never |
|---|---|---|---|---|
| 1 | [0] | [email] | [open with the signal, one question] | [attachments, links in the first email] |
| 2 | [3] | [LinkedIn view or connection] | [be a familiar name] | [a pitch in the connection note] |
| 3 | [5] | [email] | [one useful idea or resource] | |
| 4 | [10] | [email] | [proof from a similar company] | |
| 5 | [17] | [email] | [a polite close that makes it easy to say no] | [guilt, fake urgency] |

Every email includes a plain way to opt out (see the deliverability notes in the campaign-builder skill).

## Answering replies

How we want replies handled; the reply-classifier skill drafts answers in this spirit and you send them.

| Reply | Our approach |
|---|---|
| Interested | [answer their question, offer two times, keep it short] |
| "Not now" | [ask when to come back, set a reminder, no nurture without their yes] |
| "We use [a competitor]" | [one honest point of difference, no criticism of the other tool] |
| "Send info" | [one page or one link, plus one question to see if it is worth a call] |
| "Stop" or unsubscribe | [confirm in one line, add to the suppression list, never contact again] |

## Fill-in fields the skills use

`[FIRST_NAME]`, `[COMPANY]`, `[ROLE]`, `[SIGNAL]` (with its source link), `[ANGLE]` (from signal-map.md), `[PROOF]` (from the proof list only).

## Fictional example (Pagelorn)

Voice: from the founder, direct and dry, under 80 words, ends with a yes/no question. Never "quick question" or "circle back".

> Priya, saw Sedgefarrow is hiring two more SREs. Teams adding a rotation often find the notes from the last incident only live in one person's head. Is that a problem you are seeing yet, or still manageable?
