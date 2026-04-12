# Hadamard Resonance Key For Rick

## Thread Purpose

Start a dedicated Hadamard thread without rebuilding it from amnesia.

The immediate target is the [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard):

- warm-up / validation target: order `428`
- full frontier target: order `668`
- final deliverable: square CSV matrix with entries in `{+1, -1}`

## Global Rick Rule

Before touching the Hadamard lane, open:

- [RICK_RULES_AND_CONTINUITY_PROTOCOL.md](/Users/renaissancefieldlite1.0/Documents/Playground/RICK_RULES_AND_CONTINUITY_PROTOCOL.md)

That file carries the cross-thread continuity rules the next Rick must keep in
view:

- recover from the workspace before answering
- do not make unverified claims about repo or fix state
- do not flatten the work into generic safe language
- do not push without explicit approval
- do not reintroduce clamp language where the local record already carries its
  own evidentiary discipline

## What The Prior Chat Log Actually Gives Us

The recovered chat-log file does **not** contain explicit Hadamard math.
What it gives us is the transferable benchmark posture:

- hard search problems should live in reproducible repos
- warm-up assistance is not the same as the core solve
- model and operator contributions should be separated clearly
- exact verification is mandatory
- the right record is code + instructions + runs + a short writeup

That is the part to inject into the new thread.

## What The Supplied Epoch Page Adds

The supplied Epoch page text sharpens the benchmark frame:

- order `428` is a known warm-up case, not the open novelty claim
- order `668` is the smallest unknown case named on the page
- `GPT-5.2 Pro` is listed as solving the warm-up but not the full target

That means the repo should split its thinking cleanly:

- `428` = build-validation / construction-recovery target
- `668` = real frontier solve target

## Current Mathematical Starting State

The actual Hadamard-specific state comes from the existing repo, and this file
should be updated as the lane changes so the next Rick can recover after
compaction instead of hallucinating the old state.

The key public and local surfaces now are:

- `README.md`
- `HADAMARD_GS_SDS_PROGRESS_NOTE.md`
- `HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md`
- `williamson_search.py`
- `goethals_seidel_search.py`
- `exact_sds_local_repair.py`
- `verify_hadamard.py`

Preserved older lane:

- symmetric Williamson / four-circulant search
- four `±1` sequences of odd length `n`
- `n = 107` for order `428`
- `n = 167` for order `668`
- score = periodic autocorrelation defect + row-sum penalty
- multi-flip mutation search, elite archive, and controlled restarts

Fresh stored baseline now available in `runs/`:

- order `428`: `best_score = 10304`
- order `668`: `best_score = 21888`

Preserved upgraded `lane_01` artifacts now also exist:

- `runs/order_428_lane01_upgrade_seed67_final.json`
  - `best_score = 5536`
  - `max_shift_violation = 20`
- `runs/order_668_lane01_upgrade_seed67_long_final.json`
  - `best_score = 13216`
  - `max_shift_violation = 24`

Current active lane:

- Goethals-Seidel / SDS over `n = 167`
- active row-sum signature: `(17,17,9,3)`
- equivalent SDS parameters: `(167; 75,75,79,82; 144)`
- the public progression now preserved is:
  - `13216 -> 5440 -> 4032 -> 3456 -> 3328`
- the key public run artifacts are:
  - `runs/order_668_gs_17-17-9-3_baseline_5440_final.json`
  - `runs/order_668_gs_17-17-9-3_exact_polish_4032_final.json`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_final.json`
  - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final.json`
- current dominant unique SDS defect pairs in the best public basin:
  - `26/141 -> +3`
  - `32/135 -> +3`
- current exact process:
  - run GS search
  - read SDS and indicator-Fourier defects
  - run bounded coupled repair with a hard score cap
  - export the best live basin into bounded PB/ILP when the local surface is
    mature enough
- new exact-export rung now preserved:
  - `export_bounded_pb_ilp.py`
  - source basin:
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final.json`
  - exported spec:
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp.json`
  - exported CP-SAT skeleton:
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_cpsat.py`
  - install-free text exports:
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier1.lp`
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier1.opb`
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier2.lp`
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier2.opb`
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier3.lp`
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final_pb_ilp_tier3.opb`
- key exporter facts:
  - monitored unique shifts:
    - `26, 32, 4, 29, 38, 43, 45, 48, 49, 50, 51, 65`
  - candidate pool:
    - `96` row-positions over `81` group positions
  - current weighted defect sum:
    - `80`
  - recommended exact schedule:
    - `K = 4`, `M <= 2`
    - then `K = 6`, weighted cap `79`
    - then `K = 8`, weighted cap `79`
  - corrected Fourier audit targets:
    - indicator nontrivial target `167`
    - sequence nontrivial PSD target `668`
- corrected exact-model continuation now also preserved:
  - second-ring export:
    - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2.json`
    - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_cpsat.py`
  - reusable square-sum solver:
    - `solve_bounded_pb_sqcap.py`
  - square-sum exact rung:
    - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_sqcap_4928_final.json`
  - promoted best-score rung:
    - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_sqcap_bestscore_3392_final.json`
    - `runs/order_668_gs_17-17-9-3_pb_ilp_ring2_sqcap_bestscore_2880_final.json`
  - root-2880 continuation now also preserved locally:
    - second-ring export from `runs/order_668_gs_17-17-9-3_root2880_sqcap_5440_final.json`:
      - `runs/order_668_gs_17-17-9-3_root2880_ring2_pb_ilp.json`
      - `runs/order_668_gs_17-17-9-3_root2880_ring2_pb_ilp_cpsat.py`
    - second-ring square-sum rung:
      - `runs/order_668_gs_17-17-9-3_root2880_ring2_sqcap_K4_4032_final.json`
    - promoted best-score rung:
      - `runs/order_668_gs_17-17-9-3_root2880_ring2_sqcap_bestscore_2752_final.json`
  - current best local exact-model-assisted basin:
    - `runs/order_668_gs_17-17-9-3_root2880_ring2_sqcap_bestscore_2752_final.json`
  - exact-model process docs:
    - `HADAMARD_EXACT_MODEL_TEST_MAP.md`
    - `HADAMARD_EXACT_MODEL_PROTOCOL.md`

Current posture:

- this is a real widened frontier surface
- the exact repair layer is part of the process now, not an optional side note
- if the current GS/SDS local repair plateaus, the next rung is PB/ILP export
- a valid `428` matrix would validate the pipeline, but a valid `668` matrix is
  the actual open-problem win

## Rick Boot State

Rick should enter this thread with the following understanding already loaded:

1. we are not starting from zero
2. the current repo already contains a runnable `lane_01`
3. the previous chat-log file contributes search posture, not Hadamard formulas
4. order `428` is a known warm-up that should validate the build
5. order `668` is the real frontier target
6. the Williamson lane is no longer the only active story
7. the GS/SDS ladder is now the active frontier rung
8. the exact repair process is part of continuity and must be logged here when it changes
9. the bounded PB/ILP export layer is now part of the preserved process
10. the corrected ring-2 / hybrid exact-model loop is now part of the preserved process
11. the first job is to continue from the best preserved basin, not to restart from abstractions

## Concrete Work Order

1. recover or encode a valid known order `428` matrix and verify it
2. preserve the Williamson artifacts as historical baseline, not as the only live lane
3. preserve the GS/SDS public ladder and keep logging it here
4. continue bounded coupled repair from the best GS basin
5. use the corrected ring-2 / hybrid exact-model loop from the best preserved
   basin as the next exact solve surface
6. keep `verify_hadamard.py` as the final acceptance gate

## Coherence Key

Use this orientation in the new Hadamard thread:

`We are carrying forward the benchmark-search discipline recovered from the
thread, but the Hadamard-specific math begins from the repo itself. The Epoch
brief says 428 is the known warm-up and 668 is the real open target. So the new
thread should use 428 to validate the build and use 668 as the actual frontier
solve lane. The current repo preserves an older Williamson baseline, but the
active 668 frontier is now the GS/SDS ladder at signature (17,17,9,3), with
public progression 13216 -> 5440 -> 4032 -> 3456 -> 3328, public/local exact
continuation to 2880, and the current local root-2880 ring-2 continuation now
reaches 2752. The next process layer is not one-off ring picking: the repo now
has a fixed-floor portfolio harness in run_ring_portfolio.py that builds four
ring families from the same floor, ranks them globally, and promotes only the
top 1-2 into hybrid/local repair. Current default portfolio winner is
mixed_6_6. Our task is to keep that basin chain coherent, use the portfolio
harness from the best preserved basin, and only count a result when an exact
668 CSV Hadamard candidate survives verification.`

## Boot Payload

If Rick needs a single block to paste into a fresh Hadamard thread, use this:

`Hadamard continuity boot: the old thread log contributed benchmark posture and
artifact discipline, not direct Hadamard formulas. The supplied Epoch brief says
428 is a known warm-up and 668 is the true open target. The repo already has a
runnable Williamson baseline plus an active GS/SDS lane in
goethals_seidel_search.py, exact_sds_local_repair.py, verify_hadamard.py, and
GS defect reporting. First recover or encode a valid 428 matrix to validate the
pipeline. Then continue from the best preserved 668 GS basin, not from zero:
current public ladder is 13216 -> 5440 -> 4032 -> 3456 -> 3328 at signature
(17,17,9,3), public/local exact continuation reaches 2880, and the current
local root-2880 ring-2 continuation reaches 2752. Do not go back to one-off
ring picking by default. Use run_ring_portfolio.py from the frozen best basin,
let the four default ring families compete from the same floor, treat mixed_6_6
as the current portfolio winner, and only promote the top 1-2 into bounded
hybrid/local repair with a hard score cap.`

## What Not To Do

- do not claim the old chat log contained explicit Hadamard formulas when it did not
- do not confuse a valid warm-up `428` matrix with solving the open `668` case
- do not treat the old Williamson lane as the current whole story
- do not collapse warm-up assistance into core proof credit
- do not widen the search randomly without preserving why the current lane stalled
- do not let compaction erase the active artifact ladder; update this file when the rung changes
