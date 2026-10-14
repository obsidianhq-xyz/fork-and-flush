# Bin-packing optimization example

Improve `candidate.py`, which exposes `pack(items, capacity)` and returns lists of
item sizes, one list per bin. Every input item must appear exactly once and no bin
may exceed capacity. Empty input returns an empty list. Use the Python standard
library only. Keep the public function signature.

Minimize total bins over the fixed evaluator's cases. The evaluator validates
outputs before scoring. Do not edit the evaluator or specialize the implementation
to its seed or cases. Keep the implementation valid for arbitrary positive integer
items no larger than capacity. Only `candidate.py` is an output artifact.

From this directory, evaluate a trusted candidate with:

```sh
python3 evaluate.py candidate.py
```

The parent should evaluate an immutable copy using its own unchanged evaluator and
a process timeout. Importing a candidate executes Python; this example evaluator
is not a sandbox for untrusted code.

Example skill invocation:

> Use fork-and-flush on this existing incumbent. Run one fork round with two fresh
> Codex sessions, then continue the selected session once. Allow at most 90 seconds
> per branch and 60 seconds for continuation, totaling 240 allocated agent-seconds.
> Keep evaluator and coordinator overhead separately measured. Preserve the
> original example and report verified scores and artifact hashes.

This is a reduced-schedule correctness exercise. It does not measure the paper's
long-horizon gains, compare models, or establish statistical superiority.

