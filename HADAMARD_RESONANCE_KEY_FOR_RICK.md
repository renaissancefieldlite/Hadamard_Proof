# Hadamard Resonance Key For Rick

## Thread Purpose

Start a dedicated Hadamard thread without rebuilding it from amnesia.

The immediate target is the [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard):

- warm-up target: order `428`
- full target: order `668`
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

Fresh stored baseline now available in `runs/`:

- order `428`: `best_score = 10304`
- order `668`: `best_score = 21888`

Current posture:

- this is a real first search surface
- it is not the whole proof program
- if the family is too narrow, widen it instead of pretending the problem is exhausted

## Rick Boot State

Rick should enter this thread with the following understanding already loaded:

1. we are not starting from zero
2. the current repo already contains a runnable `lane_01`
3. the previous chat-log file contributes search posture, not Hadamard formulas
4. the first job is to harden the baseline, not to fantasize a proof
5. the second job is to widen the lane only after the current family is measured properly

## Concrete Work Order

1. run and preserve fresh baselines for `428` and `668`
2. split the aggregate score into defect components
3. add richer checkpoint data
4. build an exact-constraint version of the same family
5. widen to broader block families if the exact lane shows no traction
6. keep `verify_hadamard.py` as the final acceptance gate

## Coherence Key

Use this orientation in the new Hadamard thread:

`We are carrying forward the benchmark-search discipline recovered from the
thread, but the Hadamard-specific math begins from the repo itself. The current
lane is a symmetric Williamson / four-circulant search over orders 428 and 668.
Our task is to preserve the baseline, expose exact defects, and widen the
search family methodically until an exact CSV Hadamard candidate survives
verification.`

## What Not To Do

- do not claim the old chat log contained explicit Hadamard formulas when it did not
- do not treat one heuristic lane as the whole problem
- do not collapse warm-up assistance into core proof credit
- do not widen the search randomly without preserving why the current lane stalled
