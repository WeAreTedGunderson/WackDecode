# McAfee DMS Option 1 Decode Candidates

Prepared: 2026-05-24

This file lists only public artifacts with enough provenance to justify later technical analysis. An accepted candidate is not proof of a McAfee-controlled DMS. It means the artifact is real enough, public enough, and sourceable enough to analyze without wasting time on fake screenshots or copycat claims.

## Acceptance Rule Used

A candidate is accepted only if it has a public URL or archive and either:

- one primary source, or
- two independent secondary sources.

Candidates are rejected when they depend on private/leaked data, screenshot-only provenance, unauthenticated repost chains, copycat contracts without provenance, or private-person attribution.

## Accepted Candidates

### AC-001 - Official WHACKD Contract And Creation Transaction

**Artifact:** Ethereum contract `0xCF8335727B776d190f9D15a54E6B9B9348439eEE`, contract name reported by Etherscan as `Epstein`, with creation transaction `0x1bb323576cd7dcb12e9f8507a5e298a0136927a486f959e3984cb7cca21ed96b`.

**Why it is connected:** WHACKD was publicly promoted as a McAfee-associated token, and the current official WHACKD site, CoinMarketCap, and Etherscan converge on the same contract address. It is the strongest reproducible technical artifact because it is public and on-chain.

**Supporting sources:** `SRC-008`, `SRC-009`, `SRC-010`, `SRC-011`, `SRC-018`, `SRC-019`.

**Current verification:** Direct Ethereum JSON-RPC lookup on 2026-05-24 returned transaction status `0x1`, `to: null`, contract address `0xcf8335727b776d190f9d15a54e6b9b9348439eee`, block `8943162`, timestamp `2019-11-16 07:25:23 UTC`, and block hash `0x8a62444d0d9f0f66d8bdbcf9e9faeeab23863463554551d68e4020b6043da5cc`.

**Provenance rating:** High for contract identity and creation transaction. Low for any DMS payload interpretation.

**What remains unverified:** No public source proves that the contract encodes a DMS payload, release key, or McAfee-controlled post-death trigger.

**Next technical analysis:** Reconstruct official contract calls and burn/full-burn events in Option 2. Treat any claimed "1000th transaction" key derivation as invalid until it specifies whether it counts direct `transfer`, `transferFrom`, ERC-20 logs, Uniswap activity, or the internal counter state.

### AC-002 - britbonglogpost.com Wayback Capture And RDAP Record

**Artifact:** `britbonglogpost.com` public archive capture from 2021-06-24 and RDAP registration record showing registration on 2021-06-24T07:32:18Z.

**Why it is connected:** The site publicly circulated after McAfee's death with a countdown and WHACKD linkage. Bitcoin.com reported the circulation, Verisign RDAP verifies registration timing, and the Wayback capture verifies public web content existed.

**Supporting sources:** `SRC-014`, `SRC-015`, `SRC-016`.

**Provenance rating:** High for site existence and capture timing. Low for McAfee control or DMS authenticity.

**What remains unverified:** No public authentication ties the domain operator to McAfee. The domain registration after death reporting weakens any claim that the domain itself proves a pre-arranged McAfee DMS.

**Next technical analysis:** Preserve the Wayback response metadata and page content hashes, extract any outbound links or embedded resources, compare captures across timestamps, and keep this as a web-provenance artifact rather than a proven DMS payload.

### AC-003 - McAfee Public DMS / WHACKD Claim Corpus

**Artifact:** Media-reported McAfee statements about a data release on arrest/disappearance, plus WHACKD-linked "if I suicide myself" reporting.

**Why it is connected:** The public DMS theory depends on McAfee having made DMS-like claims before death. Newsweek, Firstpost, PolitiFact, and WHACKD launch reporting provide a public claim corpus.

**Supporting sources:** `SRC-004`, `SRC-017`, `SRC-018`, `SRC-019`, `SRC-023`.

**Provenance rating:** Medium for claim-chain reconstruction. Low for the alleged cache or any release mechanism.

**What remains unverified:** Direct original tweet archives are not included as accepted primary evidence in this pass, and no source verifies the alleged 31+ terabyte cache.

**Next technical analysis:** Use the claim corpus only as a timeline and hypothesis source. Do not derive keys from claim wording unless the original post, timestamp, and archive can be independently preserved.

## Rejected Or Weak Leads

| Lead | Status | Source IDs | Reason |
|---|---|---|---|
| Surfside / Champlain Towers 31TB tweet | Rejected | `SRC-017` | PolitiFact identifies the image as fake. It must not be used as a payload-location clue. |
| Instagram "Q" metadata as hidden key | Weak / rejected for decoding | `SRC-004`, `SRC-005` | The post was reported, but the DMS-key interpretation is unauthenticated and counterclaims describe the supposed code as ordinary platform metadata. |
| britbonglogpost.com as McAfee-controlled DMS | Weak attribution | `SRC-014`, `SRC-015`, `SRC-016` | The site existed, but public records do not authenticate McAfee control. The domain was registered after death reporting. |
| Later WHACKD-named copycat contracts | Rejected pending separate provenance | `SRC-012`, `SRC-013` | Later tokens and zero-address speculation are high-risk false-signal sources unless independently tied to the official 2019 contract. |
| Snowkid inferred "John McAfee Token Allocation" wallet label | Hypothesis only | `SRC-012` | Useful community hypothesis, but not accepted as attribution without independent primary evidence. |
| Telegram-only or screenshot-only clue claims | Rejected | none accepted | No original public source or stable archive. Do not promote to candidates. |
| Generic Swarm/IPFS/Arweave payload-pointer theories | Not a candidate yet | `SRC-020`, `SRC-021`, `SRC-022` | These are valid technical formats for later testing, but no candidate pointer has provenance yet. |

## Current Answer From Option 1

There are public artifacts worth analyzing later: the official WHACKD contract, the britbonglogpost.com archived site, and the McAfee DMS/WHACKD public claim corpus. None currently proves a McAfee-controlled operational dead man switch. The accepted candidates should feed Option 2 only as bounded, reproducible inputs.
