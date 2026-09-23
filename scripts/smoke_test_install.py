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
        "search": ["10000009", "--domain", "error"],
    },
    {
        "cli": "payment-cli",
        "expected_skill_path": ".claude/skills/taiwan-payment/SKILL.md",
        "expected_frontmatter_name": "taiwan-payment",
        "must_contain": "Taiwan Payment",
        "must_not_contain": "Taiwan E-Invoice",
        "search": ["10100058", "--domain", "error"],
    },
    {
        "cli": "logistics-cli",
        "expected_skill_path": ".claude/skills/taiwan-logistics/SKILL.md",
        "expected_frontmatter_name": "taiwan-logistics",
        "must_contain": "Taiwan Logistics",
        "must_not_contain": "Taiwan E-Invoice",
        "search": ["2067", "--domain", "status"],
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


# 只給開發者看的檔案，不隨 skill 安裝
NOT_INSTALLED = {"CLAUDE.md", "README.md"}


def missing_files(source: Path, installed: Path) -> list[str]:
    """source of truth 裡應安裝卻沒裝到的檔案（examples/、data/ 曾因此漏裝）"""
    out = []
    for f in sorted(source.rglob("*")):
        rel = f.relative_to(source)
        if f.is_file() and "__pycache__" not in rel.parts and str(rel) not in NOT_INSTALLED:
            if not (installed / rel).exists():
                out.append(rel.as_posix())
    return out


def run_search(skill_dir: Path, args: list[str]) -> tuple[bool, str]:
    """已安裝的 search.py 要讀得到 data/，且查得到結果"""
    proc = subprocess.run(
        [sys.executable, "scripts/search.py", *args],
        cwd=skill_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0 and args[0] in out and "查無結果" not in out, out


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

            skill_dir = installed.parent
            source = REPO / case["expected_frontmatter_name"]
            missing = missing_files(source, skill_dir)
            if missing:
                print(f"  [FAIL] {len(missing)} files not installed, e.g. {missing[:5]}")
                failures += 1
                continue

            ok, out = run_search(skill_dir, case["search"])
            if not ok:
                print(f"  [FAIL] installed search.py {' '.join(case['search'])}")
                print(out[-500:])
                failures += 1
                continue

            print(f"  [OK] writes to {case['expected_skill_path']}")
            print(f"  [OK] frontmatter name={fm.get('name')}")
            print("  [OK] all skill files installed; installed search.py works")

    if failures:
        print(f"\n{failures} smoke test(s) failed")
        return 1
    print("\nAll smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
