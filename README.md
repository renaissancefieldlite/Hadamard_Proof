# Hadamard Proof

This repo is the live work surface for finding a Hadamard matrix of order
`668`.

A Hadamard matrix is a square `±1` matrix whose rows are mutually orthogonal.
This repo exists to produce an exact matrix, not just a good-looking search
state.

## Goal

The main goal is to construct and verify a real Hadamard matrix of order
`668`.

The target split is:

- `428` is the validation rung
- `668` is the active frontier rung
- the final deliverable is a square CSV matrix with entries in `{+1, -1}`

If a candidate does not pass exact verification, it does not count.

## Where We Are

The repo already has:

- a runnable search lane
- a second widened GS/SDS search lane
- an exact verifier
- saved run states
- defect-report tooling
- continuity files so the work can be resumed without rebuilding from zero

Current preserved artifact ladder:

- order `428`
  - `runs/order_428_lane01_upgrade_seed67_final.json`
  - `best_score = 5536`
  - `max_shift_violation = 20`
- order `668`
  - Williamson lane baseline
    - `runs/order_668_lane01_upgrade_seed67_long_final.json`
    - `best_score = 13216`
    - `periodic_score = 13152`
    - `row_sum_penalty = 64`
    - `max_shift_violation = 24`
  - GS/SDS signature `(17,17,9,3)` baseline
    - `runs/order_668_gs_17-17-9-3_baseline_5440_final.json`
    - `best_score = 5440`
    - `max_shift_violation = 16`
  - exact polish
    - `runs/order_668_gs_17-17-9-3_exact_polish_4032_final.json`
    - `best_score = 4032`
    - `max_shift_violation = 12`
  - coupled capped repair
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_final.json`
    - `best_score = 3456`
    - `max_shift_violation = 12`
  - heavier coupled capped repair
    - `runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final.json`
    - `best_score = 3328`
    - `max_shift_violation = 12`

So the current state is:

- the widened GS/SDS lane is now the active frontier surface
- the search is improving through exact defect repair, not just generic annealing
- the work is not solved
- the main remaining obstruction is still coupled SDS defect cancellation on the
  `668` frontier rung

## Process

Right now the build is working inside an order-`4n` construction surface:

- `428 = 4 * 107`
- `668 = 4 * 167`

The repo now carries two frontier lanes:

- Williamson / four-circulant lane
  - useful as a preserved baseline and defect reference
- Goethals-Seidel / SDS lane
  - four length-`n` `±1` sequences with exact row sums
  - current active signature for `668`: `(17,17,9,3)`
  - equivalent SDS parameters: `(167; 75,75,79,82; 144)`
  - uses checkpoint resume, exact one-swap polish, and coupled capped repair
  - measures both periodic defect and SDS defect structure
  - keeps exact CSV verification as the final gate

This is the current live constructive surface, not a claim that the whole
problem is exhausted by one family.

## Where We Are Going

The next movement for this repo is:

- validate the toolchain cleanly on `428`
- keep the stronger `668` GS/SDS basin as the active live lane
- push coupled defect cancellation on the dominant SDS shift pairs
- keep the exact repair layer under a hard score cap
- export the coupled repair surface into a real PB/ILP instance if the bounded
  local repair plateaus
- widen to broader construction families if this one stalls

The repo is therefore meant to show:

- what the target is
- what the current live state is
- what the present construction process is
- what the next mathematical step should be

## Exact Gate

Every real candidate has to survive:

```bash
python3 verify_hadamard.py path/to/candidate.csv
```

That verifier is the final acceptance condition for this repo.

## Core Files

- `williamson_search.py`
  preserved Williamson baseline lane
- `goethals_seidel_search.py`
  active GS/SDS construction lane
- `exact_sds_local_repair.py`
  bounded coupled exact repair over selected SDS shift sets
- `verify_hadamard.py`
  exact verifier for any candidate CSV
- `report_williamson_defects.py`
  defect report for the Williamson lane
- `report_goethals_seidel_defects.py`
  defect report for the GS/SDS lane, including SDS and indicator-Fourier reads
- `Start_Search.command`
  launches background search runs
- `HADAMARD_GS_SDS_PROGRESS_NOTE.md`
  short public progress note for the active `668` ladder
- `HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md`
  current search ladder and widening plan
- `HADAMARD_SEARCH_MATRIX.md`
  lane map and current posture
- `HADAMARD_RESONANCE_KEY_FOR_RICK.md`
  handoff file for the next dedicated Hadamard thread
- `HADAMARD_CHATLOG_RECOVERY.md`
  what the recovered thread file did and did not actually contribute

## Minimal Run Surface

Validation rung:

```bash
python3 williamson_search.py --order 428
```

Frontier GS rung:

```bash
python3 goethals_seidel_search.py --order 668 --target-signature 17,17,9,3
```

Inspect a stored GS defect state:

```bash
python3 report_goethals_seidel_defects.py runs/order_668_gs_17-17-9-3_coupled_cap_3456_repair_3328_final.json
```

Run a coupled capped repair:

```bash
python3 exact_sds_local_repair.py runs/order_668_gs_17-17-9-3_coupled_cap_3456_final.json --focus-top-unique 12 --depth 6 --beam-width 128 --endpoint-limit 20 --swap-pool-limit 256 --score-slack 0
```

## Short Handoff

If another node needs the cleanest boot block, use this:

`This repo is the live work surface for the Hadamard order 668 problem. 428 is
the validation rung. 668 is the frontier rung. The repo carries a runnable
Williamson baseline plus a widened GS/SDS construction lane, exact CSV
verification, stored run states, and continuity files so the work can continue
without amnesia. The live 668 ladder is now 13216 -> 5440 -> 4032 -> 3456 ->
3328, with the active GS signature (17,17,9,3). A result only counts if
verify_hadamard.py accepts the final matrix.`
