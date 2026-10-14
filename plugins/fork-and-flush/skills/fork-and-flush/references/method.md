# Method and adaptations

Source: Ziyang Cai, Christos Ziakas, Vasilis Kontonis, Tim Pearce, Siddhartha Sen,
Akshay Krishnamurthy, Shivam Garg, and Dimitris Papailiopoulos.
*Fork-and-Flush: Escaping Idea Basins in Autoresearch Agents*, arXiv:2610.07447v1.
[Paper](https://arxiv.org/html/2610.07447v1), especially sections 4–5 and appendix D.

The method alternates branching exploration with serial exploitation. Branches
inherit the workspace and discard conversation history. Selection uses each
lineage's best evaluated result, not necessarily its latest file. The paper begins
with a cold-start fan-out, then forks the winning workspace later in the run.

Its main schedule uses four branches, approximately 6% of total credits per branch,
with fan-outs at the start and around 33% and 66% of cumulative budget. One round
therefore costs approximately 24%, not 6%. The exact cadence was not exhaustively
optimized. Fixed triggers avoid a plateau detector being reset by tiny improvements.

Illustrative allocation for 100 units:

| Phase | Aggregate allocation | Cumulative allocation |
|---|---:|---:|
| Four fresh branches, 6 each | 24 | 24 |
| Continue winner | 9 | 33 |
| Four fresh branches, 6 each | 24 | 57 |
| Continue winner | 9 | 66 |
| Four fresh branches, 6 each | 24 | 90 |
| Continue winner | 10 | 100 |

The planner uses integer allocations. Its trigger positions concern allocated
budget; a runtime using measured credits must account for actual usage and stop
before exceeding the global cap. Do not silently equate reservations with spending.

## What this package changes

- A host-neutral contract replaces the paper's particular agent harness.
- Budgets may use externally capped agent time or evaluation calls when credit
  metering is unavailable. These change what is controlled and must be reported.
- Existing-incumbent and reduced-round operation are supported for practical use.
- Explicit validity, tie, hash, and failure handling make selection auditable.
- The example is a small correctness demonstration, not one of the paper's tasks.

The paper's embedding analysis diagnoses solution trajectories; it is not required
to execute the method. This package does not implement those visualizations.
