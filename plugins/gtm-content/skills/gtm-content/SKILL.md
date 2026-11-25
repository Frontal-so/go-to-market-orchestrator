---
name: gtm-content
description: Drafts go-to-market collateral from 17 prompts. Customer case studies, internal win write-ups, buyer persona cards, account priority cards, ICP one-pagers, product one-pagers, offer and pricing one-pagers, case study one-pagers, LinkedIn carousels (thought leadership, how-to, case study), investor decks, sales decks, internal strategy decks, sales proposals, scopes of work and pricing pages. Use when the user asks to write, draft, outline or rework any of these, for example "turn this win into a case study", "make a one-pager for our product", "build a 5-slide sales deck", "write a proposal for this prospect", "persona card for heads of RevOps", "carousel from this post", "scope of work for this client". Drafts only. It saves a file in the project and never publishes, posts or sends anything.
argument-hint: "[asset type] [topic, or a file with your notes]"
---

# GTM content

One skill over a library of 17 prompts. Each prompt file has a brief (the block under
**Prompt**) with the inputs it needs and the structure the draft must follow. Load only
the one file the request needs.

## The library

| Asset | Use it for | Prompt file |
|---|---|---|
| Customer case study (long) | Website, proposals, late-stage buyers who want the full story (600 to 900 words) | [prompts/case-studies/customer-case-study.md](prompts/case-studies/customer-case-study.md) |
| Internal win write-up | Sharing a closed deal, save or launch inside the team, with what to repeat | [prompts/case-studies/internal-win.md](prompts/case-studies/internal-win.md) |
| Buyer persona card | Enablement: who the buyer is, what they care about, what loses them | [prompts/icp-cards/buyer-persona.md](prompts/icp-cards/buyer-persona.md) |
| Account priority card | One target account: why it, why now, the angle, the first move | [prompts/icp-cards/account-priority.md](prompts/icp-cards/account-priority.md) |
| ICP one-pager | One shared definition of the best-fit customer, with qualify and disqualify signals | [prompts/one-pagers/icp-one-pager.md](prompts/one-pagers/icp-one-pager.md) |
| Product one-pager | Leave-behind that explains the product in two minutes | [prompts/one-pagers/product-one-pager.md](prompts/one-pagers/product-one-pager.md) |
| Offer and pricing one-pager | What is included, what it costs, what happens after signing | [prompts/one-pagers/offer-summary.md](prompts/one-pagers/offer-summary.md) |
| Case study one-pager | A short proof point for a sales call or proposal (under 300 words) | [prompts/one-pagers/case-study-one-pager.md](prompts/one-pagers/case-study-one-pager.md) |
| Thought leadership carousel | A point of view on LinkedIn, 10 slides | [prompts/linkedin-carousels/thought-leadership.md](prompts/linkedin-carousels/thought-leadership.md) |
| How-to carousel | Teaching one process step by step, 8 to 12 slides | [prompts/linkedin-carousels/how-to.md](prompts/linkedin-carousels/how-to.md) |
| Case study carousel | A customer result told for the feed, 9 slides | [prompts/linkedin-carousels/case-study-carousel.md](prompts/linkedin-carousels/case-study-carousel.md) |
| Investor deck | Fundraising, 10 slides with speaker notes | [prompts/pitch-decks/investor-deck.md](prompts/pitch-decks/investor-deck.md) |
| Sales deck | Discovery or demo call, 5 slides with presenter notes | [prompts/pitch-decks/sales-deck.md](prompts/pitch-decks/sales-deck.md) |
| Internal strategy deck | A plan or initiative for leadership, the team or the board | [prompts/pitch-decks/strategy-deck.md](prompts/pitch-decks/strategy-deck.md) |
| Sales proposal | After discovery: their problem, your solution, scope, price, next steps | [prompts/proposals/sales-proposal.md](prompts/proposals/sales-proposal.md) |
| Scope of work | What is in, what is out, who does what, how work is accepted | [prompts/proposals/scope-of-work.md](prompts/proposals/scope-of-work.md) |
| Pricing page | Website pricing page copy: plans, FAQ, proof, final call to action | [prompts/proposals/pricing-page.md](prompts/proposals/pricing-page.md) |

When two could fit, pick by length and reader:
- A customer result: long case study (buyer doing research), case study one-pager (sales
  call), case study carousel (LinkedIn feed), internal win (your own team).
- Who to sell to: ICP one-pager (the whole segment), buyer persona card (one role),
  account priority card (one named company).

If the request still fits two rows, ask once which one, with the difference in one line.

## How to run it

1. **Pick the prompt.** Match the request (and `$ARGUMENTS`, if given) to a row above.
   If the user pointed at a file of notes, a call transcript or a past document, read it.
2. **Load only that prompt file**, from `${CLAUDE_SKILL_DIR}/prompts/`. Its **Prompt**
   block is the brief you follow. The bracketed fields are the inputs. Its **Rules for
   this draft** section, where there is one, adds to the rules below.
3. **Read the project's GTM context first**, if there is one: `CLAUDE.md` and any files
   under `gtm/` (the gtm-outbound plugin's `gtm-context` skill writes them). Pre-fill every
   input you can from there and from what the user already said: ICP, personas, proof
   points, tone, words to avoid, exclusions.
4. **Ask for what is still missing, once.** One message, listing only the inputs that the
   draft cannot be written without. Skip optional inputs. If the user says "just draft
   it", draft it with the gaps marked.
5. **Draft**, following the prompt's structure and length.
6. **Save the draft as a file** in the project: `content/<asset>/<YYYY-MM-DD>-<short-name>.md`
   (for example `content/case-studies/2026-11-25-logistics-onboarding.md`), unless the
   user named another place. Never overwrite an existing file: add `-v2`, `-v3`.
7. **Reply with** the file path, two or three lines on what the draft argues, and the
   list of open gaps (`[ASK: ...]` and the other markers). When the user sends the missing facts, fill them in
   the same file.

## Rules for every draft

- **Facts come from the user, not from you.** Use only facts the user gave, the project's
  context files hold, or a source you fetched and cite. Never invent metrics, results,
  customer names, logos, quotes, market sizes, prices, guarantees or dates. Mark every
  gap in the draft as `[ASK: what is needed]`, for example `[ASK: churn rate before and
  after]`. Some prompts also use `[RESEARCH NEEDED: ...]` (something to look up) and
  `[DATA NEEDED: ...]` (a number to gather); treat them the same way. A draft with honest
  gaps is worth more than a finished-looking one with made-up numbers.
- **Research only when asked.** If the user asks you to look something up (a target
  account, a market figure, a competitor's pricing page), use web search and put the
  source URL and the date you read it next to each fact. Mark a guess as a guess.
- **Quotes are real or absent.** Use a customer quote only if the user supplied it and
  says the customer approved it. Otherwise write `[ASK: approved quote from <role>]`.
  Never write a "representative" quote.
- **Customer names need permission.** If the user has not confirmed the customer may be
  named, use a label such as "a 200-person logistics company" and keep the real name out
  of the file.
- **Plain, specific language.** No hype words ("revolutionary", "game-changing",
  "robust", "best-in-class", "seamless"). Claims a buyer could check, in words the buyer
  uses.
- **Drafts only.** Do not publish, post, send, upload or schedule anything, and do not
  write to a CRM, Notion, a doc tool or a social scheduler as part of this skill. The
  user reviews the file and puts it where it goes. If they then ask you to move it into
  a connected tool, treat that as a separate request they confirm.

## Visuals

Carousels and decks come out as slide-by-slide copy with a one-line visual direction per
slide. Design them in your own tool (Figma, Canva, Google Slides, Keynote, PowerPoint).
For a LinkedIn carousel, export the slides as a PDF and upload it yourself as a document
post.
