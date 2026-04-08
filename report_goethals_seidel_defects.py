#!/usr/bin/env python3
"""Report detailed defects for a stored Goethals-Seidel checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from goethals_seidel_search import candidate_metrics, combined_paf, sds_lambda_from_signature, signature_to_negative_counts


def indicator_fourier_profile(state: np.ndarray) -> tuple[int, int, list[dict[str, int]]]:
    n = state.shape[1]
    blocks = [(state[row] == -1).astype(np.float64) for row in range(4)]
    target = n
    total = np.zeros(n, dtype=np.float64)
    for block in blocks:
        fft_vals = np.fft.fft(block)
        total += np.abs(fft_vals) ** 2

    deviations = np.rint(total[1:] - target).astype(np.int64)
    items = [
        {
            "frequency": int(freq),
            "deviation": int(deviations[freq - 1]),
            "abs_deviation": int(abs(deviations[freq - 1])),
        }
        for freq in range(1, n)
        if deviations[freq - 1] != 0
    ]
    items.sort(key=lambda item: (-item["abs_deviation"], item["frequency"]))
    max_deviation = items[0]["abs_deviation"] if items else 0
    return target, int(max_deviation), items


def load_checkpoint(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_path", type=Path)
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args()

    payload = load_checkpoint(args.checkpoint_path)
    order = int(payload["order"])
    n = int(payload["n"])
    signature = tuple(int(value) for value in payload["signature"])
    state = np.array(payload["best_state"], dtype=np.int8)
    seqs = [state[i].copy() for i in range(4)]
    metrics = candidate_metrics(seqs, signature)
    combined = combined_paf(seqs)
    negative_counts = signature_to_negative_counts(signature, n)
    sds_lambda = sds_lambda_from_signature(signature, n)
    fourier_target, fourier_max_dev, fourier_items = indicator_fourier_profile(state)

    print(f"Goethals-Seidel defect report | order={order} | n={n}")
    print(f"signature={signature}")
    print(f"sds_parameters=({n}; {', '.join(str(value) for value in negative_counts)}; {sds_lambda})")
    print(f"indicator_fourier_target={fourier_target}")
    print(f"indicator_fourier_max_deviation={fourier_max_dev}")
    print(f"best_score={metrics.total_score}")
    print(f"periodic_score={metrics.periodic_score}")
    print(f"row_sums={metrics.row_sums}")
    print(f"max_shift_violation={metrics.max_shift_violation}")
    print("top_shift_violations:")
    for item in metrics.top_shift_violations[: args.top]:
        print(
            f"  shift={item['shift']:>3} value={item['value']:>6} "
            f"abs={item['abs_value']:>6}"
        )
    print("top_unique_sds_defects:")
    seen: set[int] = set()
    unique_items = []
    for shift in range(1, n):
        rep = min(shift, n - shift)
        if rep in seen:
            continue
        seen.add(rep)
        value = int(combined[rep])
        if value == 0:
            continue
        unique_items.append((rep, n - rep, value // 4))
    unique_items.sort(key=lambda item: (-abs(item[2]), item[0]))
    for rep, partner, delta in unique_items[: args.top]:
        print(
            f"  shifts={rep:>3}/{partner:>3} sds_delta={delta:>4} "
            f"combined={4 * delta:>4}"
        )
    print("top_indicator_fourier_deviations:")
    for item in fourier_items[: args.top]:
        print(
            f"  frequency={item['frequency']:>3} deviation={item['deviation']:>6} "
            f"abs={item['abs_deviation']:>6}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
