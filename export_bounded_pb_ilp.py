#!/usr/bin/env python3
"""Export a bounded PB/ILP repair instance from a GS/SDS basin."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from exact_sds_local_repair import (
    build_node,
    focused_endpoint_profiles,
    load_checkpoint,
    sds_deltas_for_shifts,
    top_unique_sds_shifts,
)
from goethals_seidel_search import normalize_focus_shifts, sds_lambda_from_signature, signature_to_negative_counts


def build_candidate_pool(
    state: np.ndarray,
    focus_shifts: list[int],
    focus_deltas: list[int],
    endpoint_limit: int,
) -> list[tuple[int, int]]:
    pool: set[tuple[int, int]] = set()
    for row_idx in range(4):
        block = (state[row_idx] == -1).astype(np.int8)
        adds, removes = focused_endpoint_profiles(block, focus_shifts, focus_deltas)
        for _, idx, _ in adds[:endpoint_limit]:
            pool.add((row_idx, int(idx)))
        for _, idx, _ in removes[:endpoint_limit]:
            pool.add((row_idx, int(idx)))
    return sorted(pool)


def dedupe_preserve_order(values: list[int]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def var_x(row_idx: int, g: int) -> str:
    return f"x_r{row_idx}_g{g}"


def var_p(row_idx: int, g: int, partner: int, shift: int) -> str:
    return f"p_r{row_idx}_g{g}_h{partner}_t{shift}"


def var_d(shift: int) -> str:
    return f"d_{shift}"


def var_u(shift: int) -> str:
    return f"u_{shift}"


def compress_shift_expressions(
    occupancy: list[list[int]],
    free: set[tuple[int, int]],
    focus_shifts: list[int],
    n: int,
    sds_lambda: int,
) -> dict[str, dict[str, object]]:
    expressions: dict[str, dict[str, object]] = {
        str(shift): {
            "base_minus_lambda": -int(sds_lambda),
            "linear_terms": {},
            "quadratic_terms": {},
        }
        for shift in focus_shifts
    }

    for shift in focus_shifts:
        expr = expressions[str(shift)]
        linear_terms: dict[tuple[int, int], int] = expr["linear_terms"]  # type: ignore[assignment]
        quadratic_terms: dict[tuple[int, int, int], int] = expr["quadratic_terms"]  # type: ignore[assignment]

        for row_idx in range(4):
            for g in range(n):
                partner = (g - shift) % n
                free_left = (row_idx, g) in free
                free_right = (row_idx, partner) in free
                left_const = int(occupancy[row_idx][g])
                right_const = int(occupancy[row_idx][partner])
                old = left_const * right_const

                if not free_left and not free_right:
                    expr["base_minus_lambda"] = int(expr["base_minus_lambda"]) + old
                    continue

                expr["base_minus_lambda"] = int(expr["base_minus_lambda"]) - old

                if free_left and free_right:
                    key = (int(row_idx), int(g), int(partner))
                    quadratic_terms[key] = quadratic_terms.get(key, 0) + 1
                elif free_left:
                    coeff = int(right_const)
                    if coeff:
                        key = (int(row_idx), int(g))
                        linear_terms[key] = linear_terms.get(key, 0) + coeff
                else:
                    coeff = int(left_const)
                    if coeff:
                        key = (int(row_idx), int(partner))
                        linear_terms[key] = linear_terms.get(key, 0) + coeff

        expr["linear_terms"] = [
            {"row": row_idx, "g": g, "coeff": coeff}
            for (row_idx, g), coeff in sorted(linear_terms.items())
            if coeff != 0
        ]
        expr["quadratic_terms"] = [
            {"row": row_idx, "g": g, "partner": partner, "coeff": coeff}
            for (row_idx, g, partner), coeff in sorted(quadratic_terms.items())
            if coeff != 0
        ]

    return expressions


def lp_expr_from_terms(terms: list[tuple[int, str]]) -> str:
    if not terms:
        return "0"
    parts: list[str] = []
    for coeff, name in terms:
        if coeff == 0:
            continue
        sign = "-" if coeff < 0 else "+"
        abs_coeff = abs(coeff)
        token = f"{abs_coeff} {name}"
        if not parts:
            parts.append(token if coeff > 0 else f"- {token}")
        else:
            parts.append(f"{sign} {token}")
    return " ".join(parts) if parts else "0"


def opb_terms_from_pairs(terms: list[tuple[int, str]]) -> str:
    if not terms:
        return "0"
    return " ".join(f"{coeff} {name}" for coeff, name in terms if coeff != 0) or "0"


def get_mapping_value(mapping: dict, key: int):
    if key in mapping:
        return mapping[key]
    return mapping[str(key)]


def write_lp_text(spec: dict, tier: list[int | None], path: Path) -> None:
    K, force_M_le, weighted_cap = tier
    n = int(spec["n"])
    blocks = int(spec["blocks"])
    focus_shifts = [int(t) for t in spec["focus_shifts"]]
    occupancy = spec["occupancy"]
    block_sizes = [int(v) for v in spec["block_sizes"]]
    weights = {int(k): int(v) for k, v in spec["weights"].items()}
    pool = [tuple(item) for item in spec["candidate_pool"]]
    free = {(int(row_idx), int(g)) for row_idx, g in pool}
    shift_expressions = spec["shift_expressions"]

    binary_vars = [var_x(int(row_idx), int(g)) for row_idx, g in pool]
    binary_vars.extend(
        var_p(int(item["row"]), int(item["g"]), int(item["partner"]), shift)
        for shift in focus_shifts
        for item in shift_expressions[str(shift)]["quadratic_terms"]
    )
    general_vars = [var_d(shift) for shift in focus_shifts]
    general_vars.extend(var_u(shift) for shift in focus_shifts)
    general_vars.extend(["M", "F"])

    lines = ["Minimize", " obj: M", "Subject To"]

    for row_idx in range(blocks):
        fixed_total = sum(int(occupancy[row_idx][g]) for g in range(n) if (row_idx, g) not in free)
        lhs = lp_expr_from_terms([(1, var_x(int(i), int(g))) for i, g in pool if int(i) == row_idx])
        lines.append(f" block_size_{row_idx}: {lhs} = {block_sizes[row_idx] - fixed_total}")

    for shift in focus_shifts:
        expr = shift_expressions[str(shift)]
        for item in expr["quadratic_terms"]:
            pname = var_p(int(item["row"]), int(item["g"]), int(item["partner"]), shift)
            x1 = var_x(int(item["row"]), int(item["g"]))
            x2 = var_x(int(item["row"]), int(item["partner"]))
            lines.append(f" lin1_{shift}_{item['row']}_{item['g']}: {pname} - {x1} <= 0")
            lines.append(f" lin2_{shift}_{item['row']}_{item['g']}: {pname} - {x2} <= 0")
            lines.append(f" lin3_{shift}_{item['row']}_{item['g']}: {pname} - {x1} - {x2} >= -1")

        lhs_terms = [(1, var_d(shift))]
        lhs_terms.extend(
            [(-int(item["coeff"]), var_x(int(item["row"]), int(item["g"]))) for item in expr["linear_terms"]]
        )
        lhs_terms.extend(
            [
                (-int(item["coeff"]), var_p(int(item["row"]), int(item["g"]), int(item["partner"]), shift))
                for item in expr["quadratic_terms"]
            ]
        )
        lines.append(
            f" defect_{shift}: {lp_expr_from_terms(lhs_terms)} = {int(expr['base_minus_lambda'])}"
        )
        lines.append(f" abs_pos_{shift}: {var_d(shift)} - {var_u(shift)} <= 0")
        lines.append(f" abs_neg_{shift}: - {var_d(shift)} - {var_u(shift)} <= 0")
        lines.append(f" max_def_{shift}: {var_u(shift)} - M <= 0")
        lines.append(f" cap_{shift}: {var_u(shift)} <= {int(get_mapping_value(spec['current_abs_deltas'], shift))}")

    if force_M_le is not None:
        lines.append(f" tier_M_cap: M <= {int(force_M_le)}")

    if weighted_cap is not None:
        weighted_terms = [(weights[shift], var_u(shift)) for shift in focus_shifts]
        lines.append(f" weighted_cap: {lp_expr_from_terms(weighted_terms)} <= {int(weighted_cap)}")

    count_ones = sum(int(occupancy[int(row_idx)][int(g)]) for row_idx, g in pool)
    flip_terms = [(1, "F")]
    flip_terms.extend([(-1, var_x(int(row_idx), int(g))) for row_idx, g in pool if int(occupancy[int(row_idx)][int(g)]) == 0])
    flip_terms.extend([(1, var_x(int(row_idx), int(g))) for row_idx, g in pool if int(occupancy[int(row_idx)][int(g)]) == 1])
    lines.append(f" flip_def: {lp_expr_from_terms(flip_terms)} = {count_ones}")
    lines.append(f" flip_cap: F <= {int(K)}")

    lines.append("Bounds")
    for shift in focus_shifts:
        lines.append(f" {var_d(shift)} free")
        lines.append(f" 0 <= {var_u(shift)}")
    lines.append(" 0 <= M")
    lines.append(" 0 <= F")
    lines.append("Binaries")
    lines.extend(f" {name}" for name in binary_vars)
    lines.append("Generals")
    lines.extend(f" {name}" for name in general_vars)
    lines.append("End")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_opb_text(spec: dict, tier: list[int | None], path: Path) -> None:
    K, force_M_le, weighted_cap = tier
    n = int(spec["n"])
    blocks = int(spec["blocks"])
    focus_shifts = [int(t) for t in spec["focus_shifts"]]
    occupancy = spec["occupancy"]
    block_sizes = [int(v) for v in spec["block_sizes"]]
    weights = {int(k): int(v) for k, v in spec["weights"].items()}
    pool = [tuple(item) for item in spec["candidate_pool"]]
    free = {(int(row_idx), int(g)) for row_idx, g in pool}
    shift_expressions = spec["shift_expressions"]

    binary_vars = [var_x(int(row_idx), int(g)) for row_idx, g in pool]
    binary_vars.extend(
        var_p(int(item["row"]), int(item["g"]), int(item["partner"]), shift)
        for shift in focus_shifts
        for item in shift_expressions[str(shift)]["quadratic_terms"]
    )
    int_vars = [var_d(shift) for shift in focus_shifts]
    int_vars.extend(var_u(shift) for shift in focus_shifts)
    int_vars.extend(["M", "F"])

    constraints: list[str] = []

    for row_idx in range(blocks):
        fixed_total = sum(int(occupancy[row_idx][g]) for g in range(n) if (row_idx, g) not in free)
        terms = [(1, var_x(int(i), int(g))) for i, g in pool if int(i) == row_idx]
        constraints.append(f"{opb_terms_from_pairs(terms)} = {block_sizes[row_idx] - fixed_total} ;")

    for shift in focus_shifts:
        expr = shift_expressions[str(shift)]
        for item in expr["quadratic_terms"]:
            pname = var_p(int(item["row"]), int(item["g"]), int(item["partner"]), shift)
            x1 = var_x(int(item["row"]), int(item["g"]))
            x2 = var_x(int(item["row"]), int(item["partner"]))
            constraints.append(f"1 {pname} -1 {x1} <= 0 ;")
            constraints.append(f"1 {pname} -1 {x2} <= 0 ;")
            constraints.append(f"1 {pname} -1 {x1} -1 {x2} >= -1 ;")

        terms = [(1, var_d(shift))]
        terms.extend([(-int(item["coeff"]), var_x(int(item["row"]), int(item["g"]))) for item in expr["linear_terms"]])
        terms.extend(
            [
                (-int(item["coeff"]), var_p(int(item["row"]), int(item["g"]), int(item["partner"]), shift))
                for item in expr["quadratic_terms"]
            ]
        )
        constraints.append(f"{opb_terms_from_pairs(terms)} = {int(expr['base_minus_lambda'])} ;")
        constraints.append(f"1 {var_d(shift)} -1 {var_u(shift)} <= 0 ;")
        constraints.append(f"-1 {var_d(shift)} -1 {var_u(shift)} <= 0 ;")
        constraints.append(f"1 {var_u(shift)} -1 M <= 0 ;")
        constraints.append(f"1 {var_u(shift)} <= {int(get_mapping_value(spec['current_abs_deltas'], shift))} ;")

    if force_M_le is not None:
        constraints.append(f"1 M <= {int(force_M_le)} ;")
    if weighted_cap is not None:
        weighted_terms = [(weights[shift], var_u(shift)) for shift in focus_shifts]
        constraints.append(f"{opb_terms_from_pairs(weighted_terms)} <= {int(weighted_cap)} ;")

    count_ones = sum(int(occupancy[int(row_idx)][int(g)]) for row_idx, g in pool)
    flip_terms = [(1, "F")]
    flip_terms.extend([(-1, var_x(int(row_idx), int(g))) for row_idx, g in pool if int(occupancy[int(row_idx)][int(g)]) == 0])
    flip_terms.extend([(1, var_x(int(row_idx), int(g))) for row_idx, g in pool if int(occupancy[int(row_idx)][int(g)]) == 1])
    constraints.append(f"{opb_terms_from_pairs(flip_terms)} = {count_ones} ;")
    constraints.append(f"1 F <= {int(K)} ;")

    lines = [
        f"* #variable= {len(set(binary_vars + int_vars))} #constraint= {len(constraints)}",
        "* int " + " ".join(int_vars) + " ;",
        "min: 1 M ;",
    ]
    lines.extend(constraints)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cp_sat_script_text(spec_name: str) -> str:
    return f"""#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

try:
    from ortools.sat.python import cp_model
except ImportError as exc:
    raise SystemExit("Install ortools to run this model: pip install ortools") from exc


SPEC_PATH = Path(__file__).with_name("{spec_name}")


def load_spec() -> dict:
    with SPEC_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_model(spec: dict, K: int, force_M_le: int | None = None, weighted_cap: int | None = None):
    model = cp_model.CpModel()
    n = int(spec["n"])
    blocks = int(spec["blocks"])
    focus_shifts = [int(t) for t in spec["focus_shifts"]]
    weights = {{int(k): int(v) for k, v in spec["weights"].items()}}
    c = spec["occupancy"]
    k = [int(v) for v in spec["block_sizes"]]
    pool = [tuple(item) for item in spec["candidate_pool"]]
    free = [[False] * n for _ in range(blocks)]
    for row_idx, g in pool:
        free[row_idx][g] = True

    x = {{}}
    for row_idx, g in pool:
        x[(row_idx, g)] = model.NewBoolVar(f"x_{{row_idx}}_{{g}}")

    shift_exprs = spec["shift_expressions"]
    p = {{}}
    for t in focus_shifts:
        for item in shift_exprs[str(t)]["quadratic_terms"]:
            row_idx = int(item["row"])
            g = int(item["g"])
            g2 = int(item["partner"])
            key = (row_idx, g, g2, t)
            p[key] = model.NewBoolVar(f"p_{{row_idx}}_{{g}}_{{g2}}_{{t}}")
            model.Add(p[key] <= x[(row_idx, g)])
            model.Add(p[key] <= x[(row_idx, g2)])
            model.Add(p[key] >= x[(row_idx, g)] + x[(row_idx, g2)] - 1)

    # exact block sizes
    for row_idx in range(blocks):
        fixed_total = sum(int(c[row_idx][g]) for g in range(n) if not free[row_idx][g])
        expr = fixed_total + sum(x[(i, g)] for i, g in pool if i == row_idx)
        model.Add(expr == k[row_idx])

    d = {{}}
    u = {{}}
    M = model.NewIntVar(0, 1000, "M")
    for t in focus_shifts:
        d[t] = model.NewIntVar(-1000, 1000, f"d_{{t}}")
        u[t] = model.NewIntVar(0, 1000, f"u_{{t}}")

    for t in focus_shifts:
        shift_expr = shift_exprs[str(t)]
        expr = int(shift_expr["base_minus_lambda"])
        for item in shift_expr["linear_terms"]:
            expr += int(item["coeff"]) * x[(int(item["row"]), int(item["g"]))]
        for item in shift_expr["quadratic_terms"]:
            expr += int(item["coeff"]) * p[(int(item["row"]), int(item["g"]), int(item["partner"]), t)]
        model.Add(d[t] == expr)
        model.Add(d[t] <= u[t])
        model.Add(-d[t] <= u[t])
        model.Add(u[t] <= int(spec["current_abs_deltas"][str(t)]))
        model.Add(u[t] <= M)

    if force_M_le is not None:
        model.Add(M <= int(force_M_le))

    if weighted_cap is not None:
        model.Add(sum(weights[t] * u[t] for t in focus_shifts) <= int(weighted_cap))

    flip_terms = []
    for row_idx, g in pool:
        if int(c[row_idx][g]) == 0:
            flip_terms.append(x[(row_idx, g)])
        else:
            flip_terms.append(1 - x[(row_idx, g)])
    F = model.NewIntVar(0, len(pool), "F")
    model.Add(F == sum(flip_terms))
    model.Add(F <= int(K))

    return model, M, u, F


def solve_lexicographic(spec: dict):
    # schedule from the exported instance
    for K, force_M_le, weighted_cap in spec["recommended_schedule"]:
        model, M, u, F = build_model(spec, K=K, force_M_le=force_M_le, weighted_cap=weighted_cap)
        model.Minimize(M)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        print("tier", (K, force_M_le, weighted_cap), "status", solver.StatusName(status))
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            continue
        best_M = int(solver.Value(M))

        model2, M2, u2, F2 = build_model(spec, K=K, force_M_le=best_M, weighted_cap=weighted_cap)
        weighted_expr = sum(int(spec["weights"][str(t)]) * u2[t] for t in spec["focus_shifts"])
        model2.Minimize(weighted_expr)
        solver2 = cp_model.CpSolver()
        status2 = solver2.Solve(model2)
        print("  weighted status", solver2.StatusName(status2))
        if status2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            continue
        best_weighted = int(solver2.Value(weighted_expr))

        model3, M3, u3, F3 = build_model(spec, K=K, force_M_le=best_M, weighted_cap=best_weighted)
        model3.Minimize(F3)
        solver3 = cp_model.CpSolver()
        status3 = solver3.Solve(model3)
        print("  flip status", solver3.StatusName(status3))
        if status3 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            continue
        print("  solved tier with M=", best_M, "weighted=", best_weighted, "F=", solver3.Value(F3))
        return

    print("No feasible tier found in recommended schedule.")


if __name__ == "__main__":
    solve_lexicographic(load_spec())
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_path", type=Path)
    parser.add_argument("--focus-shifts", type=str, default="")
    parser.add_argument("--focus-top-unique", type=int, default=12)
    parser.add_argument("--endpoint-limit", type=int, default=12)
    parser.add_argument("--output-prefix", type=Path)
    args = parser.parse_args()

    payload = load_checkpoint(args.checkpoint_path)
    order = int(payload["order"])
    n = int(payload["n"])
    signature = tuple(int(value) for value in payload["signature"])
    state = np.array(payload["best_state"], dtype=np.int8)
    node = build_node(state, signature)

    explicit_focus = normalize_focus_shifts(
        [int(part.strip()) for part in args.focus_shifts.split(",") if part.strip()],
        n,
    )
    auto_focus = top_unique_sds_shifts(node.combined, args.focus_top_unique)
    focus_shifts = dedupe_preserve_order(explicit_focus + auto_focus)
    if not focus_shifts:
        raise SystemExit("provide --focus-shifts or --focus-top-unique")

    focus_deltas = sds_deltas_for_shifts(node.combined, focus_shifts)
    candidate_pool = build_candidate_pool(state, focus_shifts, focus_deltas, endpoint_limit=max(1, args.endpoint_limit))
    free = {(row_idx, g) for row_idx, g in candidate_pool}
    occupancy = ((state == -1).astype(int)).tolist()
    block_sizes = signature_to_negative_counts(signature, n)
    sds_lambda = sds_lambda_from_signature(signature, n)
    ranked_pairs = sorted(
        zip(focus_shifts, focus_deltas, strict=True),
        key=lambda item: (-abs(item[1]), item[0]),
    )
    primary_shifts = {shift for shift, _ in [(item[0], item[1]) for item in ranked_pairs[:2]]}
    weights = {shift: (10 if shift in primary_shifts else 1) for shift in focus_shifts}
    current_abs = {shift: abs(delta) for shift, delta in zip(focus_shifts, focus_deltas, strict=True)}
    current_weighted = sum(weights[shift] * current_abs[shift] for shift in focus_shifts)

    shift_expressions = compress_shift_expressions(
        occupancy=occupancy,
        free=free,
        focus_shifts=focus_shifts,
        n=n,
        sds_lambda=sds_lambda,
    )

    prefix = args.output_prefix or args.checkpoint_path.with_name(args.checkpoint_path.stem + "_pb_ilp")
    if prefix.suffix:
        prefix = prefix.with_suffix("")
    spec_path = prefix.with_suffix(".json")
    solver_path = prefix.with_name(prefix.name + "_cpsat.py")

    schedule = [
        [4, 2, None],
        [6, 3, current_weighted - 1],
        [8, 3, current_weighted - 1],
    ]

    spec = {
        "family": "goethals_seidel",
        "order": order,
        "n": n,
        "blocks": 4,
        "signature": list(signature),
        "block_sizes": block_sizes,
        "sds_lambda": int(sds_lambda),
        "source_checkpoint": str(args.checkpoint_path),
        "focus_shifts": focus_shifts,
        "focus_deltas": focus_deltas,
        "current_abs_deltas": current_abs,
        "weights": weights,
        "current_weighted_sum": int(current_weighted),
        "candidate_pool": [[int(row_idx), int(g)] for row_idx, g in candidate_pool],
        "candidate_pool_row_positions": len(candidate_pool),
        "candidate_pool_group_positions": len({g for _, g in candidate_pool}),
        "occupancy": occupancy,
        "shift_expressions": shift_expressions,
        "recommended_schedule": schedule,
        "notes": {
            "indicator_fourier_target_nontrivial": int(n),
            "sequence_psd_target_nontrivial": int(4 * n),
            "description": "Bounded occupancy PB/ILP export over ranked endpoint pool and unique monitored shifts.",
        },
    }
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    solver_path.write_text(cp_sat_script_text(spec_path.name), encoding="utf-8")
    for tier_index, tier in enumerate(schedule, start=1):
        write_lp_text(spec, tier, prefix.with_name(prefix.name + f"_tier{tier_index}.lp"))
        write_opb_text(spec, tier, prefix.with_name(prefix.name + f"_tier{tier_index}.opb"))

    print(f"spec={spec_path}")
    print(f"solver={solver_path}")
    print(f"focus_shifts={focus_shifts}")
    print(f"focus_deltas={focus_deltas}")
    print(f"candidate_pool_row_positions={len(candidate_pool)}")
    print(f"candidate_pool_group_positions={len({g for _, g in candidate_pool})}")
    print(f"current_weighted_sum={current_weighted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
