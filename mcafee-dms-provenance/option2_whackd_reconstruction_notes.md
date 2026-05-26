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
python reports\mcafee-dms-provenance\whackd_reconstruction.py --to-block 8950000
```

The script uses `ETH_RPC_URL` if set, otherwise `https://ethereum.publicnode.com`.

Outputs are written to:

`reports/mcafee-dms-provenance/option2-data/`

Files:

- `transfer_logs.csv`: decoded ERC-20 `Transfer` logs.
- `transaction_summary.csv`: logs grouped by transaction, with method selector and burn classification.
- `counter_reconstruction.csv`: direct-call counter model with `random_before`, `random_after`, certainty, and rollover flags.
- `full_burn_candidates.csv`: bounded candidate-event table extracted from expected or observed full-burn rows.
- `run_metadata.json`: reproducibility metadata.

## Contract Source Alignment

Etherscan API v2 requires an API key for `getsourcecode`; no key was available in this environment. A public Sourcify partial match is available at:

`https://repo.sourcify.dev/contracts/partial_match/1/0xcf8335727b776d190f9d15a54e6b9b9348439eee/sources/Epstein.sol`

The source alignment supports these rules:

- Constructor mints `1,000,000,000 WHACKD` with 18 decimals to `0x23D3808fEaEb966F9C6c5EF326E1dD37686E5972`.
- `transfer(address,uint256)` subtracts from `msg.sender`, then if `random < 999`, increments `random`, sends 90% to the recipient, and burns 10% to `address(0)`.
- If `transfer` runs when `random >= 999`, it resets `random` to `0`, emits a zero-value recipient transfer, and burns 100%.
- `transferFrom(address,address,uint256)` branches on `random`, but does not increment or reset it. If `random >= 999`, `transferFrom` can full-burn while leaving `random` stuck at `999`.
- A transaction whose outer `to` is not the WHACKD contract can still emit WHACKD logs through an internal call. Without trace data, those rows are marked `external_contract_call` and make later counter state uncertain.

## Current Classification Rules

The script intentionally uses conservative labels:

- `nonburn_transfer`: transfer logs exist, none to the zero address.
- `mixed_transfer_and_burn_candidate`: a transaction emits both recipient transfer logs and burn logs.
- `burn_only_candidate`: all transfer logs in the transaction go to the zero address.

These labels are not proof by themselves. Counter rows are source-aligned only when the transaction is a direct call to the WHACKD contract. External-contract calls need trace-level decoding before they can be safely treated as `transfer` or `transferFrom`.

## Smoke Run

Command:

```powershell
python reports\mcafee-dms-provenance\whackd_reconstruction.py --to-block 8944000 --chunk-size 1000 --batch-size 5
```

Result:

- Block range: `8943162` through `8944000`.
- Transfer logs: `631`.
- Grouped transactions: `316`.
- Classifications: `315` `mixed_transfer_and_burn_candidate`, `1` `nonburn_transfer`.
- The one `nonburn_transfer` is the creation transaction mint from the zero address to the deployer.
- The early post-creation transfers show paired recipient-transfer plus zero-address-burn logs, consistent with the 10% burn behavior.

## Larger Sweep

Command:

```powershell
python reports\mcafee-dms-provenance\whackd_reconstruction.py --to-block 8945000 --chunk-size 1000 --batch-size 5 --out-dir reports\mcafee-dms-provenance\option2-data-8945000
```

Result:

- Block range: `8943162` through `8945000`.
- Transfer logs: `2,989`.
- Grouped transactions: `1,495`.
- Direct WHACKD contract transactions: `1,491`.
- External-contract transactions that emitted WHACKD logs: `3`.
- Direct `transfer` calls: `1,491`.
- Direct `transferFrom` calls: `0`.
- Expected full-burn rows: `1`.
- Observed full-burn candidates: `1`.

First full-burn candidate:

- Block: `8944493`.
- Time: `2019-11-16 12:56:33 UTC`.
- Transaction: `0x8be7bd5924e3393c730a8edd8dae23915896d9e1ff33cae1c3cd696bc2bd3abd`.
- Direct transfer ordinal: `1000`.
- `random_before`: `999`.
- `random_after`: `0`.
- Burn raw value: `11972156190000000000000`.
- Non-burn raw value: `0`.

The first full-burn event is exact under the source-aligned direct-call model because it occurs before the first observed external-contract call in this sweep. After the three external calls beginning at block `8944551`, counter certainty becomes incomplete unless trace data identifies whether those internal calls invoked `transfer` or `transferFrom`.

## Next Work

1. Add trace support for external-contract rows if a node supports `trace_transaction` or `debug_traceTransaction`.
2. Run a larger range after trace handling is available, or use an Etherscan/API-key export to avoid public-RPC throttling.
3. Keep `transferFrom` rows separate from direct `transfer` rows.
4. Use `full_burn_candidates.csv` as the only input for bounded candidate-string tests.
5. Do not test payload interpretations from rows whose counter certainty is marked incomplete.

## Evidence Boundary

The official WHACKD contract and creation transaction are high-confidence public artifacts. No result from this script should be interpreted as a DMS payload, release key, or McAfee-controlled post-death trigger unless a separate public authentication chain is found.
