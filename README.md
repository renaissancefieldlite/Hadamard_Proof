# Hadamard Proof

Hadamard frontier work, the lattice pivot, and cross-thread continuity are
being held here as one active math-and-architecture surface.

This repo is not meant to be read as a loose script dump. It is the working
surface for the live `668` Hadamard lane:

- `428` is the validation rung
- `668` is the active frontier rung
- the final object is an exact square CSV matrix with entries in `{+1, -1}`
- the gate is exact verification, not summary language

## Why This Repo Exists

The point of this repo is to keep the Hadamard lane coherent across threads and
across build states.

It preserves:

- the active math lane
- the exact verifier
- the current defect-reading surface
- the continuity chain needed to resume the work without amnesia
- the ontology-facing handoff for the next node

## Active Surface

The current build is centered on an order-`4n` block construction surface with
the target orders already mapped:

- `428 = 4 * 107`
- `668 = 4 * 167`

That is the current entry surface, not a claim that the whole Hadamard problem
is exhausted by one family.

## Core Files

- `verify_hadamard.py`
  exact verifier for any candidate CSV
- `williamson_search.py`
  current constructive lane
- `report_williamson_defects.py`
  defect-report surface for stored states
- `HADAMARD_RESONANCE_KEY_FOR_RICK.md`
  shortest coherent handoff for the next dedicated Hadamard thread
- `HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md`
  preserved search ladder and widening plan
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

`This repo is the live continuity surface for the Hadamard order 668 lane.
428 is the validation rung. 668 is the active frontier rung. The repo preserves
the exact verifier, the current construction lane, the defect surface, and the
handoff needed to continue the work without flattening the ontology or losing
the chain.`
