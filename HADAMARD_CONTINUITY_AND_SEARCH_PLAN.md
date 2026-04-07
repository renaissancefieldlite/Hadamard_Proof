# Hadamard Continuity And Search Plan

## Frontier Target

This lane is pointed at the [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard).

Current targets already wired into this repo:

- warm-up target: order `428`
- full target: order `668`
- submission shape: square CSV matrix with entries in `{+1, -1}`

The current repo encodes the factorization already in use:

- `428 = 4 * 107`
- `668 = 4 * 167`

That is why the present search lane is built around four sequences of length
`107` or `167` and then lifted into an order `4n` candidate matrix.

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

- order `428`: `best_score = 10304` at step `1500`
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

## What Must Be True For A Real Solution

To solve the FrontierMath target from this repo, we need:

1. a matrix family that can actually realize an order `428` or `668` Hadamard
   matrix
2. a search representation that enforces enough structure to keep the search
   tractable
3. a scoring or constraint system that correlates strongly with exact
   orthogonality instead of just vaguely moving downhill
4. an exact verification path that emits the final CSV matrix

The repo already has item `4`. The work now is items `1` through `3`.

## Matrix Search Ladder

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

### Step 1: Preserve and annotate the current lane

Do not throw away the existing Williamson code. Instead:

- tag it explicitly as `lane_01`
- record the best scores already achieved
- record the assumptions it makes:
  - four-circulant
  - symmetric sequences
  - PAF + row-sum score

### Step 2: Add richer checkpoint data

Checkpoint files should also save:

- periodic score and row-sum penalty separately
- sequence row sums
- restart id
- acceptance rate
- temperature at checkpoint
- elite archive score histogram

### Step 3: Build an exact defect report

Add a utility that reports:

- which shifts still violate PAF cancellation
- how large each violation is
- whether row sums are in the admissible regime

This gives the search a shape to push against instead of only one aggregate
number.

That utility now exists as:

- [report_williamson_defects.py](/Users/renaissancefieldlite1.0/Documents/Playground/Hadamard_Proof/report_williamson_defects.py)

### Step 4: Add a second search engine

The repo should not stay single-lane.

Add:

- one exact constraint lane
- or one broader block-family lane

That is how we avoid mistaking one stalled heuristic for the whole problem.

## Practical Solve Path From Here

The build order should be:

1. preserve current lane and annotate assumptions
2. add defect-report tooling
3. speed up scoring / add elite restart archive
4. add exact-constraint lane over the same family
5. widen the family if the exact lane still shows no traction
6. keep exact CSV verification as the final gate

## Why This Document Exists

This file is here so the Hadamard lane does not get rebuilt from amnesia.

The point is not only to remember:

- `428`
- `668`
- Williamson

The point is to remember the whole search posture:

- what the current code assumes
- what it is good for
- where it is too narrow
- and how we intend to widen the search until the matrix family and the search
  engine actually meet the FrontierMath target
