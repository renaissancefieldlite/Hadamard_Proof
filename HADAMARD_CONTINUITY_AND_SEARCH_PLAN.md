# Hadamard Continuity And Search Plan

## Frontier Target

This lane is pointed at the [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard).

Current targets already wired into this repo:

- warm-up / validation target: order `428`
- full frontier target: order `668`
- submission shape: square CSV matrix with entries in `{+1, -1}`

The current repo encodes the factorization already in use:

- `428 = 4 * 107`
- `668 = 4 * 167`

That is why the present search lane is built around four sequences of length
`107` or `167` and then lifted into an order `4n` candidate matrix.

## Epoch Benchmark Facts Supplied In-Thread

The user also supplied the text of the Epoch problem page directly in-thread.
That gives the benchmark frame we should now treat as authoritative for this
repo's orientation:

- order `668` is the open target
- order `428` is a warm-up because it is already known
- the page states that the previous smallest unknown case, `428`, was resolved
  in `2004` by Kharaghani and Tayfeh-Rezaie
- the final requested output is a CSV matrix
- the listed AI results say `GPT-5.2 Pro` solved the warm-up but not the full
  target

Operational consequence:

- order `428` should now be treated primarily as a toolchain-validation and
  construction-recovery benchmark
- order `668` remains the actual frontier solve target

This matters because "find a valid 428 matrix" and "solve the open 668 case"
are not the same claim.

## Continuity Recovered From This Thread

The live thread established these points and they matter for how this repo
should evolve:

- do not rebuild from a thin summary when the real path is still available
- keep the matrix-search plan attached to local continuity, not just current
  code
- preserve why the current lane exists, where it is weak, and what the next
  search spaces are
- build searchable local recovery artifacts so the Hadamard lane can be
  resumed after compaction without losing the thread

The moved chat export in Playground did **not** carry the Hadamard part of the
conversation, so the Hadamard continuity here is being rebuilt from:

- the live thread continuity
- this repo's existing code and runs
- the local Playground log/report chain

The thread plus the supplied Epoch page now jointly establish the clean split:

- chat-log continuity contributes benchmark posture and artifact discipline
- Epoch benchmark facts pin which target is validation work and which target is
  genuine frontier novelty
- repo code and runs supply the current mathematical starting surface

## Current Repo State

### Active search lane

The current implementation is [williamson_search.py](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/williamson_search.py):

- four symmetric `±1` sequences
- periodic autocorrelation objective
- row-sum penalty
- four-circulant Williamson block lift
- exact CSV verifier through [verify_hadamard.py](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/verify_hadamard.py)

### What the current search is actually doing

It is a random-restart / annealed local search over the independent bits of
four symmetric sequences. At each step it:

1. flips one free bit inside one sequence
2. scores the candidate by combined periodic autocorrelation plus row-sum penalty
3. accepts downhill moves and some uphill moves according to temperature
4. checkpoints the best free-state found so far

### Current observed scores

From the latest saved runs now present in `runs/`:

- order `428`: `best_score = 10304` with best found at step `80` in the saved
  short baseline
- order `668`: `best_score = 21888` at step `1500`

The refreshed defect tooling now shows, for the saved `428` baseline:

- `periodic_score = 10304`
- `row_sum_penalty = 0`
- `max_shift_violation = 24`

That means the current best `428` lane is no longer blocked by row-sum balance.
It is now primarily a periodic-autocorrelation defect problem.

That means the present lane is producing structure, but it is not yet close to
an exact solution. We should treat it as a valid first surface, not the whole
search program.

Because `428` is a known case, this heuristic lane should now be read as a
constructive search surface and diagnostics surface, not as the only sensible
way to validate the warm-up benchmark.

## 2026-04-07 Lane 01 Upgrade Result

The current `lane_01` search engine has now been hardened beyond the original
one-bit annealed walk. It supports:

- multi-flip mutation steps
- elite archive tracking
- controlled restarts from elite states
- richer checkpoint payloads with restart and elite-score data

Preserved upgraded local artifacts:

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

Compared with the earlier stored baselines:

- order `428` improved from `10304` to `5536`
- order `668` improved from `21888` to `13216`
- order `668` max-shift defect improved from `36` to `24`

This does not solve the problem. It does show that the current family still has
traction and that the upgraded search loop is worth preserving as the active
baseline rather than treating the original lane as the current state of the art.

## What Must Be True For A Real Frontier Solution

To solve the FrontierMath target from this repo, we need:

1. a matrix family that can actually realize an order `428` or `668` Hadamard
   matrix
2. a search representation that enforces enough structure to keep the search
   tractable
3. a scoring or constraint system that correlates strongly with exact
   orthogonality instead of just vaguely moving downhill
4. an exact verification path that emits the final CSV matrix

The repo already has item `4`. The work now is items `1` through `3`.

For order `428`, the requirement is softer:

- we need a clean path to a valid known construction or imported matrix
- we need verification to pass on that matrix
- we need the export/verification path to be trustworthy before claiming any
  `668` breakthrough

## Matrix Search Ladder

### Lane 0: Recover the known warm-up target cleanly

Because `428` is already known, the repo should gain a lane dedicated to warm-up
recovery:

- encode or import a known valid order `428` matrix
- verify it with `verify_hadamard.py`
- use it as the baseline acceptance test for CSV/export correctness

Why this matters:

- it separates build validation from open-problem novelty
- it gives the new thread an exact acceptance test that should be reachable
- it keeps the full `668` search from being judged on a shaky toolchain

### Lane 1: Strengthen the existing Williamson / four-circulant lane

Keep the current family, but make the search much sharper:

- incremental updates for periodic autocorrelation instead of full recompute
- multi-bit neighborhood moves, not only one-bit flips
- tabu / beam / elite archive instead of a single state path
- restart pools with score-diversity control
- canonicalization under trivial symmetries so equivalent states are not
  revisited

Why this matters:

- it is the fastest route to a stronger baseline because the current code
  already exists
- it will tell us whether this family has traction for `107` and `167`

### Lane 2: Turn the autocorrelation conditions into an exact constraint search

Instead of only hill-climbing the score, express the sequence conditions as
hard constraints:

- periodic autocorrelation cancellation conditions
- row-sum constraints
- symmetry constraints
- normalization of first entries / sign gauges

This can be pushed into:

- SAT / MaxSAT
- CP-SAT
- integer programming over `±1` or binary encodings

Why this matters:

- the current score function is only a proxy
- an exact solver can cut away huge parts of the search space when the family
  is correct but the heuristic is too loose

### Lane 3: Expand beyond the current symmetric Williamson restriction

The present code assumes symmetric sequences. That is a strong narrowing.
If `107` or `167` do not admit a solution in that narrowed family, the search
must widen.

The next family expansion should include:

- nonsymmetric four-circulant variants
- Goethals-Seidel style block constructions
- propus-like variants where the block relations differ from strict Williamson
- supplementary difference set style encodings if they fit the target orders

Why this matters:

- a no-solution result inside the current narrow family would not mean the
  FrontierMath target is impossible
- it would only mean the current family is too tight

### Lane 4: Matrix-level local search, not just sequence-level search

If block-family searches stall, add a matrix-level lane:

- start from a structured candidate matrix
- optimize row/column orthogonality defects directly
- use row-pair violation counts as the objective
- mix local row/column moves with block-preserving moves

Why this matters:

- some useful descent directions may only appear once the full lifted matrix is
  visible
- matrix-level defects can guide search differently than sequence PAF scores

## Immediate Engineering Steps

### Step 1: Add a warm-up validation lane

Do not treat order `428` as just another heuristic score target.
Instead:

- add an explicit `lane_00`
- recover or encode a known-valid order `428` matrix
- make `verify_hadamard.py` the acceptance test for that lane

### Step 2: Preserve and annotate the current lane

Do not throw away the existing Williamson code. Instead:

- tag it explicitly as `lane_01`
- record the best scores already achieved
- record the assumptions it makes:
  - four-circulant
  - symmetric sequences
  - PAF + row-sum score
  - multi-flip local mutations
  - elite archive retention
  - controlled elite-based restarts

### Step 3: Add richer checkpoint data

Checkpoint files should also save:

- periodic score and row-sum penalty separately
- sequence row sums
- restart id
- acceptance rate
- temperature at checkpoint
- elite archive score histogram

### Step 4: Build an exact defect report

Add a utility that reports:

- which shifts still violate PAF cancellation
- how large each violation is
- whether row sums are in the admissible regime

This gives the search a shape to push against instead of only one aggregate
number.

That utility now exists as:

- [report_williamson_defects.py](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/report_williamson_defects.py)

### Step 5: Add a second search engine

The repo should not stay single-lane.

Add:

- one exact constraint lane
- or one broader block-family lane

That is how we avoid mistaking one stalled heuristic for the whole problem.

## Practical Solve Path From Here

The build order should be:

1. recover or encode a valid known order `428` matrix
2. preserve current lane and annotate assumptions
3. add defect-report tooling
4. keep speeding up scoring and preserve the new elite-restart archive lane
5. add exact-constraint lane over the same family
6. widen the family if the exact lane still shows no traction
7. keep exact CSV verification as the final gate

## Why This Document Exists

This file is here so the Hadamard lane does not get rebuilt from amnesia.

The point is not only to remember:

- `428`
- `668`
- Williamson

The point is to remember the whole search posture:

- which target is already known and should validate the build
- which target is still the frontier novelty claim
- what the current code assumes
- what it is good for
- where it is too narrow
- and how we intend to widen the search until the matrix family and the search
  engine actually meet the FrontierMath target
