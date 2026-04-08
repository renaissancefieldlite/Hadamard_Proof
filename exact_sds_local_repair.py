#!/usr/bin/env python3
"""Bounded local repair over a focused SDS defect surface."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from goethals_seidel_search import (
    CandidateMetrics,
    candidate_metrics,
    normalize_focus_shifts,
    paf,
    sds_lambda_from_signature,
)


@dataclass
class RepairNode:
    state: np.ndarray
    combined: np.ndarray
    pafs: list[np.ndarray]
    metrics: CandidateMetrics
    history: list[dict[str, object]]


@dataclass
class RepairSearchResult:
    best_focus: RepairNode
    best_score: RepairNode
    best_exact: RepairNode | None


def load_checkpoint(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_node(state: np.ndarray, signature: tuple[int, int, int, int]) -> RepairNode:
    seqs = [state[i].copy() for i in range(4)]
    pafs = [paf(seq) for seq in seqs]
    combined = sum(pafs, start=np.zeros(state.shape[1], dtype=np.int64))
    metrics = candidate_metrics(seqs, signature)
    return RepairNode(
        state=state.copy(),
        combined=combined,
        pafs=pafs,
        metrics=metrics,
        history=[],
    )


def sds_deltas_for_shifts(combined: np.ndarray, shifts: list[int]) -> list[int]:
    return [int(combined[shift] // 4) for shift in shifts]


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


def top_unique_sds_shifts(combined: np.ndarray, limit: int) -> list[int]:
    if limit <= 0:
        return []
    seen: set[int] = set()
    ranked: list[tuple[int, int]] = []
    n = len(combined)
    for shift in range(1, n):
        rep = min(shift, n - shift)
        if rep in seen:
            continue
        seen.add(rep)
        value = int(combined[rep])
        if value == 0:
            continue
        ranked.append((rep, abs(value)))
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return [shift for shift, _ in ranked[:limit]]


def objective_for_node(node: RepairNode, focus_shifts: list[int]) -> tuple[int, int, int, int]:
    focus_values = sds_deltas_for_shifts(node.combined, focus_shifts)
    focus_max = max((abs(value) for value in focus_values), default=0)
    focus_penalty = sum(value * value for value in focus_values)
    return (
        int(focus_max),
        int(focus_penalty),
        int(node.metrics.total_score),
        int(node.metrics.max_shift_violation),
    )


def focused_endpoint_profiles(
    block: np.ndarray,
    focus_shifts: list[int],
    focus_values: list[int],
) -> tuple[list[tuple[int, int, list[int]]], list[tuple[int, int, list[int]]]]:
    n = len(block)
    adds: list[tuple[int, int, list[int]]] = []
    removes: list[tuple[int, int, list[int]]] = []

    for idx in range(n):
        profile = [int(block[(idx - shift) % n] + block[(idx + shift) % n]) for shift in focus_shifts]
        utility = 0
        for value, count in zip(focus_values, profile, strict=True):
            if block[idx]:
                effect = -count
            else:
                effect = count
            utility += -value * effect

        record = (int(utility), int(idx), profile)
        if block[idx]:
            removes.append(record)
        else:
            adds.append(record)

    adds.sort(key=lambda item: (-item[0], item[1]))
    removes.sort(key=lambda item: (-item[0], item[1]))
    return adds, removes


def candidate_single_swaps(
    node: RepairNode,
    signature: tuple[int, int, int, int],
    focus_shifts: list[int],
    endpoint_limit: int,
    swap_pool_limit: int,
    max_score: int | None,
) -> list[RepairNode]:
    focus_values = sds_deltas_for_shifts(node.combined, focus_shifts)
    n = node.state.shape[1]
    candidates: list[tuple[tuple[int, int, int, int], RepairNode]] = []

    for row_idx in range(4):
        row = node.state[row_idx]
        block = (row == -1).astype(np.int8)
        adds, removes = focused_endpoint_profiles(block, focus_shifts, focus_values)
        add_pool = adds[:endpoint_limit]
        remove_pool = removes[:endpoint_limit]

        for _, add_idx, _ in add_pool:
            for _, remove_idx, _ in remove_pool:
                trial_row = row.copy()
                trial_row[add_idx] = -1
                trial_row[remove_idx] = 1
                trial_paf = paf(trial_row)
                trial_combined = node.combined - node.pafs[row_idx] + trial_paf
                trial_state = node.state.copy()
                trial_state[row_idx] = trial_row
                seqs = [trial_state[i].copy() for i in range(4)]
                trial_metrics = candidate_metrics(seqs, signature)
                trial_node = RepairNode(
                    state=trial_state,
                    combined=trial_combined,
                    pafs=[trial_paf if i == row_idx else node.pafs[i] for i in range(4)],
                    metrics=trial_metrics,
                    history=node.history
                    + [
                        {
                            "row": int(row_idx),
                            "plus_to_minus": int(add_idx),
                            "minus_to_plus": int(remove_idx),
                            "score": int(trial_metrics.total_score),
                            "max_shift": int(trial_metrics.max_shift_violation),
                            "focus_deltas": sds_deltas_for_shifts(trial_combined, focus_shifts),
                        }
                    ],
                )
                if max_score is not None and trial_metrics.total_score > max_score:
                    continue
                objective = objective_for_node(trial_node, focus_shifts)
                candidates.append((objective, trial_node))

    candidates.sort(key=lambda item: item[0])
    deduped: list[RepairNode] = []
    seen: set[bytes] = set()
    for _, node_candidate in candidates:
        key = node_candidate.state.tobytes()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(node_candidate)
        if len(deduped) >= swap_pool_limit:
            break
    return deduped


def beam_search_repair(
    root: RepairNode,
    signature: tuple[int, int, int, int],
    focus_shifts: list[int],
    depth: int,
    beam_width: int,
    endpoint_limit: int,
    swap_pool_limit: int,
    max_score: int | None,
    require_focus_zero: bool,
) -> RepairSearchResult:
    beam = [root]
    best = root
    best_score = root
    best_exact = root if objective_for_node(root, focus_shifts)[:2] == (0, 0) else None
    seen: set[bytes] = {root.state.tobytes()}

    for _ in range(depth):
        expanded: list[RepairNode] = []
        for node in beam:
            for child in candidate_single_swaps(
                node,
                signature,
                focus_shifts,
                endpoint_limit=endpoint_limit,
                swap_pool_limit=swap_pool_limit,
                max_score=max_score,
            ):
                key = child.state.tobytes()
                if key in seen:
                    continue
                seen.add(key)
                expanded.append(child)
                if (
                    child.metrics.total_score,
                    objective_for_node(child, focus_shifts),
                    len(child.history),
                ) < (
                    best_score.metrics.total_score,
                    objective_for_node(best_score, focus_shifts),
                    len(best_score.history),
                ):
                    best_score = child

        if not expanded:
            break

        expanded.sort(key=lambda node: objective_for_node(node, focus_shifts))
        beam = expanded[:beam_width]
        for candidate in beam:
            if objective_for_node(candidate, focus_shifts)[:2] == (0, 0):
                if best_exact is None or (
                    candidate.metrics.total_score,
                    candidate.metrics.max_shift_violation,
                    len(candidate.history),
                ) < (
                    best_exact.metrics.total_score,
                    best_exact.metrics.max_shift_violation,
                    len(best_exact.history),
                ):
                    best_exact = candidate
        if objective_for_node(beam[0], focus_shifts) < objective_for_node(best, focus_shifts):
            best = beam[0]

    chosen = best
    if require_focus_zero and best_exact is not None:
        chosen = best_exact
    elif best_exact is not None and objective_for_node(best_exact, focus_shifts) < objective_for_node(best, focus_shifts):
        chosen = best_exact

    return RepairSearchResult(best_focus=chosen, best_score=best_score, best_exact=best_exact)


def output_path_for(input_path: Path, suffix: str) -> Path:
    stem = input_path.stem
    if stem.endswith("_final"):
        stem = stem[: -len("_final")]
    return input_path.with_name(f"{stem}_{suffix}_final.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_path", type=Path)
    parser.add_argument("--focus-shifts", type=str, default="")
    parser.add_argument("--focus-top-unique", type=int, default=0)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--beam-width", type=int, default=48)
    parser.add_argument("--endpoint-limit", type=int, default=12)
    parser.add_argument("--swap-pool-limit", type=int, default=96)
    parser.add_argument("--score-slack", type=int, default=-1)
    parser.add_argument("--require-focus-zero", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = load_checkpoint(args.checkpoint_path)
    order = int(payload["order"])
    n = int(payload["n"])
    signature = tuple(int(value) for value in payload["signature"])
    state = np.array(payload["best_state"], dtype=np.int8)
    root = build_node(state, signature)
    explicit_focus = normalize_focus_shifts(
        [int(part.strip()) for part in args.focus_shifts.split(",") if part.strip()],
        n,
    )
    auto_focus = top_unique_sds_shifts(root.combined, args.focus_top_unique)
    focus_shifts = sorted(set(explicit_focus + auto_focus))
    if not focus_shifts:
        raise SystemExit("provide --focus-shifts or --focus-top-unique")

    max_score = None
    if args.score_slack >= 0:
        max_score = int(root.metrics.total_score + args.score_slack)
    result = beam_search_repair(
        root,
        signature,
        focus_shifts,
        depth=max(1, args.depth),
        beam_width=max(1, args.beam_width),
        endpoint_limit=max(1, args.endpoint_limit),
        swap_pool_limit=max(1, args.swap_pool_limit),
        max_score=max_score,
        require_focus_zero=args.require_focus_zero,
    )
    best = result.best_focus
    best_score_node = result.best_score

    sds_lambda = sds_lambda_from_signature(signature, n)
    fourier_target, fourier_max_dev, fourier_items = indicator_fourier_profile(best.state)
    best_score_fourier_target, best_score_fourier_max_dev, best_score_fourier_items = indicator_fourier_profile(best_score_node.state)
    output_path = args.output or output_path_for(args.checkpoint_path, f"repair_{best.metrics.total_score}")
    output_payload = {
        "family": "goethals_seidel",
        "order": order,
        "n": n,
        "signature": list(signature),
        "focus_shifts": focus_shifts,
        "sds_lambda": int(sds_lambda),
        "repair_depth": int(args.depth),
        "repair_beam_width": int(args.beam_width),
        "repair_endpoint_limit": int(args.endpoint_limit),
        "repair_swap_pool_limit": int(args.swap_pool_limit),
        "repair_score_slack": int(args.score_slack),
        "repair_require_focus_zero": bool(args.require_focus_zero),
        "repair_source": str(args.checkpoint_path),
        "repair_history": best.history,
        "best_focus_deltas": sds_deltas_for_shifts(best.combined, focus_shifts),
        "indicator_fourier_target": int(fourier_target),
        "indicator_fourier_max_deviation": int(fourier_max_dev),
        "indicator_fourier_top_deviations": fourier_items[:12],
        "best_score": int(best.metrics.total_score),
        "best_metrics": asdict(best.metrics),
        "best_state": best.state.tolist(),
        "best_score_seen": int(best_score_node.metrics.total_score),
        "best_score_seen_history": best_score_node.history,
        "best_score_seen_focus_deltas": sds_deltas_for_shifts(best_score_node.combined, focus_shifts),
        "best_score_seen_indicator_fourier_target": int(best_score_fourier_target),
        "best_score_seen_indicator_fourier_max_deviation": int(best_score_fourier_max_dev),
        "best_score_seen_indicator_fourier_top_deviations": best_score_fourier_items[:12],
        "best_score_seen_metrics": asdict(best_score_node.metrics),
        "best_score_seen_state": best_score_node.state.tolist(),
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output_payload, handle, indent=2)

    print(f"focus_shifts={focus_shifts}")
    print(f"sds_lambda={sds_lambda}")
    print(f"indicator_fourier_target={fourier_target}")
    print(f"indicator_fourier_max_deviation={fourier_max_dev}")
    print(f"max_score={max_score}")
    print(f"root_objective={objective_for_node(root, focus_shifts)}")
    print(f"best_objective={objective_for_node(best, focus_shifts)}")
    print(f"best_focus_deltas={sds_deltas_for_shifts(best.combined, focus_shifts)}")
    print(f"best_score={best.metrics.total_score}")
    print(f"best_max_shift={best.metrics.max_shift_violation}")
    print(f"best_score_seen={best_score_node.metrics.total_score}")
    print(f"best_score_seen_focus_deltas={sds_deltas_for_shifts(best_score_node.combined, focus_shifts)}")
    print(f"history_len={len(best.history)}")
    for idx, move in enumerate(best.history, start=1):
        print(
            f"  [move {idx}] row={move['row']} +->{move['plus_to_minus']} "
            f"--> - | -->+ {move['minus_to_plus']} | "
            f"score={move['score']} focus={move['focus_deltas']}"
        )
    print(f"written={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
