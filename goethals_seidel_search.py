#!/usr/bin/env python3
"""Goethals-Seidel search lane for Hadamard targets."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import asdict, dataclass
from itertools import combinations_with_replacement
from pathlib import Path

import numpy as np

ORDER_TO_N = {
    428: 107,
    668: 167,
}


def paf(seq: np.ndarray) -> np.ndarray:
    fft_vals = np.fft.fft(seq.astype(np.float64))
    corr = np.fft.ifft(np.abs(fft_vals) ** 2).real
    return np.rint(corr).astype(np.int64)


def combined_paf(seqs: list[np.ndarray]) -> np.ndarray:
    return sum((paf(seq) for seq in seqs), start=np.zeros(len(seqs[0]), dtype=np.int64))


def periodic_score_from_combined(combined: np.ndarray) -> int:
    return int(np.sum(combined[1:] ** 2))


def row_sums_for_seqs(seqs: list[np.ndarray]) -> list[int]:
    return [int(seq.sum()) for seq in seqs]


def summarize_shift_violations(combined: np.ndarray, limit: int = 8) -> list[dict[str, int]]:
    violations = [
        {"shift": int(shift), "value": int(combined[shift]), "abs_value": int(abs(combined[shift]))}
        for shift in range(1, len(combined))
        if combined[shift] != 0
    ]
    violations.sort(key=lambda item: (-item["abs_value"], item["shift"]))
    return violations[:limit]


def enumerate_odd_signatures(n: int) -> list[tuple[int, int, int, int]]:
    total = 4 * n
    max_odd = min(n, int(math.isqrt(total)))
    odds = [value for value in range(1, max_odd + 1, 2)]
    signatures: list[tuple[int, int, int, int]] = []
    for combo in combinations_with_replacement(odds, 4):
        if sum(value * value for value in combo) == total:
            signatures.append(tuple(sorted(combo, reverse=True)))
    return sorted(set(signatures), reverse=True)


def parse_signature(text: str, n: int) -> tuple[int, int, int, int]:
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if len(parts) != 4:
        raise ValueError("signature must have exactly four comma-separated values")
    signature = tuple(sorted((int(part) for part in parts), reverse=True))
    if any(value <= 0 or value > n or value % 2 != (n % 2) for value in signature):
        raise ValueError("signature entries must be positive, <= n, and match the odd parity of n")
    if sum(value * value for value in signature) != 4 * n:
        raise ValueError("signature does not satisfy s1^2 + s2^2 + s3^2 + s4^2 = 4n")
    return signature


def signature_to_positive_counts(signature: tuple[int, int, int, int], n: int) -> list[int]:
    return [int((n + row_sum) // 2) for row_sum in signature]


def signature_to_negative_counts(signature: tuple[int, int, int, int], n: int) -> list[int]:
    return [int((n - row_sum) // 2) for row_sum in signature]


def sds_lambda_from_signature(signature: tuple[int, int, int, int], n: int) -> int:
    negative_counts = signature_to_negative_counts(signature, n)
    return int((sum(count * count for count in negative_counts) - sum(negative_counts)) // (n - 1))


def random_sequence_with_row_sum(rng: np.random.Generator, n: int, row_sum: int) -> np.ndarray:
    positives = int((n + row_sum) // 2)
    seq = np.full(n, -1, dtype=np.int8)
    indices = rng.choice(n, size=positives, replace=False)
    seq[indices] = 1
    return seq


def initialize_sequences(
    rng: np.random.Generator,
    n: int,
    signature: tuple[int, int, int, int],
) -> np.ndarray:
    seqs = np.stack([random_sequence_with_row_sum(rng, n, row_sum) for row_sum in signature], axis=0)
    return seqs.astype(np.int8)


def candidate_metrics(seqs: list[np.ndarray], signature: tuple[int, int, int, int]) -> "CandidateMetrics":
    combined = combined_paf(seqs)
    periodic = periodic_score_from_combined(combined)
    row_sums = row_sums_for_seqs(seqs)
    top_shift_violations = summarize_shift_violations(combined)
    max_shift_violation = top_shift_violations[0]["abs_value"] if top_shift_violations else 0
    return CandidateMetrics(
        total_score=periodic,
        periodic_score=periodic,
        row_sums=row_sums,
        target_signature=list(signature),
        max_shift_violation=max_shift_violation,
        top_shift_violations=top_shift_violations,
    )


def circulant(first_row: np.ndarray) -> np.ndarray:
    n = len(first_row)
    return np.array([np.roll(first_row, i) for i in range(n)], dtype=np.int8)


def reversal_matrix(n: int) -> np.ndarray:
    return np.fliplr(np.eye(n, dtype=np.int8))


def goethals_seidel_matrix(seqs: list[np.ndarray]) -> np.ndarray:
    a, b, c, d = [circulant(seq) for seq in seqs]
    r = reversal_matrix(len(seqs[0]))
    br = b @ r
    cr = c @ r
    dr = d @ r
    dtr = d.T @ r
    ctr = c.T @ r
    btr = b.T @ r
    top = np.hstack([a, br, cr, dr])
    row2 = np.hstack([-br, a, dtr, -ctr])
    row3 = np.hstack([-cr, -dtr, a, btr])
    row4 = np.hstack([-dr, ctr, -btr, a])
    return np.vstack([top, row2, row3, row4]).astype(np.int8)


def save_csv_matrix(path: Path, matrix: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(matrix.tolist())


def state_signature(state: np.ndarray) -> bytes:
    return state.tobytes()


def sample_swap_count(rng: np.random.Generator, max_swaps: int) -> int:
    if max_swaps <= 1:
        return 1
    counts = np.arange(1, max_swaps + 1, dtype=np.int64)
    weights = counts[::-1].astype(np.float64)
    weights /= weights.sum()
    return int(rng.choice(counts, p=weights))


def swap_preserving_row_sum(seq: np.ndarray, rng: np.random.Generator) -> bool:
    pos = np.flatnonzero(seq == 1)
    neg = np.flatnonzero(seq == -1)
    if pos.size == 0 or neg.size == 0:
        return False
    i = int(rng.choice(pos))
    j = int(rng.choice(neg))
    seq[i] = -1
    seq[j] = 1
    return True


def mutate_state(base_state: np.ndarray, rng: np.random.Generator, max_swaps: int) -> np.ndarray:
    trial = base_state.copy()
    swap_count = sample_swap_count(rng, max_swaps)
    for _ in range(swap_count):
        row = int(rng.integers(trial.shape[0]))
        if not swap_preserving_row_sum(trial[row], rng):
            break
    return trial


@dataclass
class CandidateMetrics:
    total_score: int
    periodic_score: int
    row_sums: list[int]
    target_signature: list[int]
    max_shift_violation: int
    top_shift_violations: list[dict[str, int]]


@dataclass
class EliteEntry:
    score: int
    step: int
    state: np.ndarray
    metrics: CandidateMetrics


def push_elite(
    elites: list[EliteEntry],
    state: np.ndarray,
    metrics: CandidateMetrics,
    step: int,
    elite_size: int,
) -> None:
    if elite_size <= 0:
        return

    signature = state_signature(state)
    for existing in elites:
        if state_signature(existing.state) == signature:
            return

    elites.append(
        EliteEntry(
            score=metrics.total_score,
            step=step,
            state=state.copy(),
            metrics=metrics,
        )
    )
    elites.sort(key=lambda entry: (entry.score, entry.metrics.max_shift_violation, entry.step))
    del elites[elite_size:]


def elite_score_histogram(elites: list[EliteEntry]) -> list[int]:
    return [entry.score for entry in elites]


def select_restart_base(
    rng: np.random.Generator,
    elites: list[EliteEntry],
    best_state: np.ndarray,
) -> np.ndarray:
    if not elites:
        return best_state

    top_k = min(len(elites), 4)
    weights = np.arange(top_k, 0, -1, dtype=np.float64)
    weights /= weights.sum()
    choice = int(rng.choice(np.arange(top_k), p=weights))
    return elites[choice].state


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
    max_swaps: int
    elite_size: int
    restart_every: int
    restart_perturb: int
    signature: tuple[int, int, int, int]
    signature_label: str
    focus_shifts: list[int]


def checkpoint(run_dir: Path, label: str, payload: dict) -> None:
    path = run_dir / label
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def checkpoint_payload(
    *,
    cfg: SearchConfig,
    step: int,
    start_time: float,
    current_score: int,
    current_metrics: CandidateMetrics,
    best_score: int,
    best_metrics: CandidateMetrics,
    best_state: np.ndarray,
    best_step: int,
    accepted_moves: int,
    uphill_accepts: int,
    rejected_moves: int,
    temperature: float,
    elites: list[EliteEntry],
    restart_count: int,
    last_restart_step: int,
    stalled_steps: int,
) -> dict:
    total_decisions = accepted_moves + rejected_moves
    acceptance_rate = accepted_moves / total_decisions if total_decisions else 0.0
    uphill_acceptance_rate = uphill_accepts / accepted_moves if accepted_moves else 0.0
    return {
        "family": "goethals_seidel",
        "order": cfg.order,
        "n": cfg.n,
        "steps": cfg.steps,
        "step": step,
        "elapsed_sec": round(time.time() - start_time, 3),
        "batch": cfg.batch,
        "seed": cfg.seed,
        "temperature": round(float(temperature), 8),
        "accepted_moves": accepted_moves,
        "uphill_accepts": uphill_accepts,
        "rejected_moves": rejected_moves,
        "acceptance_rate": round(acceptance_rate, 6),
        "uphill_acceptance_rate": round(uphill_acceptance_rate, 6),
        "restart_count": restart_count,
        "last_restart_step": last_restart_step,
        "stalled_steps": stalled_steps,
        "signature": list(cfg.signature),
        "signature_label": cfg.signature_label,
        "focus_shifts": cfg.focus_shifts,
        "elite_scores": elite_score_histogram(elites),
        "current_score": int(current_score),
        "current_metrics": asdict(current_metrics),
        "best_score": int(best_score),
        "best_step": best_step,
        "best_metrics": asdict(best_metrics),
        "best_state": best_state.tolist(),
    }


def evaluate_candidate(state: np.ndarray, signature: tuple[int, int, int, int]) -> tuple[list[np.ndarray], CandidateMetrics]:
    seqs = [state[i].copy() for i in range(4)]
    metrics = candidate_metrics(seqs, signature)
    return seqs, metrics


def load_state_from_checkpoint(
    path: Path,
    *,
    order: int,
    n: int,
    signature: tuple[int, int, int, int],
) -> np.ndarray:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    payload_order = int(payload["order"])
    payload_n = int(payload["n"])
    payload_signature = tuple(int(value) for value in payload["signature"])
    if payload_order != order or payload_n != n:
        raise ValueError("resume checkpoint order/n does not match requested search")
    if payload_signature != signature:
        raise ValueError("resume checkpoint signature does not match requested signature")

    state = np.array(payload["best_state"], dtype=np.int8)
    if state.shape != (4, n):
        raise ValueError("resume checkpoint state shape is invalid")
    return state


def normalize_focus_shifts(focus_shifts: list[int], n: int) -> list[int]:
    normalized: set[int] = set()
    for shift in focus_shifts:
        shift %= n
        if shift == 0:
            continue
        normalized.add(min(shift, n - shift))
    return sorted(normalized)


def focus_shift_penalty(combined: np.ndarray, focus_shifts: list[int]) -> int:
    if not focus_shifts:
        return 0
    return int(sum(int(combined[shift]) ** 2 for shift in focus_shifts))


def best_improving_single_swap(
    state: np.ndarray,
    signature: tuple[int, int, int, int],
    focus_shifts: list[int],
) -> tuple[np.ndarray, CandidateMetrics, dict[str, int]] | None:
    n = state.shape[1]
    base_pafs = [paf(state[i]) for i in range(4)]
    base_combined = sum(base_pafs, start=np.zeros(n, dtype=np.int64))
    base_score = periodic_score_from_combined(base_combined)
    best_record = None

    for row_idx in range(4):
        row = state[row_idx]
        pos = np.flatnonzero(row == 1)
        neg = np.flatnonzero(row == -1)
        for pos_idx in pos:
            for neg_idx in neg:
                trial_row = row.copy()
                trial_row[pos_idx] = -1
                trial_row[neg_idx] = 1
                trial_row_paf = paf(trial_row)
                combined = base_combined - base_pafs[row_idx] + trial_row_paf
                trial_score = periodic_score_from_combined(combined)
                if trial_score >= base_score:
                    continue

                focus_penalty = focus_shift_penalty(combined, focus_shifts)
                max_shift = int(np.max(np.abs(combined[1:])))
                record = (
                    int(trial_score),
                    int(focus_penalty),
                    int(max_shift),
                    int(row_idx),
                    int(pos_idx),
                    int(neg_idx),
                    trial_row,
                )
                if best_record is None or record[:6] < best_record[:6]:
                    best_record = record

    if best_record is None:
        return None

    _, _, _, row_idx, pos_idx, neg_idx, trial_row = best_record
    new_state = state.copy()
    new_state[row_idx] = trial_row
    _, metrics = evaluate_candidate(new_state, signature)
    move = {
        "row": int(row_idx),
        "plus_to_minus": int(pos_idx),
        "minus_to_plus": int(neg_idx),
        "new_score": int(metrics.total_score),
        "new_max_shift": int(metrics.max_shift_violation),
    }
    return new_state, metrics, move


def greedy_polish(
    state: np.ndarray,
    signature: tuple[int, int, int, int],
    rounds: int,
    focus_shifts: list[int],
) -> tuple[np.ndarray, CandidateMetrics, list[dict[str, int]]]:
    current_state = state.copy()
    _, current_metrics = evaluate_candidate(current_state, signature)
    history: list[dict[str, int]] = []

    for round_idx in range(1, rounds + 1):
        result = best_improving_single_swap(current_state, signature, focus_shifts)
        if result is None:
            break
        current_state, current_metrics, move = result
        move["round"] = round_idx
        history.append(move)

    return current_state, current_metrics, history


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", type=int, choices=sorted(ORDER_TO_N), required=True)
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--seed", type=int, default=67)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--temp-start", type=float, default=1.5)
    parser.add_argument("--temp-end", type=float, default=0.02)
    parser.add_argument("--max-swaps", type=int, default=3)
    parser.add_argument("--elite-size", type=int, default=8)
    parser.add_argument("--restart-every", type=int, default=250)
    parser.add_argument("--restart-perturb", type=int, default=5)
    parser.add_argument("--target-signature", type=str, default="")
    parser.add_argument("--signature-index", type=int, default=0)
    parser.add_argument("--resume-json", type=Path)
    parser.add_argument("--greedy-polish-rounds", type=int, default=0)
    parser.add_argument("--focus-shifts", type=str, default="")
    parser.add_argument("--list-signatures", action="store_true")
    args = parser.parse_args()

    n = ORDER_TO_N[args.order]
    signatures = enumerate_odd_signatures(n)

    if args.list_signatures:
        print(f"order={args.order} n={n}")
        for idx, signature in enumerate(signatures):
            counts = signature_to_positive_counts(signature, n)
            print(f"[{idx}] signature={signature} positive_counts={counts}")
        return 0

    if args.target_signature:
        signature = parse_signature(args.target_signature, n)
    else:
        if args.signature_index < 0 or args.signature_index >= len(signatures):
            raise SystemExit(f"signature-index must be between 0 and {len(signatures) - 1}")
        signature = signatures[args.signature_index]

    signature_label = "-".join(str(value) for value in signature)
    focus_shifts = normalize_focus_shifts(
        [int(part.strip()) for part in args.focus_shifts.split(",") if part.strip()],
        n,
    )
    cfg = SearchConfig(
        order=args.order,
        n=n,
        steps=args.steps,
        batch=args.batch,
        seed=args.seed,
        checkpoint_every=args.checkpoint_every,
        temp_start=args.temp_start,
        temp_end=args.temp_end,
        max_swaps=max(1, args.max_swaps),
        elite_size=max(1, args.elite_size),
        restart_every=max(0, args.restart_every),
        restart_perturb=max(1, args.restart_perturb),
        signature=signature,
        signature_label=signature_label,
        focus_shifts=focus_shifts,
    )

    run_dir = Path("runs")
    run_dir.mkdir(exist_ok=True)

    rng = np.random.default_rng(cfg.seed)
    if args.resume_json:
        state = load_state_from_checkpoint(
            args.resume_json,
            order=cfg.order,
            n=cfg.n,
            signature=cfg.signature,
        )
    else:
        state = initialize_sequences(rng, cfg.n, cfg.signature)

    if args.greedy_polish_rounds > 0:
        state, _, polish_history = greedy_polish(
            state,
            cfg.signature,
            rounds=max(0, args.greedy_polish_rounds),
            focus_shifts=cfg.focus_shifts,
        )
        if polish_history:
            print("greedy polish:")
            for move in polish_history:
                print(
                    f"  [round {move['round']}] row={move['row']} "
                    f"+->{move['plus_to_minus']} --> - | "
                    f"-->+ {move['minus_to_plus']} | "
                    f"score={move['new_score']} max_shift={move['new_max_shift']}"
                )

    current_seqs, current_metrics = evaluate_candidate(state, cfg.signature)
    current_score = current_metrics.total_score
    best_state = state.copy()
    best_score = current_score
    best_seqs = [seq.copy() for seq in current_seqs]
    best_metrics = current_metrics
    best_step = 0
    elites: list[EliteEntry] = []
    push_elite(elites, best_state, best_metrics, best_step, cfg.elite_size)
    accepted_moves = 0
    uphill_accepts = 0
    rejected_moves = 0
    restart_count = 0
    last_restart_step = 0
    stalled_steps = 0
    start = time.time()

    print(
        f"Hadamard GS search | order={cfg.order} | n={cfg.n} | "
        f"signature={cfg.signature}"
    )
    if cfg.focus_shifts:
        print(f"focus_shifts={cfg.focus_shifts}")
    print(f"initial score={current_score}")

    for step in range(1, cfg.steps + 1):
        progress = (step - 1) / max(1, cfg.steps - 1)
        temperature = cfg.temp_start * ((cfg.temp_end / cfg.temp_start) ** progress)

        if cfg.restart_every > 0 and step > 1 and step % cfg.restart_every == 0:
            restart_base = select_restart_base(rng, elites, best_state)
            state = mutate_state(restart_base, rng, cfg.restart_perturb)
            current_seqs, current_metrics = evaluate_candidate(state, cfg.signature)
            current_score = current_metrics.total_score
            restart_count += 1
            last_restart_step = step
            print(
                f"[step {step}] restart current={current_score} "
                f"best={best_score} elite_best={elites[0].score}"
            )

        best_trial_state = None
        best_trial_score = None
        best_trial_seqs = None
        best_trial_metrics = None

        for _ in range(cfg.batch):
            trial = mutate_state(state, rng, cfg.max_swaps)
            trial_seqs, trial_metrics = evaluate_candidate(trial, cfg.signature)
            trial_score = trial_metrics.total_score
            if best_trial_score is None or trial_score < best_trial_score:
                best_trial_score = trial_score
                best_trial_state = trial
                best_trial_seqs = trial_seqs
                best_trial_metrics = trial_metrics

        accept = False
        if best_trial_score is not None:
            if best_trial_score <= current_score:
                accept = True
            else:
                delta = best_trial_score - current_score
                accept = rng.random() < math.exp(-delta / max(temperature, 1e-9))

        if accept and best_trial_state is not None:
            if best_trial_score is not None and best_trial_score > current_score:
                uphill_accepts += 1
            accepted_moves += 1
            state = best_trial_state
            current_score = int(best_trial_score)
            current_seqs = best_trial_seqs
            current_metrics = best_trial_metrics
        else:
            rejected_moves += 1

        if current_score < best_score:
            best_score = current_score
            best_state = state.copy()
            best_seqs = [seq.copy() for seq in current_seqs]
            best_metrics = current_metrics
            best_step = step
            stalled_steps = 0
            push_elite(elites, best_state, best_metrics, best_step, cfg.elite_size)
            print(f"[step {step}] new best score={best_score}")

            if best_score == 0:
                matrix = goethals_seidel_matrix(best_seqs)
                matrix_path = run_dir / f"order_{cfg.order}_gs_{cfg.signature_label}_best_matrix.csv"
                save_csv_matrix(matrix_path, matrix)
                print(f"score 0 candidate written to {matrix_path}")
        else:
            stalled_steps += 1
            if best_trial_state is not None and best_trial_metrics is not None:
                push_elite(elites, best_trial_state, best_trial_metrics, step, cfg.elite_size)

        if step % cfg.checkpoint_every == 0 or step == 1:
            payload = checkpoint_payload(
                cfg=cfg,
                step=step,
                start_time=start,
                current_score=current_score,
                current_metrics=current_metrics,
                best_score=best_score,
                best_metrics=best_metrics,
                best_state=best_state,
                best_step=best_step,
                accepted_moves=accepted_moves,
                uphill_accepts=uphill_accepts,
                rejected_moves=rejected_moves,
                temperature=temperature,
                elites=elites,
                restart_count=restart_count,
                last_restart_step=last_restart_step,
                stalled_steps=stalled_steps,
            )
            checkpoint(
                run_dir,
                f"order_{cfg.order}_gs_{cfg.signature_label}_latest.json",
                payload,
            )
            print(
                f"[step {step}] current={current_score} best={best_score} "
                f"max_shift={current_metrics.max_shift_violation} "
                f"elite_best={elites[0].score} restarts={restart_count} "
                f"elapsed={time.time() - start:.1f}s"
            )

    payload = checkpoint_payload(
        cfg=cfg,
        step=cfg.steps,
        start_time=start,
        current_score=current_score,
        current_metrics=current_metrics,
        best_score=best_score,
        best_metrics=best_metrics,
        best_state=best_state,
        best_step=best_step,
        accepted_moves=accepted_moves,
        uphill_accepts=uphill_accepts,
        rejected_moves=rejected_moves,
        temperature=cfg.temp_end,
        elites=elites,
        restart_count=restart_count,
        last_restart_step=last_restart_step,
        stalled_steps=stalled_steps,
    )
    checkpoint(run_dir, f"order_{cfg.order}_gs_{cfg.signature_label}_final.json", payload)
    print(f"done | best_score={best_score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
