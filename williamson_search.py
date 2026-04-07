#!/usr/bin/env python3
"""Williamson-style search lane for FrontierMath Hadamard targets."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ORDER_TO_N = {
    428: 107,
    668: 167,
}


def independent_size(n: int) -> int:
    return n // 2 + 1


def expand_symmetric(free_bits: np.ndarray, n: int) -> np.ndarray:
    seq = np.empty(n, dtype=np.int8)
    m = independent_size(n)
    seq[:m] = free_bits
    for i in range(1, m):
        seq[-i] = free_bits[i]
    return seq


def paf(seq: np.ndarray) -> np.ndarray:
    fft_vals = np.fft.fft(seq.astype(np.float64))
    corr = np.fft.ifft(np.abs(fft_vals) ** 2).real
    return np.rint(corr).astype(np.int64)


def periodic_score(seqs: list[np.ndarray]) -> int:
    combined = sum((paf(seq) for seq in seqs), start=np.zeros(len(seqs[0]), dtype=np.int64))
    return int(np.sum(combined[1:] ** 2))


def row_sum_penalty(seqs: list[np.ndarray], n: int) -> int:
    row_sums = [int(seq.sum()) for seq in seqs]
    return int((sum(val * val for val in row_sums) - (4 * n)) ** 2)


def total_score(seqs: list[np.ndarray], n: int) -> int:
    return periodic_score(seqs) + row_sum_penalty(seqs, n)


def circulant(first_row: np.ndarray) -> np.ndarray:
    n = len(first_row)
    return np.array([np.roll(first_row, i) for i in range(n)], dtype=np.int8)


def williamson_matrix(seqs: list[np.ndarray]) -> np.ndarray:
    a, b, c, d = [circulant(seq) for seq in seqs]
    top = np.hstack([a, b, c, d])
    row2 = np.hstack([-b, a, -d, c])
    row3 = np.hstack([-c, d, a, -b])
    row4 = np.hstack([-d, -c, b, a])
    return np.vstack([top, row2, row3, row4]).astype(np.int8)


def save_csv_matrix(path: Path, matrix: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(matrix.tolist())


def score_candidate(free_state: np.ndarray, n: int) -> tuple[int, list[np.ndarray]]:
    seqs = [expand_symmetric(free_state[i], n) for i in range(4)]
    return total_score(seqs, n), seqs


@dataclass
class SearchConfig:
    order: int
    n: int
    steps: int
    batch: int
    seed: int
    checkpoint_every: int
    temp_start: float
    temp_end: float


def checkpoint(run_dir: Path, label: str, payload: dict) -> None:
    path = run_dir / label
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, choices=sorted(ORDER_TO_N), required=True)
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--seed", type=int, default=67)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--temp-start", type=float, default=1.5)
    parser.add_argument("--temp-end", type=float, default=0.02)
    args = parser.parse_args()

    cfg = SearchConfig(
        order=args.order,
        n=ORDER_TO_N[args.order],
        steps=args.steps,
        batch=args.batch,
        seed=args.seed,
        checkpoint_every=args.checkpoint_every,
        temp_start=args.temp_start,
        temp_end=args.temp_end,
    )

    run_dir = Path("runs")
    run_dir.mkdir(exist_ok=True)

    rng = np.random.default_rng(cfg.seed)
    m = independent_size(cfg.n)
    free_state = rng.choice(np.array([-1, 1], dtype=np.int8), size=(4, m))
    current_score, current_seqs = score_candidate(free_state, cfg.n)
    best_state = free_state.copy()
    best_score = current_score
    best_seqs = [seq.copy() for seq in current_seqs]
    start = time.time()

    print(f"Hadamard Williamson search | order={cfg.order} | n={cfg.n}")
    print(f"initial score={current_score}")

    for step in range(1, cfg.steps + 1):
        progress = (step - 1) / max(1, cfg.steps - 1)
        temperature = cfg.temp_start * ((cfg.temp_end / cfg.temp_start) ** progress)

        best_trial_state = None
        best_trial_score = None

        for _ in range(cfg.batch):
            trial = free_state.copy()
            seq_idx = int(rng.integers(0, 4))
            bit_idx = int(rng.integers(0, m))
            trial[seq_idx, bit_idx] *= -1

            trial_score, _ = score_candidate(trial, cfg.n)
            if best_trial_score is None or trial_score < best_trial_score:
                best_trial_score = trial_score
                best_trial_state = trial

        accept = False
        if best_trial_score is not None:
            if best_trial_score <= current_score:
                accept = True
            else:
                delta = best_trial_score - current_score
                accept = rng.random() < math.exp(-delta / max(temperature, 1e-9))

        if accept and best_trial_state is not None:
            free_state = best_trial_state
            current_score, current_seqs = score_candidate(free_state, cfg.n)

        if current_score < best_score:
            best_score = current_score
            best_state = free_state.copy()
            best_seqs = [seq.copy() for seq in current_seqs]
            print(f"[step {step}] new best score={best_score}")

            if best_score == 0:
                matrix = williamson_matrix(best_seqs)
                matrix_path = run_dir / f"order_{cfg.order}_best_matrix.csv"
                save_csv_matrix(matrix_path, matrix)
                print(f"score 0 candidate written to {matrix_path}")

        if step % cfg.checkpoint_every == 0 or step == 1:
            payload = {
                "order": cfg.order,
                "n": cfg.n,
                "step": step,
                "elapsed_sec": round(time.time() - start, 3),
                "current_score": int(current_score),
                "best_score": int(best_score),
                "best_free_state": best_state.tolist(),
            }
            checkpoint(run_dir, f"order_{cfg.order}_latest.json", payload)
            print(
                f"[step {step}] current={current_score} best={best_score} "
                f"elapsed={time.time() - start:.1f}s"
            )

    payload = {
        "order": cfg.order,
        "n": cfg.n,
        "steps": cfg.steps,
        "elapsed_sec": round(time.time() - start, 3),
        "best_score": int(best_score),
        "best_free_state": best_state.tolist(),
    }
    checkpoint(run_dir, f"order_{cfg.order}_final.json", payload)
    print(f"done | best_score={best_score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

