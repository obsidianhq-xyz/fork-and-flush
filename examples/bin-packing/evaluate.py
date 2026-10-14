#!/usr/bin/env python3
"""Evaluate a trusted local candidate. Lower total bin count is better."""

import argparse
from collections import Counter
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random


def evaluate(path):
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rng = random.Random(7823)
    cases = [[], [10], [6, 4, 6, 4], [3, 3, 3, 3, 3, 3]]
    cases += [[rng.randint(1, 10) for _ in range(40)] for _ in range(12)]
    result = {"artifact_sha256": digest, "direction": "minimize", "cases": len(cases)}
    try:
        spec = importlib.util.spec_from_file_location("candidate_under_test", path)
        module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(module)
            score = 0
            for items in cases:
                bins = module.pack(list(items), 10)
                if not isinstance(bins, list) or any(not isinstance(b, list) or not b for b in bins):
                    raise ValueError("pack must return a list of nonempty lists")
                flat = [item for bucket in bins for item in bucket]
                if any(type(item) is not int for item in flat) or Counter(flat) != Counter(items):
                    raise ValueError("items were lost, duplicated, or changed")
                if any(sum(bucket) > 10 for bucket in bins):
                    raise ValueError("bin capacity exceeded")
                score += len(bins)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("candidate changed during evaluation")
        result.update(valid=True, score=score)
    except Exception as exc:
        result.update(valid=False, score=None, error=f"{type(exc).__name__}: {exc}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.candidate), sort_keys=True))
