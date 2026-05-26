#!/usr/bin/env python3
"""Run bounded format screens on exact WHACKD full-burn candidates.

This is not a decoder and it does not resolve public gateways. It only turns
rows from full_burn_candidates.csv into deterministic strings and marks whether
those strings resemble public reference formats. Broad hash-shaped matches are
recorded as format-only collisions, not evidence of a payload.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import re
from pathlib import Path


REFERENCE_TESTS = [
    ("ipfs_cidv0", re.compile(r"^Qm[1-9A-HJ-NP-Za-km-z]{44}$"), "specific"),
    ("ipfs_cidv1_base32", re.compile(r"^bafy[a-z2-7]{20,}$"), "specific"),
    ("ens_name", re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)*\.eth$"), "specific"),
    ("ethereum_address", re.compile(r"^0x[a-fA-F0-9]{40}$"), "specific"),
    ("ethereum_tx_or_bytes32", re.compile(r"^0x[a-fA-F0-9]{64}$"), "broad"),
    ("hex_bytes32_no_prefix", re.compile(r"^[a-fA-F0-9]{64}$"), "broad"),
    ("arweave_txid_shape", re.compile(r"^[A-Za-z0-9_-]{43}$"), "broad"),
]


def canonical_row(row: dict) -> str:
    fields = [
        "block_number",
        "block_timestamp_utc",
        "transaction_hash",
        "transaction_index",
        "method",
        "call_scope",
        "transfer_call_ordinal",
        "direct_transfer_ordinal",
        "random_before",
        "random_after",
        "burn_raw_value",
        "nonburn_raw_value",
    ]
    return "|".join(str(row.get(field, "")) for field in fields)


def printable_ascii_from_hex(value: str) -> str:
    clean = value[2:] if value.startswith("0x") else value
    if len(clean) % 2:
        return ""
    try:
        raw = bytes.fromhex(clean)
    except ValueError:
        return ""
    if not raw:
        return ""
    text = raw.decode("ascii", "ignore")
    if len(text) != len(raw):
        return ""
    if any(ord(char) < 32 or ord(char) > 126 for char in text):
        return ""
    return text


def row_candidates(row: dict) -> list[dict]:
    canonical = canonical_row(row)
    canonical_bytes = canonical.encode("utf-8")
    sha256_hex = hashlib.sha256(canonical_bytes).hexdigest()
    sha3_hex = hashlib.sha3_256(canonical_bytes).hexdigest()
    sha256_b64url = base64.urlsafe_b64encode(bytes.fromhex(sha256_hex)).decode("ascii").rstrip("=")
    tx_hash = row["transaction_hash"]
    candidates = [
        ("transaction_hash", tx_hash),
        ("transaction_hash_no_prefix", tx_hash[2:] if tx_hash.startswith("0x") else tx_hash),
        ("canonical_row", canonical),
        ("canonical_row_sha256_hex", sha256_hex),
        ("canonical_row_sha256_0x", f"0x{sha256_hex}"),
        ("canonical_row_sha3_256_hex", sha3_hex),
        ("canonical_row_sha256_base64url", sha256_b64url),
        ("block_number", row["block_number"]),
        ("block_timestamp_utc", row["block_timestamp_utc"]),
        ("transfer_call_ordinal", row["transfer_call_ordinal"]),
        ("direct_transfer_ordinal", row["direct_transfer_ordinal"]),
        ("burn_raw_value", row["burn_raw_value"]),
    ]
    ascii_tx = printable_ascii_from_hex(tx_hash)
    if ascii_tx:
        candidates.append(("transaction_hash_ascii", ascii_tx))
    return [
        {
            "transaction_hash": row["transaction_hash"],
            "block_number": row["block_number"],
            "transfer_call_ordinal": row["transfer_call_ordinal"],
            "candidate_type": candidate_type,
            "candidate_value": candidate_value,
        }
        for candidate_type, candidate_value in candidates
    ]


def screen_candidate(candidate: dict) -> list[dict]:
    rows = []
    value = candidate["candidate_value"]
    for test_name, pattern, strength in REFERENCE_TESTS:
        if pattern.fullmatch(value):
            rows.append(
                {
                    **candidate,
                    "test_name": test_name,
                    "test_strength": strength,
                    "result": "format_match_only",
                    "note": (
                        "Specific public-reference shape; still unresolved"
                        if strength == "specific"
                        else "Broad hash-shaped collision; not evidence by itself"
                    ),
                }
            )
    if not rows:
        rows.append(
            {
                **candidate,
                "test_name": "reference_format_screen",
                "test_strength": "none",
                "result": "no_format_match",
                "note": "No supported public-reference shape matched this exact string",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("full_burn_candidates", type=Path)
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Defaults to the input file directory.",
    )
    args = parser.parse_args()

    out_dir = args.out_dir or args.full_burn_candidates.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    with args.full_burn_candidates.open(newline="", encoding="utf-8") as handle:
        exact_rows = [
            row
            for row in csv.DictReader(handle)
            if row.get("counter_certainty_before") == "exact"
            and row.get("counter_certainty_after") == "exact"
            and row.get("expected_full_burn_from_counter") == "True"
            and row.get("observed_full_burn_candidate") == "True"
        ]

    candidate_rows = []
    screen_rows = []
    for row in exact_rows:
        for candidate in row_candidates(row):
            candidate_rows.append(candidate)
            screen_rows.extend(screen_candidate(candidate))

    candidate_fields = [
        "transaction_hash",
        "block_number",
        "transfer_call_ordinal",
        "candidate_type",
        "candidate_value",
    ]
    screen_fields = candidate_fields + ["test_name", "test_strength", "result", "note"]
    write_csv(out_dir / "bounded_candidate_strings.csv", candidate_rows, candidate_fields)
    write_csv(out_dir / "bounded_candidate_format_tests.csv", screen_rows, screen_fields)

    specific_matches = sum(
        1
        for row in screen_rows
        if row["result"] == "format_match_only" and row["test_strength"] == "specific"
    )
    broad_matches = sum(
        1
        for row in screen_rows
        if row["result"] == "format_match_only" and row["test_strength"] == "broad"
    )
    print(
        {
            "exact_full_burn_rows": len(exact_rows),
            "candidate_strings": len(candidate_rows),
            "specific_format_matches": specific_matches,
            "broad_format_matches": broad_matches,
            "outputs": [
                str(out_dir / "bounded_candidate_strings.csv"),
                str(out_dir / "bounded_candidate_format_tests.csv"),
            ],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
