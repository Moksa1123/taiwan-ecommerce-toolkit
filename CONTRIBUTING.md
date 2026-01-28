# Contributing

Thank you for your interest in contributing to Taiwan Invoice Skills.

## How to Contribute

### Reporting Issues

- Use [GitHub Issues](../../issues) to report bugs or suggest features.
- Include steps to reproduce the issue, expected behavior, and actual behavior.
- For API-related issues, specify which provider (ECPay, SmilePay, or Amego) is affected.

### Submitting Changes

1. Fork the repository.
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes.
4. Test your changes with the included test scripts:
   ```bash
   python taiwan-invoice/scripts/test-invoice-amounts.py
   ```
5. Commit with a clear message:
   ```bash
   git commit -m "Add: description of your change"
   ```
6. Push and open a Pull Request.

### Commit Message Convention

Use the following prefixes:

- `Add:` new feature or file
- `Fix:` bug fix
- `Update:` improvement to existing feature
- `Remove:` removed feature or file
- `Docs:` documentation only change
- `Refactor:` code change that neither fixes a bug nor adds a feature

### Code Style

- TypeScript examples should follow standard TypeScript conventions.
- Python scripts should follow PEP 8.
- Markdown files should use consistent heading levels and no trailing whitespace.
- Do not use emoji in any files.

### API Reference Updates

When updating API reference documents in `taiwan-invoice/references/`:

- Verify changes against the official provider documentation.
- Include the date of verification.
- Update all three platform copies (`.claude/skills/`, `.cursor/skills/`, `.agent/skills/`).

### Skill Definition Updates

When modifying `taiwan-invoice/SKILL.md`:

- Keep the file under 500 lines.
- Ensure YAML frontmatter fields are valid for all supported platforms.
- Test that the skill loads correctly on at least one platform.

## Project Structure

```
taiwan-invoice/          # Source of truth
.claude/skills/          # Claude Code (auto-discovered)
.cursor/skills/          # Cursor (auto-discovered, also reads .claude/skills/)
.agent/skills/           # Google Antigravity (auto-discovered)
```

Changes should be made to `taiwan-invoice/` first, then synced to platform directories.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
