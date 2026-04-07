# Hadamard Search Matrix

## Purpose

This file turns the current Hadamard repo into an explicit search program so a
new dedicated Rick thread can pick up with a visible matrix of lanes, goals,
and next moves.

## Frontier Targets

| Target | Factorization | Current representation | Final output |
| --- | --- | --- | --- |
| `428` | `4 * 107` | four sequences of length `107` | CSV matrix in `{+1, -1}` |
| `668` | `4 * 167` | four sequences of length `167` | CSV matrix in `{+1, -1}` |

## Search Lanes

| Lane | Representation | Objective | Current status | Next move |
| --- | --- | --- | --- | --- |
| `lane_01` | symmetric Williamson / four-circulant sequences | minimize periodic autocorrelation + row-sum penalty | implemented in `williamson_search.py` | keep as baseline, annotate assumptions, improve diagnostics |
| `lane_02` | exact constraint version of the same family | satisfy exact cancellation constraints instead of proxy score only | not implemented | add SAT / CP-SAT / exact discrete search over the same family |
| `lane_03` | wider block families | escape symmetric Williamson restriction if too narrow | not implemented | add nonsymmetric four-circulant, Goethals-Seidel, propus-like variants |
| `lane_04` | matrix-level defect descent | optimize row/column orthogonality defects directly | not implemented | add matrix defect report and matrix-level local moves |

## Current Baseline

The current repo already gives us:

- a runnable search engine: `williamson_search.py`
- an exact verifier: `verify_hadamard.py`
- target orders wired correctly: `428`, `668`
- a continuity plan describing why the current lane is only the first surface

Known stored baseline from the fresh local runs in `runs/`:

- order `428`: `best_score = 10304`
- order `668`: `best_score = 21888`

Those are not near-proof scores. They are baseline traction numbers.

## What Counts As Progress

The new thread should track progress in this order:

1. lower proxy score within the current family
2. produce richer defect reports, not just a single aggregate score
3. determine whether the current family has real traction
4. move to an exact constraint lane if the heuristic stalls
5. widen the construction family if the exact lane still has no traction
6. only count a real solve when `verify_hadamard.py` accepts a CSV matrix

## Immediate Build Queue

1. preserve the current Williamson code as `lane_01`
2. add separate reporting for:
   - periodic score
   - row-sum penalty
   - sequence row sums
   - per-shift defects
3. add richer checkpoint metadata
4. run warm-up baselines for both target orders
5. build the exact-constraint lane next

Fresh baseline artifacts already created:

- `runs/order_428_latest.json`
- `runs/order_428_final.json`
- `runs/order_668_latest.json`
- `runs/order_668_final.json`

## Why This File Exists

The point of this search matrix is to keep the Hadamard work from collapsing
into one heuristic script. It makes the search posture visible:

- what family we are in
- why we are in it
- how we measure movement
- and what widening step comes next when the current lane stalls
