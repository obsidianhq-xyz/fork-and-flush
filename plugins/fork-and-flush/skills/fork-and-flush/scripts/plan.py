#!/usr/bin/env python3
"""Plan integer budget allocations; does not launch agents or enforce limits."""

import argparse
import json
from fractions import Fraction


def plan(budget, branches=4, explore_fraction="0.06", triggers=("0", "0.33", "0.66")):
    if type(budget) is not int or budget <= 0:
        raise ValueError("budget must be a positive integer")
    if type(branches) is not int or branches <= 0:
        raise ValueError("branches must be a positive integer")
    share = Fraction(explore_fraction)
    points = [Fraction(t) for t in triggers]
    if not 0 < share < 1:
        raise ValueError("explore fraction must be between zero and one")
    if not points or points[0] != 0 or any(p < 0 or p >= 1 for p in points):
        raise ValueError("triggers must start at zero and lie in [0, 1)")
    if any(a >= b for a, b in zip(points, points[1:])):
        raise ValueError("triggers must be strictly increasing")
    per_branch = int(budget * share)
    if per_branch < 1:
        raise ValueError("budget is too small for at least one unit per branch")
    phases, spent = [], 0
    for round_id, point in enumerate(points):
        start = int(budget * point)
        end = int(budget * points[round_id + 1]) if round_id + 1 < len(points) else budget
        if start < spent or start + branches * per_branch > end:
            raise ValueError("fork allocation overlaps the next trigger or exceeds the budget")
        if start > spent:
            phases.append({"kind": "exploit", "allocation": start - spent})
        phases.append({"kind": "fork", "round": round_id, "branches": branches,
                       "per_branch": per_branch, "allocation": branches * per_branch})
        spent = start + branches * per_branch
    if spent < budget:
        phases.append({"kind": "exploit", "allocation": budget - spent})
    return {"budget": budget, "accounting": "allocated units; not measured consumption",
            "phases": phases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--branches", type=int, default=4)
    parser.add_argument("--explore-fraction", default="0.06")
    parser.add_argument("--triggers", nargs="+", default=["0", "0.33", "0.66"])
    args = parser.parse_args()
    try:
        result = plan(args.budget, args.branches, args.explore_fraction, args.triggers)
    except (ValueError, ZeroDivisionError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
