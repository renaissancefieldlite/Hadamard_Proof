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
- corrected ring-2 / hybrid rung
  - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2.json`
  - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_cpsat.py`
  - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_sqcap_4928_final.json`
  - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_sqcap_bestscore_3392_final.json`
  - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_sqcap_bestscore_2880_final.json`

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
- `HADAMARD_EXACT_MODEL_TEST_MAP.md`
  - visual rung map of the exact-model descent
- `HADAMARD_EXACT_MODEL_PROTOCOL.md`
  - fixed scan backbone plus adaptive branch rules

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

For the corrected ring-2 / hybrid descent:

- the corrected exporter now evaluates the live basin honestly
- the second-ring exact model and square-sum surrogate produced:
  - `4928`
  - then promoted best-score basin `3392`
  - then promoted best-score basin `2880`
- current best local exact-model-assisted basin:
  - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_sqcap_bestscore_2880_final.json`
- current read of that basin:
  - `best_score = 2880`
  - `max_shift_violation = 12`
  - `indicator_fourier_max_deviation = 32`

For the next root-`2880` continuation:

- exported a new bounded PB/ILP ring from the first leakage candidate
  `runs/order_668_gs_17-17-9-3_root2880_sqcap_5440_final.json`
- used a reusable square-sum exact solver:
  - `solve_bounded_pb_sqcap.py`
- second-ring exact result:
  - `runs/order_668_gs_17-17-9-3_root2880_ring2_sqcap_K4_4032_final.json`
- exact-to-local handoff from that `4032` basin promoted a new best-score rung:
  - `runs/order_668_gs_17-17-9-3_root2880_ring2_sqcap_bestscore_2752_final.json`
- current local read of that promoted basin:
  - `best_score = 2752`
  - `max_shift_violation = 8`
  - `indicator_fourier_max_deviation = 33`
- immediate zero-slack continuation from `2752` plateaued, so this is a real
  new basin, not just an interrupted partial step
- a fixed-floor ring portfolio harness now exists:
  - `run_ring_portfolio.py`
- first portfolio validation from the `2752` floor is recorded at:
  - `runs/order_668_gs_17-17-9-3_root2752_portfolio_v2_summary.json`
- portfolio winner from that floor:
  - `mixed_6_6`
- promoted winner artifact:
  - `runs/order_668_gs_17-17-9-3_root2752_portfolio_v2_mixed_6_6_sqcap_K4_4608_bestscore_2752_final.json`
- that winner re-touches the `2752` floor but does not beat it, so the floor is
  stable and the portfolio method is acting as a disciplined seed generator

For the blended surrogate upgrade from the `2752` floor:

- upgraded portfolio summary:
  - `runs/order_668_gs_17-17-9-3_root2752_portfolio_v5_summary.json`
- that wider blended method opened a new floor:
  - `runs/order_668_gs_17-17-9-3_root2752_v5blend_floor_bestscore_2688_final.json`
- current read of that `2688` floor:
  - `best_score = 2688`
  - `max_shift_violation = 12`
  - `indicator_fourier_max_deviation = 39`
- winner ordering at that floor changed:
  - `mixed_12_12` became the best exact-seed family
  - `mixed_6_6` became second

For the meta-blended continuation from the `2688` floor:

- re-root portfolio summary:
  - `runs/order_668_gs_17-17-9-3_root2688_portfolio_v2_summary.json`
- the meta-blended floor escape from that floor opened a new floor:
  - `runs/order_668_gs_17-17-9-3_root2688_metablend_floor_bestscore_2496_512slack_final.json`
- current read of that `2496` floor:
  - `best_score = 2496`
  - `max_shift_violation = 8`
  - `indicator_fourier_max_deviation = 37`

For the first portfolio validation from the `2496` floor:

- summary:
  - `runs/order_668_gs_17-17-9-3_root2496_portfolio_v1_summary.json`
- winner ordering changed again:
  - `mixed_18_18` is now the best exact-seed family
  - `mixed_12_12` is second
- promoted winner artifact:
  - `runs/order_668_gs_17-17-9-3_root2496_portfolio_v1_mixed_18_18_sqcap_K4_4736_bestscore_2496_final.json`
- the winner re-touches the `2496` floor but does not beat it, so `2496` is the
  current stable local frontier

For the next surrogate upgrade after the `2496` floor:

- exporter-time hard-capped guard shifts were added to the PB/ILP path so seed
  quality can be constrained before late repair
- first guarded `2496` validation improved some exact seeds early, especially
  the Fourier-led side, but strict guarded `mixed_18_18` also showed that the
  cap schedule can freeze the seed if it is too rigid
- current read:
  - hard caps earlier are the right direction
  - the next rung is staged guard-cap tuning, not just wider rings or more
    Fourier pressure

For the first staged guard-cap tuning pass on the `2496` winner surface:

- baseline winner surface remains `mixed_18_18`
- forcing square-drop at the first guarded exact stage still over-constrains the
  seed
- a relaxed guarded no-drop seed stage is now validated:
  - `runs/order_668_gs_17-17-9-3_root2496_mixed18_guardv3_nodrop_retry_K4_4736_final.json`
  - `best_score = 4736`
  - `pb_ilp_monitored_square_sum = 38`
- updated read:
  - the right next schedule is now two-stage:
    1. guarded no-drop seed shaping
    2. promotion / local repair from that shaped seed

## Meaning

The important repo-level change is:

- the widened GS/SDS lane is real
- the exact repair layer is real
- coupled capped repair can improve the live basin without giving up the score
  floor
- the repo now carries a real bounded PB/ILP export surface from the best public
  basin
- the corrected exact-model cycle can now produce real full-score improvements,
  not just monitored-window improvements
- the next root-`2880` exact-to-local cycle improved the live local floor again,
  from `2880` to `2752`
- the next process improvements were both methodological and numeric:
  - blended surrogate promotion opened `2752 -> 2688`
  - meta-blended floor escape opened `2688 -> 2496`
  - the fixed-floor ring portfolio now tracks a winner-family widening:
    `mixed_6_6 -> mixed_12_12 -> mixed_18_18`
- the work is not solved, but the frontier surface is stronger and cleaner than
  the earlier Williamson-only state

## Next Step

The next clean rung after this note is:

- keep the `2496` basin as the frozen floor
- use the `2496` ring portfolio harness as the default driver for new exact-ring
  cycles
- treat `mixed_18_18` as the default portfolio winner until another ring family
  beats it on true global score
- promote only the top `1-2` portfolio seeds into hybrid/local repair
- if that cycle plateaus, widen the ring or change the surrogate before asking
  for a new reduction

## Public Reminder

These artifacts are milestone basins, not exact solutions.

The problem is solved only when a candidate CSV passes `verify_hadamard.py`.
