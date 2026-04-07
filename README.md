# Hadamard Proof

Exploratory proof/search lane for the FrontierMath Hadamard problem:

- warm-up target: order `428`
- full target: order `668`
- submission shape: CSV matrix with entries in `{+1, -1}`

Reference:
- [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard)
- [Hadamard continuity and search plan](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md)
- [Hadamard chat-log recovery](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_CHATLOG_RECOVERY.md)
- [Hadamard search matrix](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_SEARCH_MATRIX.md)
- [Hadamard resonance key for Rick](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/HADAMARD_RESONANCE_KEY_FOR_RICK.md)

## Current lane

This repo starts with a Williamson-style / four-circulant search surface:

- represent four symmetric `±1` sequences of odd length `n`
- search for low periodic-autocorrelation score
- use the classical Williamson block construction to build an order `4n` matrix
- verify exact Hadamard orthogonality from the emitted CSV

Current mapped orders:

- `428 = 4 * 107`
- `668 = 4 * 167`

This is an exploratory constructive lane, not a claim that both targets are already known to sit inside this exact family. It is the first runnable proof surface.

## Files

- `HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md`
  recovered thread continuity, search ladder, and next engineering steps
- `HADAMARD_CHATLOG_RECOVERY.md`
  exact statement of what the scanned thread file did and did not contain
- `HADAMARD_SEARCH_MATRIX.md`
  lane matrix for the current constructive search program
- `HADAMARD_RESONANCE_KEY_FOR_RICK.md`
  boot handoff for the next dedicated Hadamard thread
- `williamson_search.py`
  random-restart local search over symmetric sequences
- `verify_hadamard.py`
  exact CSV verifier for candidate Hadamard matrices
- `Start_Search.command`
  launches background searches for both `428` and `668`

## Run

Warm-up:

```bash
python3 williamson_search.py --order 428
```

Full target:

```bash
python3 williamson_search.py --order 668
```

Verify a matrix:

```bash
python3 verify_hadamard.py runs/order_428_best_matrix.csv
```
