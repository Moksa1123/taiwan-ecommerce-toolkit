#!/usr/bin/env python3
"""
Test script to verify taiwan-invoice CLI installation works for all platforms.

Usage:
    python test-install.py              # Test all platforms
    python test-install.py claude       # Test specific platform
    python test-install.py --offline    # Test with offline mode
"""

import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path

# All supported platforms
PLATFORMS = [
    'claude',
    'cursor',
    'windsurf',
    'copilot',
    'antigravity',
    'kiro',
    'codex',
    'qoder',
    'roocode',
    'gemini',
    'trae',
    'opencode',
    'continue',
    'codebuddy',
]

# Expected files after installation
EXPECTED_FILES = [
    'SKILL.md',
    'EXAMPLES.md',
    'references/ECPAY_API_REFERENCE.md',
    'references/SMILEPAY_API_REFERENCE.md',
    'references/AMEGO_API_REFERENCE.md',
    'scripts/generate-invoice-service.py',
    'scripts/test-invoice-amounts.py',
]

def get_install_path(platform: str, base_dir: str) -> str:
    """Get the expected installation path for a platform."""
    paths = {
        'claude': '.claude/skills/taiwan-invoice',
        'cursor': '.cursor/skills/taiwan-invoice',
        'windsurf': '.windsurf/skills/taiwan-invoice',
        'copilot': '.github/copilot/skills/taiwan-invoice',
        'antigravity': '.agent/skills/taiwan-invoice',
        'kiro': '.kiro/skills/taiwan-invoice',
        'codex': '.codex/skills/taiwan-invoice',
        'qoder': '.qodo/skills/taiwan-invoice',
        'roocode': '.roo/skills/taiwan-invoice',
        'gemini': '.gemini/skills/taiwan-invoice',
        'trae': '.trae/skills/taiwan-invoice',
        'opencode': '.opencode/skills/taiwan-invoice',
        'continue': '.continue/skills/taiwan-invoice',
        'codebuddy': '.codebuddy/skills/taiwan-invoice',
    }
    return os.path.join(base_dir, paths.get(platform, ''))


def test_platform(platform: str, cli_path: str, offline: bool = False) -> tuple[bool, str]:
    """Test installation for a single platform."""
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Build command
            cmd = ['node', cli_path, 'init', '--ai', platform, '--force']
            if offline:
                cmd.append('--offline')

            # Run installation
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return False, f"CLI returned error: {result.stderr}"

            # Check expected files
            install_path = get_install_path(platform, temp_dir)

            if not os.path.exists(install_path):
                return False, f"Install path not found: {install_path}"

            missing_files = []
            for expected_file in EXPECTED_FILES:
                file_path = os.path.join(install_path, expected_file)
                if not os.path.exists(file_path):
                    missing_files.append(expected_file)

            if missing_files:
                return False, f"Missing files: {', '.join(missing_files)}"

            # Check SKILL.md has content
            skill_path = os.path.join(install_path, 'SKILL.md')
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) < 1000:
                    return False, f"SKILL.md seems too small ({len(content)} bytes)"
                if 'taiwan-invoice' not in content.lower():
                    return False, "SKILL.md doesn't contain expected content"

            return True, "OK"

        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, str(e)


def main():
    # Parse arguments
    platforms_to_test = PLATFORMS
    offline = '--offline' in sys.argv

    # Check for specific platform
    for arg in sys.argv[1:]:
        if arg in PLATFORMS:
            platforms_to_test = [arg]
            break

    # Find CLI path
    script_dir = Path(__file__).parent.parent
    cli_path = script_dir / 'dist' / 'index.js'

    if not cli_path.exists():
        print("[ERROR] CLI not built. Run 'npm run build' first.")
        sys.exit(1)

    print("=" * 60)
    print("Taiwan Invoice CLI Installation Test")
    print("=" * 60)
    print(f"CLI Path: {cli_path}")
    print(f"Offline Mode: {offline}")
    print(f"Platforms: {len(platforms_to_test)}")
    print("=" * 60)
    print()

    results = []

    for platform in platforms_to_test:
        print(f"Testing {platform}...", end=' ', flush=True)
        success, message = test_platform(platform, str(cli_path), offline)
        results.append((platform, success, message))

        if success:
            print(f"[OK]")
        else:
            print(f"[FAIL] {message}")

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")

    if failed > 0:
        print()
        print("Failed platforms:")
        for platform, success, message in results:
            if not success:
                print(f"  - {platform}: {message}")
        sys.exit(1)
    else:
        print()
        print("[OK] All platforms passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
