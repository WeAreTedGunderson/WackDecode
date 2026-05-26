#!/usr/bin/env python3
"""Reconstruct WHACKD transfer/burn evidence from public Ethereum RPC.

This is an Option 2 starter, not a decoder. It fetches ERC-20 Transfer logs for
the official WHACKD contract, groups logs by transaction, decodes common ERC-20
method selectors, optionally resolves internal token calls with RPC traces, and
classifies burn candidates without assigning hidden-message meaning to any event.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


CONTRACT = "0xcf8335727b776d190f9d15a54e6b9b9348439eee"
CREATION_BLOCK = 8_943_162
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
DEFAULT_RPC = "https://ethereum.publicnode.com"
FALLBACK_RPCS = [
    DEFAULT_RPC,
    "https://rpc.flashbots.net",
    "https://eth.llamarpc.com",
]
REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "WackDecode-WHACKD-Reconstruction/0.1",
}

SELECTORS = {
    "0xa9059cbb": "transfer(address,uint256)",
    "0x23b872dd": "transferFrom(address,address,uint256)",
    "0x095ea7b3": "approve(address,uint256)",
}


def rpc_call(url: str, method: str, params: list, request_id: int = 1, retries: int = 4) -> object:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers=REQUEST_HEADERS)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "ignore")
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"RPC HTTP {exc.code}: {detail}")
    if "error" in body:
        raise RuntimeError(f"RPC error from {method}: {body['error']}")
    return body.get("result")


def rpc_batch(url: str, calls: list[tuple[str, list]], retries: int = 4) -> list[object]:
    payload = json.dumps(
        [
            {"jsonrpc": "2.0", "id": index, "method": method, "params": params}
            for index, (method, params) in enumerate(calls, start=1)
        ]
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers=REQUEST_HEADERS)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise
    by_id = {item["id"]: item for item in body}
    results = []
    for index in range(1, len(calls) + 1):
        item = by_id[index]
        if "error" in item:
            raise RuntimeError(f"RPC batch error: {item['error']}")
        results.append(item.get("result"))
    return results


def hex_int(value: str) -> int:
    return int(value, 16)


def hex_block(block: int) -> str:
    return hex(block)


def topic_address(topic: str) -> str:
    return "0x" + topic[-40:].lower()


def decode_selector(input_data: str | None) -> str:
    if not input_data or input_data == "0x":
        return ""
    return SELECTORS.get(input_data[:10].lower(), input_data[:10].lower())


def is_token_counter_method(method: str) -> bool:
    return method in ("transfer(address,uint256)", "transferFrom(address,address,uint256)")


def classify_contract_method(tx_to: str, input_data: str | None) -> tuple[str, str]:
    selector = decode_selector(input_data)
    if not tx_to:
        return "contract_creation", "creation"
    if tx_to == CONTRACT:
        return selector, "direct_contract_call"
    return f"external_call:{selector}", "external_contract_call"


def classify_tx(logs: list[dict]) -> str:
    transfer_logs = [log for log in logs if log["event"] == "Transfer"]
    if not transfer_logs:
        return "no_transfer_logs"
    burns = [log for log in transfer_logs if log["to_address"] == ZERO_ADDRESS]
    nonburns = [log for log in transfer_logs if log["to_address"] != ZERO_ADDRESS]
    if burns and not nonburns:
        return "burn_only_candidate"
    if burns and nonburns:
        if sum(int(log["raw_value"]) for log in nonburns) == 0:
            return "full_burn_candidate"
        return "mixed_transfer_and_burn_candidate"
    return "nonburn_transfer"


def reconstruct_counter(tx_rows: list[dict]) -> list[dict]:
    random_value = 0
    certainty = "exact"
    rows = []
    transfer_call_ordinal = 0
    transfer_ordinal = 0
    transfer_from_ordinal = 0
    for tx in tx_rows:
        method = tx["method"]
        random_before = random_value
        counter_action = "not_counter_relevant"
        certainty_before = certainty
        if method == "transfer(address,uint256)":
            transfer_call_ordinal += 1
            if tx["call_scope"] == "direct_contract_call":
                transfer_ordinal += 1
            if random_value < 999:
                random_value += 1
                counter_action = "increment"
            else:
                random_value = 0
                counter_action = "reset_full_burn"
        elif method == "transferFrom(address,address,uint256)":
            transfer_from_ordinal += 1
            counter_action = "read_only_full_burn_branch" if random_value >= 999 else "read_only_normal_branch"
        elif method.startswith("external_call:"):
            certainty = "uncertain_after_external_call"
            counter_action = "unknown_internal_token_call"
        random_after = random_value
        certainty_after = certainty
        expected_full_burn = certainty_before == "exact" and (
            (
                method == "transfer(address,uint256)"
                and counter_action == "reset_full_burn"
            )
            or (
                method == "transferFrom(address,address,uint256)"
                and random_before >= 999
            )
        )
        observed_full_burn = tx["classification"] == "full_burn_candidate"
        rows.append(
            {
                "block_number": tx["block_number"],
                "block_timestamp_utc": tx["block_timestamp_utc"],
                "transaction_hash": tx["transaction_hash"],
                "transaction_index": tx["transaction_index"],
                "method": method,
                "call_scope": tx["call_scope"],
                "outer_method": tx.get("outer_method", ""),
                "traced_token_method": tx.get("traced_token_method", ""),
                "trace_status": tx.get("trace_status", ""),
                "trace_token_call_count": tx.get("trace_token_call_count", ""),
                "counter_relevant": is_token_counter_method(method),
                "transfer_call_ordinal": transfer_call_ordinal
                if method == "transfer(address,uint256)"
                else "",
                "direct_transfer_ordinal": transfer_ordinal
                if method == "transfer(address,uint256)" and tx["call_scope"] == "direct_contract_call"
                else "",
                "transfer_from_ordinal": transfer_from_ordinal
                if method == "transferFrom(address,address,uint256)"
                else "",
                "random_before": random_before
                if is_token_counter_method(method)
                else "",
                "random_after": random_after
                if is_token_counter_method(method)
                else "",
                "counter_action": counter_action,
                "counter_certainty_before": certainty_before,
                "counter_certainty_after": certainty_after,
                "expected_full_burn_from_counter": expected_full_burn,
                "observed_full_burn_candidate": observed_full_burn,
                "classification": tx["classification"],
                "burn_log_count": tx["burn_log_count"],
                "burn_raw_value": tx["burn_raw_value"],
                "nonburn_raw_value": tx["nonburn_raw_value"],
            }
        )
    return rows


def get_logs(url: str, from_block: int, to_block: int) -> list[dict]:
    params = [
        {
            "fromBlock": hex_block(from_block),
            "toBlock": hex_block(to_block),
            "address": CONTRACT,
            "topics": [TRANSFER_TOPIC],
        }
    ]
    return rpc_call(url, "eth_getLogs", params) or []


def fetch_logs(url: str, from_block: int, to_block: int, chunk_size: int) -> list[dict]:
    all_logs: list[dict] = []
    start = from_block
    while start <= to_block:
        end = min(start + chunk_size - 1, to_block)
        logs = get_logs(url, start, end)
        print(f"blocks {start}-{end}: {len(logs)} Transfer logs", file=sys.stderr)
        all_logs.extend(logs)
        start = end + 1
        time.sleep(0.2)
    return all_logs


def normalize_logs(raw_logs: list[dict]) -> list[dict]:
    normalized = []
    for log in raw_logs:
        topics = [topic.lower() for topic in log["topics"]]
        normalized.append(
            {
                "block_number": hex_int(log["blockNumber"]),
                "transaction_hash": log["transactionHash"].lower(),
                "transaction_index": hex_int(log["transactionIndex"]),
                "log_index": hex_int(log["logIndex"]),
                "event": "Transfer",
                "from_address": topic_address(topics[1]),
                "to_address": topic_address(topics[2]),
                "raw_value": str(hex_int(log["data"])),
            }
        )
    normalized.sort(key=lambda row: (row["block_number"], row["transaction_index"], row["log_index"]))
    return normalized


def extract_parity_trace_token_calls(trace_result: object) -> list[dict]:
    token_calls = []
    if not isinstance(trace_result, list):
        return token_calls
    for item in trace_result:
        if not isinstance(item, dict):
            continue
        action = item.get("action") or {}
        to_address = (action.get("to") or "").lower()
        input_data = action.get("input") or ""
        method = decode_selector(input_data)
        if to_address == CONTRACT and is_token_counter_method(method):
            token_calls.append(
                {
                    "method": method,
                    "from_address": (action.get("from") or "").lower(),
                    "to_address": to_address,
                    "input": input_data,
                    "trace_address": ".".join(str(part) for part in item.get("traceAddress", [])),
                    "trace_type": item.get("type", ""),
                }
            )
    return token_calls


def extract_calltree_token_calls(call: object, prefix: str = "") -> list[dict]:
    token_calls = []
    if not isinstance(call, dict):
        return token_calls
    to_address = (call.get("to") or "").lower()
    input_data = call.get("input") or ""
    method = decode_selector(input_data)
    if to_address == CONTRACT and is_token_counter_method(method):
        token_calls.append(
            {
                "method": method,
                "from_address": (call.get("from") or "").lower(),
                "to_address": to_address,
                "input": input_data,
                "trace_address": prefix,
                "trace_type": call.get("type", ""),
            }
        )
    for index, child in enumerate(call.get("calls") or []):
        child_prefix = f"{prefix}.{index}" if prefix else str(index)
        token_calls.extend(extract_calltree_token_calls(child, child_prefix))
    return token_calls


def fetch_trace_token_calls(url: str, tx_hash: str) -> tuple[str, list[dict]]:
    try:
        trace_result = rpc_call(url, "trace_transaction", [tx_hash])
        token_calls = extract_parity_trace_token_calls(trace_result)
        return "trace_transaction_ok", token_calls
    except Exception as parity_exc:
        try:
            debug_result = rpc_call(url, "debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}])
            token_calls = extract_calltree_token_calls(debug_result)
            return "debug_callTracer_ok", token_calls
        except Exception as debug_exc:
            return f"trace_unavailable: {parity_exc}; {debug_exc}", []


def resolve_external_token_calls(
    url: str, txs: dict[str, dict], trace_mode: str
) -> dict[str, dict]:
    if trace_mode == "off":
        return {}

    trace_rows = {}
    external_hashes = [
        tx_hash
        for tx_hash, tx in txs.items()
        if tx["call_scope"] == "external_contract_call"
    ]
    for tx_hash in external_hashes:
        status, token_calls = fetch_trace_token_calls(url, tx_hash)
        if not token_calls:
            if trace_mode == "required":
                raise RuntimeError(f"No token trace calls found for {tx_hash}: {status}")
            txs[tx_hash]["trace_status"] = status
            txs[tx_hash]["trace_token_call_count"] = 0
            trace_rows[tx_hash] = {"transaction_hash": tx_hash, "trace_status": status}
            continue

        if len(token_calls) == 1:
            token_call = token_calls[0]
            txs[tx_hash]["method"] = token_call["method"]
            txs[tx_hash]["call_scope"] = "traced_internal_contract_call"
            txs[tx_hash]["traced_token_method"] = token_call["method"]
            txs[tx_hash]["trace_status"] = status
            txs[tx_hash]["trace_token_call_count"] = 1
            txs[tx_hash]["trace_address"] = token_call["trace_address"]
            txs[tx_hash]["trace_from_address"] = token_call["from_address"]
        else:
            txs[tx_hash]["trace_status"] = f"{status}:multiple_token_calls"
            txs[tx_hash]["trace_token_call_count"] = len(token_calls)
            if trace_mode == "required":
                raise RuntimeError(f"Multiple token trace calls found for {tx_hash}")

        for index, token_call in enumerate(token_calls, start=1):
            trace_rows[f"{tx_hash}:{index}"] = {
                "transaction_hash": tx_hash,
                "trace_status": status,
                "trace_token_call_index": index,
                "trace_token_call_count": len(token_calls),
                "trace_address": token_call["trace_address"],
                "trace_type": token_call["trace_type"],
                "trace_from_address": token_call["from_address"],
                "trace_to_address": token_call["to_address"],
                "traced_token_method": token_call["method"],
            }
        time.sleep(0.2)
    return trace_rows


def fetch_blocks(url: str, block_numbers: list[int], batch_size: int) -> dict[int, dict]:
    blocks: dict[int, dict] = {}
    for i in range(0, len(block_numbers), batch_size):
        chunk = block_numbers[i : i + batch_size]
        calls = [("eth_getBlockByNumber", [hex_block(block), False]) for block in chunk]
        for block_number, block in zip(chunk, rpc_batch(url, calls)):
            timestamp = hex_int(block["timestamp"])
            blocks[block_number] = {
                "block_hash": block["hash"],
                "block_timestamp": timestamp,
                "block_timestamp_utc": datetime.fromtimestamp(
                    timestamp, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
        time.sleep(0.5)
    return blocks


def fetch_transactions(url: str, tx_hashes: list[str], batch_size: int) -> dict[str, dict]:
    txs: dict[str, dict] = {}
    for i in range(0, len(tx_hashes), batch_size):
        chunk = tx_hashes[i : i + batch_size]
        calls = [("eth_getTransactionByHash", [tx_hash]) for tx_hash in chunk]
        for tx_hash, tx in zip(chunk, rpc_batch(url, calls)):
            tx_to = (tx.get("to") or "").lower() if tx.get("to") else ""
            method, call_scope = classify_contract_method(tx_to, tx.get("input"))
            txs[tx_hash] = {
                "from_address": (tx.get("from") or "").lower(),
                "to_address": tx_to,
                "method": method,
                "outer_method": method,
                "call_scope": call_scope,
                "input": tx.get("input", ""),
                "traced_token_method": "",
                "trace_status": "not_requested",
                "trace_token_call_count": "",
                "trace_address": "",
                "trace_from_address": "",
            }
        time.sleep(0.5)
    return txs


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def select_rpc_url(preferred_url: str) -> str:
    urls = [preferred_url]
    for url in FALLBACK_RPCS:
        if url not in urls:
            urls.append(url)
    for url in urls:
        try:
            chain_id = rpc_call(url, "eth_chainId", [])
            if chain_id == "0x1":
                return url
            print(f"skipping {url}: eth_chainId returned {chain_id}", file=sys.stderr)
        except Exception as exc:
            print(f"skipping {url}: {exc}", file=sys.stderr)
    raise RuntimeError("No usable Ethereum mainnet RPC endpoint found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", default=os.environ.get("ETH_RPC_URL", DEFAULT_RPC))
    parser.add_argument("--from-block", type=int, default=CREATION_BLOCK)
    parser.add_argument("--to-block", type=int, required=True)
    parser.add_argument("--chunk-size", type=int, default=2_000)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument(
        "--trace-mode",
        choices=("auto", "off", "required"),
        default="auto",
        help=(
            "Resolve external-contract WHACKD log rows through trace_transaction "
            "or debug_traceTransaction when available. 'auto' keeps running if "
            "tracing is unavailable; 'required' fails on unresolved external rows."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "option2-data",
    )
    args = parser.parse_args()

    if args.from_block < CREATION_BLOCK:
        raise SystemExit(f"from-block must be >= creation block {CREATION_BLOCK}")
    if args.to_block < args.from_block:
        raise SystemExit("to-block must be >= from-block")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    rpc_url = select_rpc_url(args.rpc_url)
    print(f"using RPC endpoint: {rpc_url}", file=sys.stderr)

    raw_logs = fetch_logs(rpc_url, args.from_block, args.to_block, args.chunk_size)
    logs = normalize_logs(raw_logs)
    block_map = fetch_blocks(rpc_url, sorted({row["block_number"] for row in logs}), args.batch_size)
    tx_map = fetch_transactions(rpc_url, sorted({row["transaction_hash"] for row in logs}), args.batch_size)
    trace_rows_by_key = resolve_external_token_calls(rpc_url, tx_map, args.trace_mode)

    for row in logs:
        row.update(block_map[row["block_number"]])
        tx = tx_map[row["transaction_hash"]]
        row["tx_from_address"] = tx["from_address"]
        row["tx_to_address"] = tx["to_address"]
        row["method"] = tx["method"]
        row["outer_method"] = tx["outer_method"]
        row["call_scope"] = tx["call_scope"]
        row["traced_token_method"] = tx["traced_token_method"]
        row["trace_status"] = tx["trace_status"]

    grouped = defaultdict(list)
    for row in logs:
        grouped[row["transaction_hash"]].append(row)

    tx_rows = []
    for tx_hash, tx_logs in grouped.items():
        tx = tx_map[tx_hash]
        burn_value = sum(int(log["raw_value"]) for log in tx_logs if log["to_address"] == ZERO_ADDRESS)
        nonburn_value = sum(int(log["raw_value"]) for log in tx_logs if log["to_address"] != ZERO_ADDRESS)
        first = tx_logs[0]
        tx_rows.append(
            {
                "block_number": first["block_number"],
                "block_timestamp_utc": first["block_timestamp_utc"],
                "transaction_index": first["transaction_index"],
                "transaction_hash": tx_hash,
                "method": tx["method"],
                "call_scope": tx["call_scope"],
                "outer_method": tx["outer_method"],
                "traced_token_method": tx["traced_token_method"],
                "trace_status": tx["trace_status"],
                "trace_token_call_count": tx["trace_token_call_count"],
                "trace_address": tx["trace_address"],
                "trace_from_address": tx["trace_from_address"],
                "tx_from_address": tx["from_address"],
                "tx_to_address": tx["to_address"],
                "transfer_log_count": len(tx_logs),
                "classification": classify_tx(tx_logs),
                "burn_log_count": sum(1 for log in tx_logs if log["to_address"] == ZERO_ADDRESS),
                "burn_raw_value": str(burn_value),
                "nonburn_raw_value": str(nonburn_value),
            }
        )
    tx_rows.sort(key=lambda row: (row["block_number"], row["transaction_index"], row["transaction_hash"]))
    counter_rows = reconstruct_counter(tx_rows)

    log_fields = [
        "block_number",
        "block_timestamp_utc",
        "block_timestamp",
        "block_hash",
        "transaction_hash",
        "transaction_index",
        "log_index",
        "method",
        "outer_method",
        "call_scope",
        "traced_token_method",
        "trace_status",
        "tx_from_address",
        "tx_to_address",
        "event",
        "from_address",
        "to_address",
        "raw_value",
    ]
    tx_fields = [
        "block_number",
        "block_timestamp_utc",
        "transaction_index",
        "transaction_hash",
        "method",
        "call_scope",
        "outer_method",
        "traced_token_method",
        "trace_status",
        "trace_token_call_count",
        "trace_address",
        "trace_from_address",
        "tx_from_address",
        "tx_to_address",
        "transfer_log_count",
        "classification",
        "burn_log_count",
        "burn_raw_value",
        "nonburn_raw_value",
    ]
    counter_fields = [
        "block_number",
        "block_timestamp_utc",
        "transaction_hash",
        "transaction_index",
        "method",
        "call_scope",
        "outer_method",
        "traced_token_method",
        "trace_status",
        "trace_token_call_count",
        "counter_relevant",
        "transfer_call_ordinal",
        "direct_transfer_ordinal",
        "transfer_from_ordinal",
        "random_before",
        "random_after",
        "counter_action",
        "counter_certainty_before",
        "counter_certainty_after",
        "expected_full_burn_from_counter",
        "observed_full_burn_candidate",
        "classification",
        "burn_log_count",
        "burn_raw_value",
        "nonburn_raw_value",
    ]

    write_csv(args.out_dir / "transfer_logs.csv", logs, log_fields)
    write_csv(args.out_dir / "transaction_summary.csv", tx_rows, tx_fields)
    write_csv(args.out_dir / "counter_reconstruction.csv", counter_rows, counter_fields)
    trace_rows = list(trace_rows_by_key.values())
    trace_fields = [
        "transaction_hash",
        "trace_status",
        "trace_token_call_index",
        "trace_token_call_count",
        "trace_address",
        "trace_type",
        "trace_from_address",
        "trace_to_address",
        "traced_token_method",
    ]
    write_csv(args.out_dir / "trace_token_calls.csv", trace_rows, trace_fields)
    full_burn_rows = [
        row
        for row in counter_rows
        if row["expected_full_burn_from_counter"] or row["observed_full_burn_candidate"]
    ]
    write_csv(args.out_dir / "full_burn_candidates.csv", full_burn_rows, counter_fields)

    metadata = {
        "contract": CONTRACT,
        "creation_block": CREATION_BLOCK,
        "from_block": args.from_block,
        "to_block": args.to_block,
        "rpc_url": rpc_url,
        "transfer_log_count": len(logs),
        "transaction_count": len(tx_rows),
        "direct_contract_transaction_count": sum(
            1 for row in tx_rows if row["call_scope"] == "direct_contract_call"
        ),
        "external_contract_transaction_count": sum(
            1 for row in tx_rows if row["call_scope"] == "external_contract_call"
        ),
        "traced_internal_contract_transaction_count": sum(
            1 for row in tx_rows if row["call_scope"] == "traced_internal_contract_call"
        ),
        "trace_mode": args.trace_mode,
        "trace_token_call_count": len(trace_rows),
        "counter_certainty": "uncertain_after_external_call"
        if any(row["call_scope"] == "external_contract_call" for row in tx_rows)
        else "exact_for_resolved_token_calls",
        "counter_relevant_transaction_count": sum(
            1 for row in counter_rows if row["counter_relevant"]
        ),
        "token_transfer_count": sum(
            1 for row in counter_rows if row["method"] == "transfer(address,uint256)"
        ),
        "direct_transfer_count": sum(
            1
            for row in counter_rows
            if row["method"] == "transfer(address,uint256)"
            and row["call_scope"] == "direct_contract_call"
        ),
        "transfer_from_count": sum(
            1
            for row in counter_rows
            if row["method"] == "transferFrom(address,address,uint256)"
        ),
        "expected_full_burn_count": sum(
            1 for row in counter_rows if row["expected_full_burn_from_counter"]
        ),
        "observed_full_burn_candidate_count": sum(
            1 for row in counter_rows if row["observed_full_burn_candidate"]
        ),
        "full_burn_candidate_file_count": len(full_burn_rows),
        "classification_counts": dict(
            sorted(
                {
                    key: sum(1 for row in tx_rows if row["classification"] == key)
                    for key in {row["classification"] for row in tx_rows}
                }.items()
            )
        ),
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    (args.out_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
