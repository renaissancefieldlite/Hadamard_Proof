#!/usr/bin/env python3
"""Exact verifier for Hadamard CSV matrices."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def load_csv_matrix(path: Path) -> np.ndarray:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            rows.append([int(cell.strip()) for cell in row])
    if not rows:
        raise ValueError("CSV is empty")
    matrix = np.array(rows, dtype=np.int64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"matrix must be square, got {matrix.shape}")
    if not np.all(np.isin(matrix, (-1, 1))):
        raise ValueError("matrix contains values outside {-1, 1}")
    return matrix


def verify_hadamard(matrix: np.ndarray) -> tuple[bool, str]:
    n = matrix.shape[0]
    gram = matrix @ matrix.T
    target = np.eye(n, dtype=np.int64) * n
    if np.array_equal(gram, target):
        return True, f"valid Hadamard matrix of order {n}"

    diff = gram - target
    max_abs = int(np.max(np.abs(diff)))
    return False, f"failed orthogonality check (max |HH^T - nI| = {max_abs})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    matrix = load_csv_matrix(args.csv_path)
    ok, message = verify_hadamard(matrix)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

