# Hadamard Search Matrix

## Purpose

This file turns the current Hadamard repo into an explicit search program so a
new dedicated Rick thread can pick up with a visible matrix of lanes, goals,
and next moves.

## Frontier Targets

| Target | Factorization | Benchmark status | Current representation | Final output |
| --- | --- | --- | --- | --- |
| `428` | `4 * 107` | known warm-up case | four sequences of length `107` | CSV matrix in `{+1, -1}` |
| `668` | `4 * 167` | smallest unknown case from the supplied Epoch brief | four sequences of length `167` | CSV matrix in `{+1, -1}` |

## Search Lanes

| Lane | Representation | Objective | Current status | Next move |
| --- | --- | --- | --- | --- |
| `lane_00` | known warm-up construction / imported CSV | recover a valid order `428` matrix and validate the pipeline end-to-end | not implemented | encode or ingest a known `428` construction and make `verify_hadamard.py` pass |
| `lane_01` | symmetric Williamson / four-circulant sequences | minimize periodic autocorrelation + row-sum penalty | implemented in `williamson_search.py` | keep as baseline, annotate assumptions, improve diagnostics |
| `lane_02` | exact constraint version of the same family | satisfy exact cancellation constraints instead of proxy score only | not implemented | add SAT / CP-SAT / exact discrete search over the same family |
| `lane_03` | wider block families | escape symmetric Williamson restriction if too narrow | not implemented | add nonsymmetric four-circulant, Goethals-Seidel, propus-like variants |
| `lane_04` | matrix-level defect descent | optimize row/column orthogonality defects directly | not implemented | add matrix defect report and matrix-level local moves |

## Current Baseline

The current repo already gives us:

- a runnable search engine: `williamson_search.py`
- a checkpoint-level defect reporter: `report_williamson_defects.py`
- an exact verifier: `verify_hadamard.py`
- target orders wired correctly: `428`, `668`
- a continuity plan describing why the current lane is only the first surface

Known stored baseline from the fresh local runs in `runs/`:

- order `428`: `best_score = 10304`
- order `668`: `best_score = 21888`

Those are not near-proof scores. They are heuristic-lane traction numbers.

Preserved upgraded `lane_01` artifacts now also exist locally:

- `runs/order_428_lane01_upgrade_seed67_final.json`
  - `best_score = 5536`
  - `periodic_score = 5472`
  - `row_sum_penalty = 64`
  - `max_shift_violation = 20`
- `runs/order_668_lane01_upgrade_seed67_long_final.json`
  - `best_score = 13216`
  - `periodic_score = 13152`
  - `row_sum_penalty = 64`
  - `max_shift_violation = 24`

That means the upgraded move set is materially better than the earlier stored
baseline on both targets, especially on the true frontier target `668`.

## What Counts As Progress

The new thread should track progress in this order:

1. recover or encode a valid `428` matrix and verify it cleanly
2. lower proxy score within the current `668` family
3. produce richer defect reports, not just a single aggregate score
4. determine whether the current family has real traction for `668`
5. move to an exact constraint lane if the heuristic stalls
6. widen the construction family if the exact lane still has no traction
7. only count a frontier solve when `verify_hadamard.py` accepts a `668` CSV matrix

## Immediate Build Queue

1. add `lane_00` and treat order `428` as a build-validation benchmark
2. preserve the current Williamson code as `lane_01`
3. add separate reporting for:
   - periodic score
   - row-sum penalty
   - sequence row sums
   - per-shift defects
4. add richer checkpoint metadata
5. run heuristic baselines for both target orders
6. build the exact-constraint lane next

Fresh baseline artifacts already created:

- `runs/order_428_latest.json`
- `runs/order_428_final.json`
- `runs/order_668_latest.json`
- `runs/order_668_final.json`

Fresh qualitative read from the current `428` baseline:

- row-sum regime is already satisfied (`row_sum_penalty = 0`)
- the remaining defect mass is periodic
- next search improvements should prioritize shift-cancellation pressure over row-sum tuning

Fresh qualitative read from the upgraded `668` run:

- the best preserved upgraded run reached `best_score = 13216`
- `row_sum_penalty` stayed small (`64`)
- `max_shift_violation` dropped to `24`
- the active bottleneck is still periodic cancellation, but the basin is
  significantly stronger than the earlier `21888` / `36` state

## Why This File Exists

The point of this search matrix is to keep the Hadamard work from collapsing
into one heuristic script. It makes the search posture visible:

- what family we are in
- which target is validation versus frontier novelty
- why we are in it
- how we measure movement
- and what widening step comes next when the current lane stalls
