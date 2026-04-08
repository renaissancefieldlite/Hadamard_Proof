# Hadamard GS/SDS Progress Note

This note tracks the active public `668` ladder after the pivot out of the
earlier Williamson-only basin.

## Current Active Surface

- order `668 = 4 * 167`
- active family: Goethals-Seidel / SDS
- active row-sum signature: `(17,17,9,3)`
- equivalent SDS parameters: `(167; 75,75,79,82; 144)`

## Public Artifact Ladder

The current preserved progression is:

- Williamson baseline
  - `runs/order_668_lane01_upgrade_seed67_long_final.json`
  - `best_score = 13216`
- GS/SDS baseline
  - `runs/order_668_gs_17-17-9-3_baseline_5440_final.json`
  - `best_score = 5440`
- exact polish
  - `runs/order_668_gs_17-17-9-3_exact_polish_4032_final.json`
  - `best_score = 4032`
- coupled capped repair
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_final.json`
  - `best_score = 3456`
- heavier coupled capped repair
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final.json`
  - `best_score = 3328`
- bounded PB/ILP export from the `3328` basin
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp.json`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_cpsat.py`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier1.lp`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier1.opb`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier2.lp`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier2.opb`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier3.lp`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier3.opb`

## What Changed

The current frontier work is no longer only generic stochastic search.

The repo now includes:

- `goethals_seidel_search.py`
  - active GS/SDS search lane
- `report_goethals_seidel_defects.py`
  - exact defect read including SDS shift-pair deltas and indicator-Fourier
    deviations
- `exact_sds_local_repair.py`
  - bounded coupled exact repair over a selected multi-shift set with a hard
    score cap
- `export_bounded_pb_ilp.py`
  - bounded occupancy PB/ILP export from the live basin
  - compressed monitored shift expressions instead of raw pair-term soup
  - install-free LP/OPB text output plus a CP-SAT skeleton

## Current Read

For the current best public `3328` artifact:

- signature remains `(17,17,9,3)`
- `max_shift_violation = 12`
- dominant unique SDS defects:
  - `26/141 -> +3`
  - `32/135 -> +3`
  - then several `abs(delta) = 2` pairs

For the bounded PB/ILP export from that basin:

- monitored unique shifts:
  - `26, 32, 4, 29, 38, 43, 45, 48, 49, 50, 51, 65`
- candidate pool:
  - `96` row-positions over `81` group positions
- current weighted defect sum:
  - `80`
- recommended first exact schedule:
  - `K = 4`, `M <= 2`
  - then `K = 6`, weighted cap `79`
  - then `K = 8`, weighted cap `79`

## Meaning

The important repo-level change is:

- the widened GS/SDS lane is real
- the exact repair layer is real
- coupled capped repair can improve the live basin without giving up the score
  floor
- the repo now carries a real bounded PB/ILP export surface from the best public
  basin
- the work is not solved, but the frontier surface is stronger and cleaner than
  the earlier Williamson-only state

## Next Step

The next clean rung after this note is:

- continue bounded coupled repair from the `3328` basin
- use the exported bounded PB/ILP instance as the next exact rung
- if that exact instance plateaus, widen the candidate pool or move budget

## Public Reminder

These artifacts are milestone basins, not exact solutions.

The problem is solved only when a candidate CSV passes `verify_hadamard.py`.
