---
name: vault
description: Read from and write to Jules's Obsidian research vault (Second_Brain). Use whenever a paper, study, or citation comes up in the work — the user shares one, I fetch or search for one, or one gets cited in a plan — and whenever a new concept, method, or dataset worth remembering appears. Also use when asked what the vault already contains, to check whether something is already noted, or to link/refresh existing notes.
---

# Obsidian vault protocol

Vault: `C:\Users\jules\OneDrive - The University of Manchester\Second_Brain`

```
00_Map_of_Content/Knowledge_Graph_Index.md   the hub — themes + recent sources
01_Inbox/                                     unprocessed (Failed/, TEMP_PROCESSING/)
02_Source_Notes/    Lit_*.md                  one note per paper
03_Atomic_Concepts/ <Concept Name>.md         one note per idea
04_Entities/                                  people/orgs (currently empty)
```

~190 notes. Plain Markdown, `#` H1 title, `##` sections, `[[wikilinks]]`. No YAML frontmatter —
do not add any; it would break the existing convention.

## Always dedupe before creating

The vault is large enough that duplicates are a real risk, and a duplicated paper note silently
splits the link graph. Before writing anything new:

1. `Glob` `02_Source_Notes/Lit_*` (or `03_Atomic_Concepts/*`) to see what exists.
2. `Grep` the vault for the title, first author surname, and DOI separately — existing notes are
   named inconsistently (`Lit_Booth_2013_...` and `Lit_Bayesian_Calibration_UBEM` may be the same
   work), so a filename miss does not mean absent.
3. If a note exists, **update it in place** rather than adding a second one.

Near-duplicate *concept* notes are equally damaging. Check `03_Atomic_Concepts/` for an existing
note covering the idea under a different name before minting a new one.

## Verify citations before they enter the vault

If a paper arrives with a DOI/PMID/arXiv ID — especially one surfaced by a model rather than
read directly — verify it with Scholar Sidekick's `verifyCitation` before creating a note. The
dominant fabrication pattern is a *real, resolving* identifier paired with an *invented* title,
so "the DOI loads" proves nothing. A vault polluted with fabricated references is worse than no
vault, because it launders them into future drafts.

If verification fails or is unavailable, say so in the note rather than presenting it as checked.

## New paper → `02_Source_Notes/Lit_<Author>_<Year>_<Short_Title>.md`

Match the existing depth. These notes are substantial working documents, not stubs — see
`Lit_Neto-Bradley_2021_*` as the reference standard. Structure:

```markdown
# <Full paper title>

## Executive Summary
Two paragraphs. What the paper does and why it matters.

## Core Argument & Objectives
The claim, then numbered objectives.

## Methodology & Data Sources
Algorithms, equations (LaTeX inline is used freely), datasets. Wikilink every named
method and dataset: [[Iterative Proportional Fitting]], [[Census of India 2011]].

## Key Findings & Results
Specific numbers, not summaries of summaries.

## Limitations & Future Work
Split into ### Limitations and ### Future Work.

[[Concept One]]
[[Concept Two]]
```

Trailing bare wikilinks at the end are the convention — concept tags, not under a heading.

**Link liberally, including to notes that do not exist yet.** Ghost links are intentional here:
they mark ideas worth writing up later and show as unresolved in the graph view. Do not create a
concept note for every link — only for ideas that carry real weight in the work.

**When the paper bears on current research**, add a short `## Relevance` section naming which
paper/plan it touches and how. That is the part that pays off later.

## New concept → `03_Atomic_Concepts/<Name>.md`

Shorter. Follow `Performance Gap.md`:

```markdown
# <Concept>

## Definition
One tight paragraph.

## <Substantive section(s)>
Causes / Why it matters / The trap — whatever the idea needs.

## Linked Sources
- [[Lit_...]]
- [[Related Concept]]
```

Title-case filename with spaces, matching `Thermal Headroom.md`, `Comfort Take-back.md`.

## Update the index

`00_Map_of_Content/Knowledge_Graph_Index.md` has `## Key Themes`, topic groupings, and
`## Recent Sources`. Add genuinely significant papers to Recent Sources with a parenthetical
gloss; add concepts to the appropriate theme grouping, creating a new grouping only for a real
new line of work (as `## Causal Identification (Paper 2 line)` was added for Paper 2).

Do not add every note to the index — it is a map, not a table of contents. Routine notes are
reachable via links and search.

## What not to do

- No YAML frontmatter, no tags-as-metadata — this vault uses links, not tags.
- Do not restructure existing notes or rename files; inbound `[[links]]` break silently.
- Do not summarise a paper you have not actually read into a note that implies you did. If
  working from an abstract, say so in the note.
- Do not write research *conclusions* into `02_Source_Notes/` — those belong in the project's
  `docs/`. The vault holds what the literature says and what concepts mean; the repo holds what
  we are doing about it.
