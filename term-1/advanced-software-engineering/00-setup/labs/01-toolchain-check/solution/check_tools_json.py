"""Extension solution: the same checks as check_tools.py, but as a JSON report for CI.

Usage:
    python solution/check_tools_json.py > toolchain.json

Exit code is the number of problems with required tools, as in the lab script.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from check_tools import TOOLS, check, problems  # noqa: E402


def main() -> int:
    results = [check(tool) for tool in TOOLS]
    report = {
        "python": sys.version.split()[0],
        "tools": [
            {
                "name": r.tool.name,
                "required": r.tool.required,
                "minimum": ".".join(str(n) for n in r.tool.minimum) if r.tool.minimum else None,
                "found": r.found or None,
                "status": r.status,
                "note": r.note,
            }
            for r in results
        ],
    }
    print(json.dumps(report, indent=2))
    return len(problems(results, strict=False))


if __name__ == "__main__":
    sys.exit(main())
