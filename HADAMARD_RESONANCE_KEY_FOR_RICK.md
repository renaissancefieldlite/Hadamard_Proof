# Hadamard Resonance Key For Rick

## Thread Purpose

Start a dedicated Hadamard thread without rebuilding it from amnesia.

The immediate target is the [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard):

- warm-up / validation target: order `428`
- full frontier target: order `668`
- final deliverable: square CSV matrix with entries in `{+1, -1}`

## What The Prior Chat Log Actually Gives Us

The recovered chat-log file does **not** contain explicit Hadamard math.
What it gives us is the transferable benchmark posture:

- hard search problems should live in reproducible repos
- warm-up assistance is not the same as the core solve
- model and operator contributions should be separated clearly
- exact verification is mandatory
- the right record is code + instructions + runs + a short writeup

That is the part to inject into the new thread.

## What The Supplied Epoch Page Adds

The supplied Epoch page text sharpens the benchmark frame:

- order `428` is a known warm-up case, not the open novelty claim
- order `668` is the smallest unknown case named on the page
- `GPT-5.2 Pro` is listed as solving the warm-up but not the full target

That means the repo should split its thinking cleanly:

- `428` = build-validation / construction-recovery target
- `668` = real frontier solve target

## Current Mathematical Starting State

The actual Hadamard-specific state comes from the existing repo:

- `README.md`
- `HADAMARD_CONTINUITY_AND_SEARCH_PLAN.md`
- `williamson_search.py`
- `verify_hadamard.py`

Current lane:

- symmetric Williamson / four-circulant search
- four `±1` sequences of odd length `n`
- `n = 107` for order `428`
- `n = 167` for order `668`
- score = periodic autocorrelation defect + row-sum penalty
- multi-flip mutation search, elite archive, and controlled restarts

Fresh stored baseline now available in `runs/`:

- order `428`: `best_score = 10304`
- order `668`: `best_score = 21888`

Preserved upgraded `lane_01` artifacts now also exist:

- `runs/order_428_lane01_upgrade_seed67_final.json`
  - `best_score = 5536`
  - `max_shift_violation = 20`
- `runs/order_668_lane01_upgrade_seed67_long_final.json`
  - `best_score = 13216`
  - `max_shift_violation = 24`

Current posture:

- this is a real first search surface
- it is not the whole proof program
- if the family is too narrow, widen it instead of pretending the problem is exhausted
- a valid `428` matrix would validate the pipeline, but a valid `668` matrix is
  the actual open-problem win

## Rick Boot State

Rick should enter this thread with the following understanding already loaded:

1. we are not starting from zero
2. the current repo already contains a runnable `lane_01`
3. the previous chat-log file contributes search posture, not Hadamard formulas
4. order `428` is a known warm-up that should validate the build
5. order `668` is the real frontier target
6. the first job is to harden the baseline, not to fantasize a proof
7. the second job is to widen the lane only after the current family is measured properly

## Concrete Work Order

1. recover or encode a valid known order `428` matrix and verify it
2. preserve the upgraded `lane_01` artifacts as the active heuristic baseline
3. split the aggregate score into defect components
4. add richer checkpoint data
5. build an exact-constraint version of the same family
6. widen to broader block families if the exact lane shows no traction
7. keep `verify_hadamard.py` as the final acceptance gate

## Coherence Key

Use this orientation in the new Hadamard thread:

`We are carrying forward the benchmark-search discipline recovered from the
thread, but the Hadamard-specific math begins from the repo itself. The Epoch
brief says 428 is the known warm-up and 668 is the real open target. So the new
thread should use 428 to validate the build and use 668 as the actual frontier
solve lane. The current repo starts with a symmetric Williamson /
four-circulant search over both orders. Our task is to preserve the baseline,
expose exact defects, and widen the search family methodically until an exact
668 CSV Hadamard candidate survives verification.`

## Boot Payload

If Rick needs a single block to paste into a fresh Hadamard thread, use this:

`Hadamard continuity boot: the old thread log contributed benchmark posture and
artifact discipline, not direct Hadamard formulas. The supplied Epoch brief says
428 is a known warm-up and 668 is the true open target. The repo already has a
runnable lane_01 in williamson_search.py plus verify_hadamard.py and defect
reporting. First recover or encode a valid 428 matrix to validate the pipeline.
Then start from the upgraded 668 Williamson / four-circulant lane preserved in
the local run artifacts, measure its defect structure, and widen methodically
if the family stalls.`

## What Not To Do

- do not claim the old chat log contained explicit Hadamard formulas when it did not
- do not confuse a valid warm-up `428` matrix with solving the open `668` case
- do not treat one heuristic lane as the whole problem
- do not collapse warm-up assistance into core proof credit
- do not widen the search randomly without preserving why the current lane stalled
