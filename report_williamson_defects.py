#!/usr/bin/env python3
"""Report detailed defects for a stored Williamson search checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from williamson_search import candidate_metrics, expand_sequences


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
    free_state = np.array(payload["best_free_state"], dtype=np.int8)
    seqs = expand_sequences(free_state, n)
    metrics = candidate_metrics(seqs, n)

    print(f"Williamson defect report | order={order} | n={n}")
    print(f"best_score={metrics.total_score}")
    print(f"periodic_score={metrics.periodic_score}")
    print(f"row_sum_penalty={metrics.row_sum_penalty}")
    print(f"row_sums={metrics.row_sums}")
    print(f"row_sum_residual={metrics.row_sum_residual}")
    print(f"max_shift_violation={metrics.max_shift_violation}")
    print("top_shift_violations:")
    for item in metrics.top_shift_violations[: args.top]:
        print(
            f"  shift={item['shift']:>3} value={item['value']:>6} "
            f"abs={item['abs_value']:>6}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
