#!/usr/bin/env python3
"""Solve a bounded PB/ILP repair spec with a monitored square-sum surrogate."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from ortools.sat.python import cp_model

from exact_sds_local_repair import indicator_fourier_profile, load_checkpoint, sds_deltas_for_shifts
from goethals_seidel_search import candidate_metrics, paf, sds_lambda_from_signature


def load_spec(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_model(
    spec: dict,
    K: int,
    force_M_le: int | None = None,
    square_cap: int | None = None,
    translation_fix: bool = False,
):
    model = cp_model.CpModel()
    n = int(spec["n"])
    blocks = int(spec["blocks"])
    focus_shifts = [int(t) for t in spec["focus_shifts"]]
    guard_shifts = [int(t) for t in spec.get("guard_shifts", [])]
    monitored_shifts = list(dict.fromkeys(focus_shifts + guard_shifts))
    c = spec["occupancy"]
    k = [int(v) for v in spec["block_sizes"]]
    guard_caps = {int(k): int(v) for k, v in spec.get("guard_abs_caps", {}).items()}
    pool = [tuple(item) for item in spec["candidate_pool"]]
    free = [[False] * n for _ in range(blocks)]
    for row_idx, g in pool:
        free[row_idx][g] = True

    x: dict[tuple[int, int], cp_model.IntVar] = {}
    for row_idx, g in pool:
        x[(row_idx, g)] = model.NewBoolVar(f"x_{row_idx}_{g}")

    if translation_fix:
        for probe in [(0, 0), *pool]:
            row_idx, g = probe
            if (row_idx, g) in x:
                model.Add(x[(row_idx, g)] == int(c[row_idx][g]))
                break

    shift_exprs = spec["shift_expressions"]
    p: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
    for t in monitored_shifts:
        for item in shift_exprs[str(t)]["quadratic_terms"]:
            row_idx = int(item["row"])
            g = int(item["g"])
            partner = int(item["partner"])
            key = (row_idx, g, partner, t)
            p[key] = model.NewBoolVar(f"p_{row_idx}_{g}_{partner}_{t}")
            model.Add(p[key] <= x[(row_idx, g)])
            model.Add(p[key] <= x[(row_idx, partner)])
            model.Add(p[key] >= x[(row_idx, g)] + x[(row_idx, partner)] - 1)

    for row_idx in range(blocks):
        fixed_total = sum(int(c[row_idx][g]) for g in range(n) if not free[row_idx][g])
        expr = fixed_total + sum(x[(i, g)] for i, g in pool if i == row_idx)
        model.Add(expr == k[row_idx])

    d: dict[int, cp_model.IntVar] = {}
    u: dict[int, cp_model.IntVar] = {}
    sq: dict[int, cp_model.IntVar] = {}
    M = model.NewIntVar(0, 1000, "M")
    for t in monitored_shifts:
        d[t] = model.NewIntVar(-1000, 1000, f"d_{t}")
        u[t] = model.NewIntVar(0, 1000, f"u_{t}")
        if t in focus_shifts:
            max_u = int(spec["current_abs_deltas"][str(t)])
            sq[t] = model.NewIntVar(0, max_u * max_u, f"sq_{t}")

    for t in monitored_shifts:
        shift_expr = shift_exprs[str(t)]
        expr = int(shift_expr["base_minus_lambda"])
        for item in shift_expr["linear_terms"]:
            expr += int(item["coeff"]) * x[(int(item["row"]), int(item["g"]))]
        for item in shift_expr["quadratic_terms"]:
            expr += int(item["coeff"]) * p[(int(item["row"]), int(item["g"]), int(item["partner"]), t)]
        model.Add(d[t] == expr)
        model.Add(d[t] <= u[t])
        model.Add(-d[t] <= u[t])
        if t in focus_shifts:
            model.Add(u[t] <= int(spec["current_abs_deltas"][str(t)]))
            model.Add(u[t] <= M)
            model.AddMultiplicationEquality(sq[t], [u[t], u[t]])
        else:
            model.Add(u[t] <= int(guard_caps[t]))

    if force_M_le is not None:
        model.Add(M <= int(force_M_le))

    square_sum = model.NewIntVar(0, 100000, "square_sum")
    model.Add(square_sum == sum(sq[t] for t in focus_shifts))
    if square_cap is not None:
        model.Add(square_sum <= int(square_cap))

    flip_terms = []
    for row_idx, g in pool:
        if int(c[row_idx][g]) == 0:
            flip_terms.append(x[(row_idx, g)])
        else:
            flip_terms.append(1 - x[(row_idx, g)])
    F = model.NewIntVar(0, len(pool), "F")
    model.Add(F == sum(flip_terms))
    model.Add(F <= int(K))

    return model, x, d, u, sq, M, square_sum, F


def solve_lexicographic_square_sum(
    spec: dict,
    K: int,
    force_M_le: int | None,
    square_cap: int | None,
    translation_fix: bool,
    time_limit: float,
):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8

    model1, x1, d1, u1, sq1, M1, square_sum1, F1 = build_model(
        spec,
        K=K,
        force_M_le=force_M_le,
        square_cap=square_cap,
        translation_fix=translation_fix,
    )
    model1.Minimize(square_sum1)
    status1 = solver.Solve(model1)
    if status1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    best_sq = int(solver.Value(square_sum1))
    best_M = int(solver.Value(M1))

    model2, x2, d2, u2, sq2, M2, square_sum2, F2 = build_model(
        spec,
        K=K,
        force_M_le=best_M,
        square_cap=best_sq,
        translation_fix=translation_fix,
    )
    model2.Minimize(F2)
    solver2 = cp_model.CpSolver()
    solver2.parameters.max_time_in_seconds = time_limit
    solver2.parameters.num_search_workers = 8
    status2 = solver2.Solve(model2)
    if status2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    return {
        "status_square": solver.StatusName(status1),
        "status_flip": solver2.StatusName(status2),
        "solver": solver2,
        "x": x2,
        "d": d2,
        "u": u2,
        "M": M2,
        "square_sum": square_sum2,
        "F": F2,
    }


def reconstruct_state(spec: dict, solution: dict) -> tuple[np.ndarray, list[dict[str, int]]]:
    n = int(spec["n"])
    pool = [tuple(item) for item in spec["candidate_pool"]]
    occupancy = np.array(spec["occupancy"], dtype=np.int8)
    solver = solution["solver"]
    x = solution["x"]

    new_occ = occupancy.copy()
    flips: list[dict[str, int]] = []
    for row_idx, g in pool:
        old = int(occupancy[row_idx][g])
        new = int(solver.Value(x[(row_idx, g)]))
        new_occ[row_idx][g] = new
        if new != old:
            flips.append(
                {
                    "row": int(row_idx),
                    "index": int(g),
                    "from_occupancy": int(old),
                    "to_occupancy": int(new),
                    "from_value": int(-1 if old else 1),
                    "to_value": int(-1 if new else 1),
                }
            )

    state = np.where(new_occ == 1, -1, 1).astype(np.int8)
    return state, flips


def score_state(state: np.ndarray, signature: tuple[int, int, int, int], focus_shifts: list[int]) -> dict:
    seqs = [state[i].copy() for i in range(4)]
    metrics = candidate_metrics(seqs, signature)
    combined = sum((paf(seq) for seq in seqs), start=np.zeros(state.shape[1], dtype=np.int64))
    focus_deltas = sds_deltas_for_shifts(combined, focus_shifts)
    fourier_target, fourier_max_dev, fourier_items = indicator_fourier_profile(state)
    return {
        "metrics": metrics,
        "focus_deltas": focus_deltas,
        "fourier_target": int(fourier_target),
        "fourier_max_dev": int(fourier_max_dev),
        "fourier_items": fourier_items[:12],
    }


def write_candidate(
    output_path: Path,
    spec: dict,
    mode: str,
    K: int,
    solution: dict,
    state: np.ndarray,
    flips: list[dict[str, int]],
    scored: dict,
) -> None:
    signature = tuple(int(v) for v in spec["signature"])
    payload = {
        "family": "goethals_seidel",
        "order": int(spec["order"]),
        "n": int(spec["n"]),
        "signature": list(signature),
        "sds_lambda": int(spec["sds_lambda"]),
        "pb_ilp_source_spec": str(spec["__spec_path__"]),
        "pb_ilp_mode": mode,
        "pb_ilp_best_K": int(K),
        "pb_ilp_flip_count": int(len(flips)),
        "pb_ilp_flips": flips,
        "pb_ilp_monitored_shifts": [int(t) for t in spec["focus_shifts"]],
        "pb_ilp_monitored_abs_defects": {
            str(int(t)): int(solution["solver"].Value(solution["u"][int(t)]))
            for t in spec["focus_shifts"]
        },
        "pb_ilp_guard_shifts": [int(t) for t in spec.get("guard_shifts", [])],
        "pb_ilp_guard_abs_caps": {str(k): int(v) for k, v in spec.get("guard_abs_caps", {}).items()},
        "pb_ilp_guard_abs_defects": {
            str(int(t)): int(solution["solver"].Value(solution["u"][int(t)]))
            for t in spec.get("guard_shifts", [])
        },
        "pb_ilp_monitored_square_sum": int(solution["solver"].Value(solution["square_sum"])),
        "indicator_fourier_target": int(scored["fourier_target"]),
        "indicator_fourier_max_deviation": int(scored["fourier_max_dev"]),
        "indicator_fourier_top_deviations": scored["fourier_items"],
        "best_score": int(scored["metrics"].total_score),
        "best_metrics": asdict(scored["metrics"]),
        "best_state": state.tolist(),
        "best_focus_deltas": scored["focus_deltas"],
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def output_path_for(prefix: Path, K: int, score: int) -> Path:
    return prefix.with_name(f"{prefix.name}_K{K}_{score}_final.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec_path", type=Path)
    parser.add_argument("--source-checkpoint", type=Path)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--K-values", type=str, default="4,6,8")
    parser.add_argument("--target-max", type=int, default=-1)
    parser.add_argument("--square-drop", type=int, default=1)
    parser.add_argument("--translation-fix", action="store_true")
    parser.add_argument("--time-limit", type=float, default=30.0)
    args = parser.parse_args()

    spec = load_spec(args.spec_path)
    spec["__spec_path__"] = str(args.spec_path)
    source_checkpoint = args.source_checkpoint or Path(spec["source_checkpoint"])
    payload = load_checkpoint(source_checkpoint)
    signature = tuple(int(v) for v in payload["signature"])

    focus_shifts = [int(t) for t in spec["focus_shifts"]]
    guard_shifts = [int(t) for t in spec.get("guard_shifts", [])]
    current_abs = [int(spec["current_abs_deltas"][str(t)]) for t in focus_shifts]
    base_sq = sum(value * value for value in current_abs)
    current_max = max(current_abs, default=0)
    target_max = args.target_max if args.target_max >= 0 else max(current_max - 1, 0)
    square_cap = base_sq - int(args.square_drop)
    K_values = [int(part.strip()) for part in args.K_values.split(",") if part.strip()]
    output_prefix = args.output_prefix or args.spec_path.with_name(args.spec_path.stem + "_sqcap")

    print(f"source_checkpoint={source_checkpoint}")
    print(f"focus_shifts={focus_shifts}")
    print(f"guard_shifts={guard_shifts}")
    print(f"current_abs={current_abs}")
    print(f"base_square_sum={base_sq}")
    print(f"target_max={target_max}")
    print(f"square_cap={square_cap}")

    best_record = None
    for K in K_values:
        result = solve_lexicographic_square_sum(
            spec,
            K=K,
            force_M_le=target_max,
            square_cap=square_cap,
            translation_fix=args.translation_fix,
            time_limit=max(1.0, args.time_limit),
        )
        if result is None:
            print(f"K={K} status=INFEASIBLE")
            continue

        state, flips = reconstruct_state(spec, result)
        scored = score_state(state, signature, focus_shifts)
        score = int(scored["metrics"].total_score)
        max_shift = int(scored["metrics"].max_shift_violation)
        fourier = int(scored["fourier_max_dev"])
        square_sum = int(result["solver"].Value(result["square_sum"]))
        M = int(result["solver"].Value(result["M"]))
        F = int(result["solver"].Value(result["F"]))
        out_path = output_path_for(output_prefix, K, score)
        write_candidate(out_path, spec, output_prefix.name, K, result, state, flips, scored)
        print(
            f"K={K} square_status={result['status_square']} flip_status={result['status_flip']} "
            f"M={M} F={F} sq={square_sum} score={score} max_shift={max_shift} "
            f"fourier={fourier} written={out_path}"
        )
        if best_record is None or (score, max_shift, fourier, square_sum, F) < (
            best_record["score"],
            best_record["max_shift"],
            best_record["fourier"],
            best_record["square_sum"],
            best_record["F"],
        ):
            best_record = {
                "path": out_path,
                "score": score,
                "max_shift": max_shift,
                "fourier": fourier,
                "square_sum": square_sum,
                "F": F,
            }

    if best_record is None:
        raise SystemExit("no feasible K found under the square-sum rung")

    print(f"best_path={best_record['path']}")
    print(
        f"best_score={best_record['score']} best_max_shift={best_record['max_shift']} "
        f"best_fourier={best_record['fourier']} best_sq={best_record['square_sum']} best_F={best_record['F']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
