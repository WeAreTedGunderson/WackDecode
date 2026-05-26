# Option 2 WHACKD Reconstruction Notes

Prepared: 2026-05-24

## Scope

This is the first reproducible scaffold for reconstructing the official WHACKD contract history. It does not claim any DMS payload. It only builds tables that make later claims testable.

Official contract:

`0xCF8335727B776d190f9D15a54E6B9B9348439eEE`

Creation transaction:

`0x1bb323576cd7dcb12e9f8507a5e298a0136927a486f959e3984cb7cca21ed96b`

Creation block:

`8943162`

## Script

Run:

```powershell
python mcafee-dms-provenance\whackd_reconstruction.py --to-block 8950000
```

The script uses `ETH_RPC_URL` if set, otherwise `https://ethereum.publicnode.com`.

Outputs are written to:

`mcafee-dms-provenance/option2-data/`

Files:

- `transfer_logs.csv`: decoded ERC-20 `Transfer` logs.
- `transaction_summary.csv`: logs grouped by transaction, with method selector and burn classification.
- `counter_reconstruction.csv`: direct-call counter model with `random_before`, `random_after`, certainty, and rollover flags.
- `trace_token_calls.csv`: token-level calls found inside external-contract transactions when RPC trace support is available.
- `full_burn_candidates.csv`: bounded candidate-event table extracted from expected or observed full-burn rows.
- `bounded_candidate_strings.csv`: deterministic candidate strings generated only from exact full-burn rows.
- `bounded_candidate_format_tests.csv`: format-screen results for the bounded candidate strings.
- `run_metadata.json`: reproducibility metadata.

## Contract Source Alignment

Etherscan API v2 requires an API key for `getsourcecode`; no key was available in this environment. A public Sourcify partial match is available at:

`https://repo.sourcify.dev/contracts/partial_match/1/0xcf8335727b776d190f9d15a54e6b9b9348439eee/sources/Epstein.sol`

The source alignment supports these rules:

- Constructor mints `1,000,000,000 WHACKD` with 18 decimals to `0x23D3808fEaEb966F9C6c5EF326E1dD37686E5972`.
- `transfer(address,uint256)` subtracts from `msg.sender`, then if `random < 999`, increments `random`, sends 90% to the recipient, and burns 10% to `address(0)`.
- If `transfer` runs when `random >= 999`, it resets `random` to `0`, emits a zero-value recipient transfer, and burns 100%.
- `transferFrom(address,address,uint256)` branches on `random`, but does not increment or reset it. If `random >= 999`, `transferFrom` can full-burn while leaving `random` stuck at `999`.
- A transaction whose outer `to` is not the WHACKD contract can still emit WHACKD logs through an internal call. The current script attempts `trace_transaction` first, then `debug_traceTransaction` with `callTracer`; unresolved external rows stay marked `external_contract_call` and make later counter state uncertain.

## Current Classification Rules

The script intentionally uses conservative labels:

- `nonburn_transfer`: transfer logs exist, none to the zero address.
- `mixed_transfer_and_burn_candidate`: a transaction emits both recipient transfer logs and burn logs.
- `burn_only_candidate`: all transfer logs in the transaction go to the zero address.

These labels are not proof by themselves. Counter rows are source-aligned only when the transaction is a direct call to the WHACKD contract. External-contract calls need trace-level decoding before they can be safely treated as `transfer` or `transferFrom`.

## Smoke Run

Command:

```powershell
python mcafee-dms-provenance\whackd_reconstruction.py --to-block 8944000 --chunk-size 1000 --batch-size 10 --out-dir mcafee-dms-provenance\option2-data
```

Result:

- Block range: `8943162` through `8944000`.
- Transfer logs: `631`.
- Grouped transactions: `316`.
- Direct WHACKD contract transactions: `315`.
- Traced internal token calls: `0`.
- Classifications: `315` `mixed_transfer_and_burn_candidate`, `1` `nonburn_transfer`.
- The one `nonburn_transfer` is the creation transaction mint from the zero address to the deployer.
- The early post-creation transfers show paired recipient-transfer plus zero-address-burn logs, consistent with the 10% burn behavior.

## Larger Sweep

Command:

```powershell
python mcafee-dms-provenance\whackd_reconstruction.py --to-block 8945000 --chunk-size 1000 --batch-size 10 --out-dir mcafee-dms-provenance\option2-data-8945000
```

Result:

- Block range: `8943162` through `8945000`.
- Transfer logs: `2,989`.
- Grouped transactions: `1,495`.
- Direct WHACKD contract transactions: `1,491`.
- External-contract transactions left unresolved: `0`.
- Traced internal WHACKD calls: `3`, all `transferFrom(address,address,uint256)`.
- Direct `transfer` calls: `1,491`.
- `transferFrom` calls: `3`.
- Expected full-burn rows: `1`.
- Observed full-burn candidates: `1`.
- Counter certainty: `exact_for_resolved_token_calls`.

First full-burn candidate:

- Block: `8944493`.
- Time: `2019-11-16 12:56:33 UTC`.
- Transaction: `0x8be7bd5924e3393c730a8edd8dae23915896d9e1ff33cae1c3cd696bc2bd3abd`.
- Direct transfer ordinal: `1000`.
- `random_before`: `999`.
- `random_after`: `0`.
- Burn raw value: `11972156190000000000000`.
- Non-burn raw value: `0`.

The first full-burn event is exact under the source-aligned token-call model. Trace data resolves the three formerly external rows in this range as internal `transferFrom` calls, which do not increment or reset `random`, so counter certainty remains exact through block `8945000`.

## Extended Sweep

Command:

```powershell
python mcafee-dms-provenance\whackd_reconstruction.py --to-block 8950000 --chunk-size 1000 --batch-size 10 --out-dir mcafee-dms-provenance\option2-data-8950000
```

Result:

- Block range: `8943162` through `8950000`.
- Transfer logs: `10,043`.
- Grouped transactions: `5,022`.
- Direct WHACKD contract transactions: `5,004`.
- External-contract transactions left unresolved: `0`.
- Traced internal WHACKD calls: `17` (`16` `transferFrom`, `1` `transfer`).
- Token-level `transfer` calls: `5,005`.
- Direct `transfer` calls: `5,004`.
- `transferFrom` calls: `16`.
- Expected full-burn rows: `5`.
- Observed full-burn candidates: `5`.
- Counter certainty: `exact_for_resolved_token_calls`.

Exact full-burn candidates in this range:

| Token transfer ordinal | Direct transfer ordinal | Block | Time | Transaction |
|---:|---:|---:|---|---|
| `1000` | `1000` | `8944493` | `2019-11-16 12:56:33 UTC` | `0x8be7bd5924e3393c730a8edd8dae23915896d9e1ff33cae1c3cd696bc2bd3abd` |
| `2000` | `2000` | `8947258` | `2019-11-16 23:38:27 UTC` | `0xf08a81141f00b66f0c5e2ec7ba2988ea4a8301ee7001c04cec86278a958b63d8` |
| `3000` | `2999` | `8947976` | `2019-11-17 02:30:34 UTC` | `0x5b006e7a92486a10d001dc6f5045d7ac7a0a0cfc686bf369c2605c4adbcd575a` |
| `4000` | `3999` | `8948982` | `2019-11-17 06:37:27 UTC` | `0xcee6e8a5e0a1c7e79f6d7b052c6397b9271304eff3edfa5d8d0cd03e74ee3569` |
| `5000` | `4999` | `8949990` | `2019-11-17 10:48:29 UTC` | `0x83188b61b38c6b969883cfe72fba37ac892be9d853b6199641a1d97b1a7a0c27` |

The offset after the second full-burn row is expected: one traced internal `transfer(address,uint256)` call occurs before the third full-burn row and increments the token-level counter, but it is not a direct outer call to the WHACKD contract.

## Bounded Candidate-String Screen

Command:

```powershell
python mcafee-dms-provenance\bounded_candidate_tests.py mcafee-dms-provenance\option2-data-8950000\full_burn_candidates.csv
```

Result:

- Exact full-burn rows tested: `5`.
- Deterministic candidate strings generated: `60`.
- Specific public-reference format matches: `0`.
- Broad hash-shaped format matches: `30`.
- Output files:
  - `mcafee-dms-provenance/option2-data-8950000/bounded_candidate_strings.csv`
  - `mcafee-dms-provenance/option2-data-8950000/bounded_candidate_format_tests.csv`

The broad matches are expected collisions for 32-byte hex values and base64url-encoded hashes. They are recorded as `format_match_only`, not as payload evidence. No candidate string in this bounded pass matched a specific IPFS CID, ENS name, or Ethereum address pattern.

## Next Work

1. Continue larger range reconstruction in bounded chunks and preserve `trace_token_calls.csv` with each run.
2. Keep `transferFrom` rows separate from `transfer` rows in any downstream analysis.
3. Extend bounded candidate tests only from exact rows in `full_burn_candidates.csv`.
4. Do not test payload interpretations from rows whose counter certainty is marked incomplete.
5. Treat broad hash-shaped matches as false-positive-prone until a specific public reference resolves.

## Evidence Boundary

The official WHACKD contract and creation transaction are high-confidence public artifacts. No result from this script should be interpreted as a DMS payload, release key, or McAfee-controlled post-death trigger unless a separate public authentication chain is found.
