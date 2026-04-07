# Hadamard Proof

Working repo for the Hadamard order `668` problem.

This repo does three concrete things:

- searches a constructive surface for candidate Hadamard matrices
- reports defect structure for stored states
- verifies candidate CSV matrices exactly

Current targets:

- `428` is the validation target
- `668` is the active frontier target
- the final object is a square CSV matrix with entries in `{+1, -1}`

## Current Construction Surface

The current build is centered on an order-`4n` block construction surface with
the target orders already mapped:

- `428 = 4 * 107`
- `668 = 4 * 167`

The active lane uses four length-`n` symmetric `±1` sequences, scores their
combined periodic autocorrelation defects, and lifts them through a
Williamson-style four-circulant block construction.

## Core Files

- `verify_hadamard.py`
  exact verifier for any candidate CSV
- `williamson_search.py`
  current constructive lane
- `report_williamson_defects.py`
  defect-report surface for stored states
- `Start_Search.command`
  launches background search runs
- `HADAMARD_RESONANCE_KEY_FOR_RICK.md`
  handoff for the next dedicated Hadamard thread
- `HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md`
  current search ladder and widening plan
- `HADAMARD_SEARCH_MATRIX.md`
  lane map and current search posture
- `HADAMARD_CHATLOG_RECOVERY.md`
  what the recovered thread file did and did not actually contain

## Exact Gate

Every real candidate has to survive:

```bash
python3 verify_hadamard.py path/to/candidate.csv
```

## Minimal Run Surface

Warm-up / validation rung:

```bash
python3 williamson_search.py --order 428
```

Frontier rung:

```bash
python3 williamson_search.py --order 668
```

Inspect a stored state:

```bash
python3 report_williamson_defects.py runs/order_668_final.json
```

## Thread Seed

If another node needs the cleanest boot block, use this:

`This repo is the working surface for the Hadamard order 668 problem. It
searches a Williamson / four-circulant construction lane, reports exact defect
structure for stored states, and verifies candidate CSV matrices exactly. 428
is the validation target. 668 is the active frontier target.`
