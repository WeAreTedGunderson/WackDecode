# WackDecode

Public-source firewalking through the John McAfee dead-man-switch rumor machine, the WHACKD token, and the wreckage field of screenshots, countdowns, copycats, and bad magic.

This repository does **not** claim that a McAfee-controlled dead man switch has been proven. It does something more useful: it drags every claim under fluorescent light, checks the timestamps, separates real artifacts from theatrical smoke, and leaves a reproducible trail for anyone brave enough to keep digging.

No private data. No breached material. No vigilante cosplay. Public sources, public chains, public archives, sober confidence ratings.

## The Short Version

McAfee made dead-man-switch-like public claims. WHACKD is a real Ethereum token. Post-death artifacts and rumors circulated. Those facts are not the same thing as proof of a functioning dead man switch.

The current assessment:

| Question | Current answer |
|---|---|
| Did McAfee make public DMS-style claims? | Yes, reported by multiple public sources. |
| Is WHACKD a real on-chain artifact? | Yes. The official contract is `0xCF8335727B776d190f9D15a54E6B9B9348439eEE`. |
| Did post-death DMS rumors circulate? | Yes. The Instagram "Q" post, Telegram/QAnon claims, and `britbonglogpost.com` countdown all belong to that ecosystem. |
| Has a McAfee-controlled operational DMS been proven? | No. Not from the evidence currently preserved here. |
| Is there still useful technical work to do? | Yes. Start with provenance, then reconstruct the official WHACKD contract behavior. |

## What Is In This Repo

| Path | Purpose |
|---|---|
| [`mcafee-dms-report-and-decoding-plan.md`](mcafee-dms-report-and-decoding-plan.md) | Main report: evidence summary, confidence matrix, timeline, WHACKD mechanics, and technical decoding plan. |
| [`mcafee-dms-report-and-decoding-plan.html`](mcafee-dms-report-and-decoding-plan.html) | Browser-readable version of the main report. |
| [`mcafee-dms-provenance/provenance-map-report.html`](mcafee-dms-provenance/provenance-map-report.html) | Provenance map report for the accepted and rejected leads. |
| [`mcafee-dms-provenance/confidence_ranked_timeline.md`](mcafee-dms-provenance/confidence_ranked_timeline.md) | Event timeline with confidence levels and source IDs. |
| [`mcafee-dms-provenance/decode_candidates.md`](mcafee-dms-provenance/decode_candidates.md) | Shortlist of public artifacts worth technical analysis. |
| [`mcafee-dms-provenance/sources.csv`](mcafee-dms-provenance/sources.csv) | Source ledger with URLs, source IDs, and provenance metadata. |
| [`mcafee-dms-provenance/evidence_graph.graphml`](mcafee-dms-provenance/evidence_graph.graphml) | GraphML evidence graph for external graph tools. |
| [`mcafee-dms-provenance/option2_whackd_reconstruction_notes.md`](mcafee-dms-provenance/option2_whackd_reconstruction_notes.md) | Current WHACKD Option 2 reconstruction notes, run commands, source alignment, and full-burn findings. |
| [`mcafee-dms-provenance/whackd_reconstruction.py`](mcafee-dms-provenance/whackd_reconstruction.py) | Reproducible script for exporting Transfer logs, grouping transactions, and reconstructing the direct-transfer counter model. |
| [`mcafee-dms-provenance/option2-data/`](mcafee-dms-provenance/option2-data/) | Initial smoke-run output tables for blocks `8943162` through `8944000`. |
| [`mcafee-dms-provenance/option2-data-8945000/`](mcafee-dms-provenance/option2-data-8945000/) | Larger sweep output tables for blocks `8943162` through `8945000`, including the first exact full-burn candidate. |
| [`.agents/skills/osint/`](.agents/skills/osint/) | Local OSINT skill pack used to structure public-source investigation work. |

## The Operating Principle

Every claim gets handled like a live wire:

1. Find the original public source or the earliest stable archive.
2. Record the source ID, date, artifact type, and confidence.
3. Separate primary evidence from reporting, reposts, screenshots, and inference.
4. Reject leads that depend on private data, leaked data, unverifiable screenshots, or copycat contracts.
5. Promote only public, sourceable artifacts into technical decoding.

If the chain of custody collapses, the lead goes in the trash. Not because it is boring, but because bad evidence is how nonsense puts on a lab coat.

## Accepted Decode Candidates

These are not proven payloads. They are the current public artifacts that are real enough to analyze without wasting your life in the swamp.

### AC-001: Official WHACKD Contract

- Contract: `0xCF8335727B776d190f9D15a54E6B9B9348439eEE`
- Creation transaction: `0x1bb323576cd7dcb12e9f8507a5e298a0136927a486f959e3984cb7cca21ed96b`
- Contract name reported by Etherscan: `Epstein`
- Status: high confidence for artifact identity, low confidence for any DMS payload interpretation.

Current technical progress:

- Option 2 reconstruction has started in [`whackd_reconstruction.py`](mcafee-dms-provenance/whackd_reconstruction.py), with notes in [`option2_whackd_reconstruction_notes.md`](mcafee-dms-provenance/option2_whackd_reconstruction_notes.md).
- A smoke run over blocks `8943162` through `8944000` produced `631` Transfer logs and `316` grouped transactions in [`option2-data/`](mcafee-dms-provenance/option2-data/).
- A larger sweep over blocks `8943162` through `8945000` produced `2,989` Transfer logs, `1,495` grouped transactions, `1,491` direct WHACKD contract transactions, `3` external-contract transactions, and `1` exact full-burn candidate in [`option2-data-8945000/`](mcafee-dms-provenance/option2-data-8945000/).
- The first exact full-burn candidate is transaction `0x8be7bd5924e3393c730a8edd8dae23915896d9e1ff33cae1c3cd696bc2bd3abd` at block `8944493`, timestamp `2019-11-16 12:56:33 UTC`, direct transfer ordinal `1000`, with `random_before=999` and `random_after=0`.

Next useful work: add trace support for external-contract rows, continue larger range reconstruction after the trace boundary is handled, keep `transferFrom` separate from direct `transfer`, and test bounded candidate strings only from reproducible full-burn rows.

### AC-002: `britbonglogpost.com`

- Publicly circulated after McAfee's death with a countdown and WHACKD linkage.
- RDAP registration timestamp preserved in the report.
- Wayback capture preserved as a public web artifact.
- Status: high confidence that the site existed, low confidence that McAfee controlled it.

Next useful work: preserve page hashes, capture metadata, extract embedded resources, compare archive timestamps, and avoid pretending attribution has been solved.

### AC-003: McAfee DMS / WHACKD Claim Corpus

- Public reports support that McAfee made DMS-like and WHACKD-linked statements.
- Status: medium confidence for the public claim chain, low confidence for the alleged cache or release mechanism.

Next useful work: locate original post archives, preserve timestamps, and treat wording-based key theories as invalid unless they produce reproducible, non-arbitrary output.

## Rejected Or Weak Leads

| Lead | Status | Why |
|---|---|---|
| Surfside / Champlain Towers "31TB" tweet | Rejected | Identified as fabricated by fact-checking. |
| Instagram "Q" post as a DMS key | Weak | Reported as an event, but not authenticated as a trigger or key. |
| `britbonglogpost.com` as proven McAfee infrastructure | Weak | Site existence is real; McAfee control is unproven. |
| Later WHACKD-named contracts | Rejected pending provenance | Copycat risk is high. |
| Telegram-only or screenshot-only clues | Rejected | No stable public source chain. |
| Generic Swarm/IPFS/Arweave theories | Not candidates yet | Valid storage systems, but no proven pointer has been accepted. |

## How To Read The Reports

Start here:

```text
mcafee-dms-report-and-decoding-plan.md
```

Then check the provenance layer:

```text
mcafee-dms-provenance/decode_candidates.md
mcafee-dms-provenance/confidence_ranked_timeline.md
mcafee-dms-provenance/sources.csv
```

Then check the current Option 2 reconstruction layer:

```text
mcafee-dms-provenance/option2_whackd_reconstruction_notes.md
mcafee-dms-provenance/whackd_reconstruction.py
mcafee-dms-provenance/option2-data/
mcafee-dms-provenance/option2-data-8945000/
```

If you use graph tooling, open:

```text
mcafee-dms-provenance/evidence_graph.graphml
```

The HTML reports are included so the investigation can be read without a Markdown renderer.

## Methodology

This project uses a provenance-first OSINT method:

- Public sources only.
- Source IDs for traceability.
- Confidence ratings per claim, not per vibe.
- Explicit separation between verified facts, public claims, inference, and speculation.
- Known false leads preserved so they do not keep resurrecting themselves in new clothes.
- Technical analysis only after the artifact passes basic provenance checks.

The point is not to be cynical. The point is to be unfooled.

## Legal And Ethical Boundary

This repo is for lawful public-source research and technical analysis of public artifacts.

Do not use it to:

- identify private people behind wallets without a strong public-interest basis;
- buy, request, or distribute leaked data;
- access private systems;
- harass people;
- launder rumor into accusation;
- pretend a coincidence is a cryptographic proof.

The conspiracy-industrial complex wants your attention. Evidence wants your discipline.

## Current Technical Progress

The defensible next phase, WHACKD blockchain reconstruction, is now underway. The current reproducible artifacts are:

- [`option2_whackd_reconstruction_notes.md`](mcafee-dms-provenance/option2_whackd_reconstruction_notes.md): run notes, source alignment, classification rules, and current findings.
- [`whackd_reconstruction.py`](mcafee-dms-provenance/whackd_reconstruction.py): script for fetching Transfer logs, grouping transactions, classifying burn behavior, and modeling the direct-transfer counter.
- [`option2-data/`](mcafee-dms-provenance/option2-data/): smoke-run tables for blocks `8943162` through `8944000`.
- [`option2-data-8945000/`](mcafee-dms-provenance/option2-data-8945000/): larger sweep tables for blocks `8943162` through `8945000`.

The larger sweep found one exact full-burn candidate before counter certainty becomes incomplete:

| Field | Value |
|---|---|
| Transaction | `0x8be7bd5924e3393c730a8edd8dae23915896d9e1ff33cae1c3cd696bc2bd3abd` |
| Block | `8944493` |
| Timestamp | `2019-11-16 12:56:33 UTC` |
| Direct transfer ordinal | `1000` |
| Counter state | `random_before=999`, `random_after=0` |
| Burn raw value | `11972156190000000000000` |
| Non-burn raw value | `0` |

Source alignment currently supports this rule boundary: direct `transfer(address,uint256)` calls mutate the `random` counter, while `transferFrom(address,address,uint256)` branches on `random` but does not increment or reset it. External-contract calls that emit WHACKD logs need trace-level decoding before later counter state can be treated as exact.

## Next Technical Work

The next phase should tighten the counter reconstruction before any payload tests:

1. Add trace support for external-contract rows if `trace_transaction` or `debug_traceTransaction` is available.
2. Run progressively larger block ranges after the trace boundary is handled.
3. Keep direct `transfer` and `transferFrom` activity in separate tables.
4. Compare the grouped Transfer-log behavior against the verified or mirrored contract source.
5. Use `full_burn_candidates.csv` as the only starting point for bounded candidate-string tests.

A decoding theory is only worth keeping if someone else can reproduce it from the same public inputs and get the same output without knowing the desired answer first.

## Current Bottom Line

WHACKD is real. The claims are real. The rumor machine is real.

The dead man switch is not proven.

That is not a surrender. That is the line in the sand. Cross it with evidence or do not cross it at all.
