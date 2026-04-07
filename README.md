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
- an exact verifier
- saved run states
- defect-report tooling
- continuity files so the work can be resumed without rebuilding from zero

Current preserved upgraded baseline artifacts:

- order `428`
  - `runs/order_428_lane01_upgrade_seed67_final.json`
  - `best_score = 5536`
  - `max_shift_violation = 20`
- order `668`
  - `runs/order_668_lane01_upgrade_seed67_long_final.json`
  - `best_score = 13216`
  - `periodic_score = 13152`
  - `row_sum_penalty = 64`
  - `max_shift_violation = 24`

So the current state is:

- the lane is real
- the search is improving
- the work is not solved
- the main remaining obstruction is still defect cancellation on the `668`
  frontier rung

## Process

Right now the build is working inside an order-`4n` construction surface:

- `428 = 4 * 107`
- `668 = 4 * 167`

The current live lane:

- searches over four length-`n` `±1` sequences
- measures periodic autocorrelation defect and row-sum pressure
- lifts candidates through a Williamson-style four-circulant block
  construction
- keeps stored checkpoints and defect reads
- uses exact CSV verification as the final gate

That is the current lane, not a claim that the whole problem is exhausted by
one family.

## Where We Are Going

The next movement for this repo is:

- validate the toolchain cleanly on `428`
- keep the stronger `668` baseline as the active live lane
- push defect cancellation harder on the dominant bad shifts
- turn the current family into a tighter exact-constraint lane
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
  current constructive search lane
- `verify_hadamard.py`
  exact verifier for any candidate CSV
- `report_williamson_defects.py`
  reads saved states and exposes where the live defects are
- `Start_Search.command`
  launches background search runs
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

Frontier rung:

```bash
python3 williamson_search.py --order 668
```

Inspect a stored defect state:

```bash
python3 report_williamson_defects.py runs/order_668_lane01_upgrade_seed67_long_final.json
```

## Short Handoff

If another node needs the cleanest boot block, use this:

`This repo is the live work surface for the Hadamard order 668 problem. 428 is
the validation rung. 668 is the frontier rung. The repo carries a runnable
Williamson / four-circulant construction lane, exact CSV verification, stored
run states, and continuity files so the work can continue without amnesia. A
result only counts if verify_hadamard.py accepts the final matrix.`
