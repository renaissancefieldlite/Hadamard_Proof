#!/usr/bin/env python3
"""Run a bounded ring portfolio from one floor basin and promote the best seeds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from exact_sds_local_repair import (
    build_node,
    indicator_fourier_profile,
    load_checkpoint,
    top_unique_sds_shifts,
)


@dataclass
class RingSpec:
    name: str
    focus_shifts: list[int]


def dedupe_preserve_order(values: list[int], n: int) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for value in values:
        shift = int(value) % n
        if shift <= 0 or shift >= n:
            continue
        rep = min(shift, n - shift)
        if rep == 0 or rep in seen:
            continue
        seen.add(rep)
        ordered.append(rep)
    return ordered


def top_unique_fourier_reps(state: np.ndarray, limit: int) -> list[int]:
    n = state.shape[1]
    _, _, items = indicator_fourier_profile(state)
    reps: list[int] = []
    seen: set[int] = set()
    for item in items:
        rep = min(int(item["frequency"]), n - int(item["frequency"]))
        if rep <= 0 or rep in seen:
            continue
        seen.add(rep)
        reps.append(rep)
        if len(reps) >= limit:
            break
    return reps


def default_ring_specs(state: np.ndarray, signature: tuple[int, int, int, int]) -> list[RingSpec]:
    node = build_node(state, signature)
    n = state.shape[1]
    defect_top12 = top_unique_sds_shifts(node.combined, 12)
    defect_top6 = top_unique_sds_shifts(node.combined, 6)
    fourier_top12 = top_unique_fourier_reps(state, 12)
    mixed_6_6 = dedupe_preserve_order(defect_top6 + fourier_top12[:6], n)
    return [
        RingSpec("defect_top12", defect_top12),
        RingSpec("defect_top6", defect_top6),
        RingSpec("fourier_top12", fourier_top12),
        RingSpec("mixed_6_6", mixed_6_6),
    ]


def run_cmd(cmd: list[str], workdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=workdir,
        check=True,
        capture_output=True,
        text=True,
    )


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def best_sqcap_candidate(prefix: Path) -> Path | None:
    candidates = sorted(prefix.parent.glob(prefix.name + "_K*_final.json"))
    if not candidates:
        return None

    def key(path: Path) -> tuple[int, int, int, int]:
        payload = read_json(path)
        return (
            int(payload["best_score"]),
            int(payload["best_metrics"]["max_shift_violation"]),
            int(payload["indicator_fourier_max_deviation"]),
            int(payload["pb_ilp_monitored_square_sum"]),
        )

    return min(candidates, key=key)


def promote_best_score_seen(repair_path: Path) -> Path | None:
    payload = read_json(repair_path)
    best_score_seen = int(payload["best_score_seen"])
    current_score = int(payload["best_score"])
    if best_score_seen >= current_score:
        return None

    out_path = repair_path.with_name(repair_path.stem.replace("_repair", f"_bestscore_{best_score_seen}") + "_final.json")
    promoted = {
        "family": payload["family"],
        "order": payload["order"],
        "n": payload["n"],
        "signature": payload["signature"],
        "sds_lambda": payload["sds_lambda"],
        "repair_source": str(repair_path.resolve()),
        "repair_promoted_from_best_score_seen": True,
        "repair_focus_shifts": payload["focus_shifts"],
        "repair_history": payload["best_score_seen_history"],
        "best_focus_deltas": payload["best_score_seen_focus_deltas"],
        "indicator_fourier_target": payload["best_score_seen_indicator_fourier_target"],
        "indicator_fourier_max_deviation": payload["best_score_seen_indicator_fourier_max_deviation"],
        "indicator_fourier_top_deviations": payload["best_score_seen_indicator_fourier_top_deviations"],
        "best_score": payload["best_score_seen"],
        "best_metrics": payload["best_score_seen_metrics"],
        "best_state": payload["best_score_seen_state"],
    }
    out_path.write_text(json.dumps(promoted, indent=2), encoding="utf-8")
    return out_path


def checkpoint_key(path: Path) -> tuple[int, int, int]:
    payload = read_json(path)
    return (
        int(payload["best_score"]),
        int(payload["best_metrics"]["max_shift_violation"]),
        int(payload["indicator_fourier_max_deviation"]),
    )


def write_summary(path: Path, summary: dict) -> None:
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("floor_checkpoint", type=Path)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--endpoint-limit", type=int, default=20)
    parser.add_argument("--time-limit", type=float, default=20.0)
    parser.add_argument("--promote-count", type=int, default=2)
    parser.add_argument("--repair-depth", type=int, default=6)
    parser.add_argument("--repair-beam-width", type=int, default=96)
    parser.add_argument("--repair-swap-pool-limit", type=int, default=256)
    parser.add_argument("--repair-endpoint-limit", type=int, default=20)
    args = parser.parse_args()

    workdir = Path.cwd()
    floor_payload = load_checkpoint(args.floor_checkpoint)
    state = np.array(floor_payload["best_state"], dtype=np.int8)
    signature = tuple(int(v) for v in floor_payload["signature"])
    floor_score = int(floor_payload["best_score"])
    n = int(floor_payload["n"])
    base_prefix = args.output_prefix or args.floor_checkpoint.with_name(args.floor_checkpoint.stem + "_portfolio")

    ring_specs = default_ring_specs(state, signature)
    ring_results: list[dict[str, object]] = []
    summary_path = base_prefix.with_name(base_prefix.name + "_summary.json")

    print(f"floor={args.floor_checkpoint}", flush=True)
    print(f"floor_score={floor_score}", flush=True)

    def persist(promoted_items: list[dict[str, object]]) -> None:
        write_summary(
            summary_path,
            {
                "floor_checkpoint": str(args.floor_checkpoint),
                "floor_score": floor_score,
                "rings": ring_results,
                "promoted": promoted_items,
            },
        )

    persist([])
    for ring in ring_specs:
        focus = dedupe_preserve_order(ring.focus_shifts, n)
        export_prefix = base_prefix.with_name(base_prefix.name + f"_{ring.name}_pb_ilp")
        run_cmd(
            [
                sys.executable,
                "export_bounded_pb_ilp.py",
                str(args.floor_checkpoint),
                "--focus-top-unique",
                "0",
                "--focus-shifts",
                ",".join(str(v) for v in focus),
                "--endpoint-limit",
                str(max(1, args.endpoint_limit)),
                "--output-prefix",
                str(export_prefix),
            ],
            workdir,
        )
        sq_prefix = base_prefix.with_name(base_prefix.name + f"_{ring.name}_sqcap")
        run_cmd(
            [
                sys.executable,
                "solve_bounded_pb_sqcap.py",
                str(export_prefix.with_suffix(".json")),
                "--output-prefix",
                str(sq_prefix),
                "--K-values",
                "4,6,8",
                "--translation-fix",
                "--time-limit",
                str(args.time_limit),
            ],
            workdir,
        )
        best_candidate = best_sqcap_candidate(sq_prefix)
        if best_candidate is None:
            ring_results.append(
                {
                    "ring": ring.name,
                    "focus_shifts": focus,
                    "status": "no_candidate",
                }
            )
            continue
        key = checkpoint_key(best_candidate)
        ring_results.append(
            {
                "ring": ring.name,
                "focus_shifts": focus,
                "status": "ok",
                "best_candidate": str(best_candidate),
                "best_candidate_key": list(key),
            }
        )
        print(f"ring={ring.name} best_candidate={best_candidate} key={key}", flush=True)
        persist([])

    successful = [item for item in ring_results if item.get("status") == "ok"]
    successful.sort(key=lambda item: tuple(item["best_candidate_key"]))  # type: ignore[index]
    promoted: list[dict[str, object]] = []
    for item in successful[: max(1, args.promote_count)]:
        candidate_path = Path(str(item["best_candidate"]))
        repair_path = candidate_path.with_name(candidate_path.stem.replace("_final", "_repair") + ".json")
        run_cmd(
            [
                sys.executable,
                "exact_sds_local_repair.py",
                str(candidate_path),
                "--focus-top-unique",
                "12",
                "--depth",
                str(max(1, args.repair_depth)),
                "--beam-width",
                str(max(1, args.repair_beam_width)),
                "--endpoint-limit",
                str(max(1, args.repair_endpoint_limit)),
                "--swap-pool-limit",
                str(max(1, args.repair_swap_pool_limit)),
                "--score-slack",
                "0",
                "--output",
                str(repair_path),
            ],
            workdir,
        )
        repair_payload = read_json(repair_path)
        promoted_path = promote_best_score_seen(repair_path)
        promoted_item = {
            "ring": item["ring"],
            "candidate": str(candidate_path),
            "repair": str(repair_path),
            "repair_best_score": int(repair_payload["best_score"]),
            "repair_best_score_seen": int(repair_payload["best_score_seen"]),
            "promoted_path": str(promoted_path) if promoted_path else None,
        }
        promoted.append(promoted_item)
        print(
            f"promote ring={item['ring']} candidate={candidate_path.name} "
            f"repair_best={repair_payload['best_score']} best_seen={repair_payload['best_score_seen']}",
            flush=True,
        )
        persist(promoted)

    persist(promoted)
    print(f"summary={summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
