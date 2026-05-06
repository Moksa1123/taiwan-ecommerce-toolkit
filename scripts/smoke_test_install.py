"""End-to-end smoke test for the three CLIs in this repo.

Each CLI's `init --ai claude` is run against a fresh temp directory; we then
verify the SKILL.md actually lands at the expected path and carries the
expected frontmatter `name`. This is the regression test for the bug where
payment-cli and logistics-cli were forked from invoice-cli without updating
their platform JSON / base templates / source command code, so installs
silently wrote into ~/.claude/skills/taiwan-invoice/ regardless of which
package was used (taiwan-payment-skill@1.1.4 and taiwan-logistics-skill@1.1.4
both shipped this bug).

Run from repo root, after building each CLI:

    python scripts/smoke_test_install.py

Add to a CLI's package.json `prepublishOnly` once Python is on the CI image:

    "prepublishOnly": "npm run build && python ../scripts/smoke_test_install.py"
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CASES = [
    {
        "cli": "invoice-cli",
        "expected_skill_path": ".claude/skills/taiwan-invoice/SKILL.md",
        "expected_frontmatter_name": "taiwan-invoice",
        "must_contain": "Taiwan E-Invoice",
        "must_not_contain": None,
    },
    {
        "cli": "payment-cli",
        "expected_skill_path": ".claude/skills/taiwan-payment/SKILL.md",
        "expected_frontmatter_name": "taiwan-payment",
        "must_contain": "Taiwan Payment",
        "must_not_contain": "Taiwan E-Invoice",
    },
    {
        "cli": "logistics-cli",
        "expected_skill_path": ".claude/skills/taiwan-logistics/SKILL.md",
        "expected_frontmatter_name": "taiwan-logistics",
        "must_contain": "Taiwan Logistics",
        "must_not_contain": "Taiwan E-Invoice",
    },
]


def run_install(cli: str, tmpdir: Path) -> tuple[bool, str]:
    cli_root = REPO / cli
    dist = cli_root / "dist" / "index.js"
    if not dist.exists():
        return False, f"build artifact missing: {dist}. Run 'npm run build' in {cli}."

    proc = subprocess.run(
        ["node", str(dist), "init", "--ai", "claude"],
        cwd=tmpdir,
        input="n\n",
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.lstrip().startswith("---"):
        return {}
    body = text.lstrip()
    end = body.find("\n---", 3)
    if end < 0:
        return {}
    block = body[3:end]
    fm: dict[str, str] = {}
    for line in block.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm


def main() -> int:
    failures = 0
    for case in CASES:
        print(f"\n=== {case['cli']} ===")
        with tempfile.TemporaryDirectory(prefix="ttk-smoke-") as td:
            tdp = Path(td)
            ok, log = run_install(case["cli"], tdp)
            if not ok:
                print("  [FAIL] init exited non-zero")
                print(log[-500:])
                failures += 1
                continue

            installed = tdp / case["expected_skill_path"]
            if not installed.exists():
                print(f"  [FAIL] expected file not created: {case['expected_skill_path']}")
                for p in tdp.rglob("SKILL.md"):
                    print(f"    -> instead found: {p.relative_to(tdp)}")
                failures += 1
                continue

            content = installed.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)

            if fm.get("name") != case["expected_frontmatter_name"]:
                print(
                    f"  [FAIL] frontmatter name mismatch: "
                    f"expected '{case['expected_frontmatter_name']}', "
                    f"got '{fm.get('name')}'"
                )
                failures += 1
                continue

            if case["must_not_contain"] and case["must_not_contain"] in content:
                print(
                    f"  [FAIL] SKILL.md still contains '{case['must_not_contain']}'"
                )
                failures += 1
                continue

            if case["must_contain"] not in content:
                print(
                    f"  [FAIL] SKILL.md missing expected phrase '{case['must_contain']}'"
                )
                failures += 1
                continue

            print(f"  [OK] writes to {case['expected_skill_path']}")
            print(f"  [OK] frontmatter name={fm.get('name')}")

    if failures:
        print(f"\n{failures} smoke test(s) failed")
        return 1
    print("\nAll smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
