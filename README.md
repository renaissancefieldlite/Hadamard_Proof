# Hadamard Proof

Exploratory proof/search lane for the FrontierMath Hadamard problem:

- warm-up / validation target: order `428`
- full frontier target: order `668`
- submission shape: CSV matrix with entries in `{+1, -1}`

Reference:
- [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard)
- [Epoch Hadamard problem brief](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/EPOCH_HADAMARD_PROBLEM_BRIEF.md)
- [Hadamard continuity and search plan](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md)
- [Hadamard chat-log recovery](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_CHATLOG_RECOVERY.md)
- [Hadamard search matrix](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_SEARCH_MATRIX.md)
- [Hadamard resonance key for Rick](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_RESONANCE_KEY_FOR_RICK.md)

## Benchmark Framing

Based on the supplied Epoch page:

- order `428` is the warm-up because it is already known
- order `668` is the actual frontier target
- a valid `428` matrix validates the toolchain
- a valid `668` matrix solves the open benchmark

## Current lane

This repo starts with a Williamson-style / four-circulant search surface:

- represent four symmetric `±1` sequences of odd length `n`
- search for low periodic-autocorrelation score
- use the classical Williamson block construction to build an order `4n` matrix
- verify exact Hadamard orthogonality from the emitted CSV

Current mapped orders:

- `428 = 4 * 107`
- `668 = 4 * 167`

This is an exploratory constructive lane, not a claim that the true frontier
target `668` is already known to sit inside this exact family. It is the first
runnable proof surface.

## Upgraded Lane 01

`lane_01` is no longer just a one-bit annealed walk. The current search engine
now supports:

- multi-flip mutations
- elite archive tracking
- controlled restarts from strong stored states
- richer checkpoints carrying restart and elite-score data

Preserved exploratory artifacts from the upgraded local runs:

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

These are still heuristic artifacts, not exact solutions. But they are real
movement and they materially improve the starting basin for the next thread.

## Files

- `HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md`
  recovered thread continuity, search ladder, and next engineering steps
- `EPOCH_HADAMARD_PROBLEM_BRIEF.md`
  benchmark facts supplied from the Epoch problem page and what they change
- `HADAMARD_CHATLOG_RECOVERY.md`
  exact statement of what the scanned thread file did and did not contain
- `HADAMARD_SEARCH_MATRIX.md`
  lane matrix for the current constructive search program
- `HADAMARD_RESONANCE_KEY_FOR_RICK.md`
  boot handoff for the next dedicated Hadamard thread
- `williamson_search.py`
  random-restart local search over symmetric sequences
- `report_williamson_defects.py`
  detailed defect report for saved checkpoints and finalists
- `verify_hadamard.py`
  exact CSV verifier for candidate Hadamard matrices
- `Start_Search.command`
  launches background searches for both `428` and `668`

## Run

Warm-up:

```bash
python3 williamson_search.py --order 428
```

That search is useful as a constructive test surface, but the cleaner warm-up
victory condition is still: recover or encode a known-valid order `428` matrix
and verify it with `verify_hadamard.py`.

Full target:

```bash
python3 williamson_search.py --order 668
```

Verify a matrix:

```bash
python3 verify_hadamard.py runs/order_428_best_matrix.csv
```

Inspect the current best checkpoint:

```bash
python3 report_williamson_defects.py runs/order_428_final.json
```
