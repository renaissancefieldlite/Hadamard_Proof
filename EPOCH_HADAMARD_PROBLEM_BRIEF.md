# Epoch Hadamard Problem Brief

## Source

This brief is based on the Epoch FrontierMath Hadamard problem page content
provided directly in-thread:

- [Epoch FrontierMath Hadamard problem](https://epoch.ai/frontiermath/open-problems/hadamard/)

## Benchmark Facts Supplied In-Thread

- full target: find a Hadamard matrix of order `668`
- warm-up target: find a Hadamard matrix of order `428`
- final deliverable: provide the matrix as a CSV with entries in `{+1, -1}`
- the smallest case for which no matrix is known is stated to be `668`
- the previous smallest unknown case was `428`, resolved in `2004` by
  Kharaghani and Tayfeh-Rezaie

AI-attempt notes from the same page:

- `GPT-5.2 Pro` solved the warm-up
- `GPT-5.2 Pro` did not solve the full `668` problem
- `Gemini 3 Deep Think` did not solve the full `668` problem

Mathematician-survey notes from the same page:

- serious attempts: `5-10`
- expert-human estimate: `1-4 weeks`
- notability: moderately interesting
- publication venue expectation: standard specialty journal
- estimated solvability: `95-99%`

## What This Changes In The Repo

The current repo had already treated `428` as a warm-up and `668` as the full
target. The Epoch page sharpens that into a more useful split:

1. `428` is a known-solved validation target.
   That means a verified order-`428` matrix is not the frontier novelty claim.
   It is the right place to validate the export path, verifier, and any
   construction-recovery tooling.

2. `668` is the actual frontier target.
   That is the order where a new valid CSV would count as solving the Epoch
   problem.

3. Warm-up work still matters.
   If the repo cannot reliably recover or ingest a valid `428` matrix, then the
   toolchain is not yet trustworthy enough for `668`.

## Repo Consequences

The search program should now be read as:

- `lane_00`: recover, encode, or import a known-valid order `428` construction
  and verify it cleanly
- `lane_01`: keep the current heuristic Williamson / four-circulant search as a
  live constructive baseline
- `lane_02+`: exact-constraint and wider-family lanes aimed at `668`

## Clean Handoff Sentence

Use this as the benchmark anchor in the next Hadamard thread:

`Epoch's page says 428 is the warm-up because it is already known, while 668 is
the smallest unknown case. So the new thread should treat 428 as build and
verification validation, and treat 668 as the real novelty target.`
