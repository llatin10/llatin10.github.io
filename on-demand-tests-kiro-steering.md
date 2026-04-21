# Kiro Steering File — OnDemand specific tests (copy/paste)

Use this steering file in **Kiro** to generate the exact string to paste into the GitHub Actions workflow field:

> **Run specific test class pattern(s), comma-separated. Takes precedence over testTag.**

This is meant for developers who use **Kiro** and **do not have** the `#on-demand-specific-test-run` steering file yet.

---

## Setup instructions

1. Create the file `~/.kiro/steering/on-demand-specific-test-run.md`
2. Copy and paste **everything in the block below** into that file
3. In Kiro chat, type `#on-demand-specific-test-run` followed by your test names

---

## Steering file content (copy/paste everything below into `~/.kiro/steering/on-demand-specific-test-run.md`)

```markdown
---
inclusion: manual
---

Generate the exact string to paste into the **Run specific test(s)** field of the GitHub workflow `run-specific-tests.yml`, plus a verification table.

## Canonical paths

- **Script (test index + lookup):** `~/.kiro/imports from cursor/version-prep/scripts/extract_test_index.py`

## Input

**Ask the user for test name(s)** if not already provided. Accept:
- Full test description
- Partial name or keywords
- One test per line or comma-separated list

## Steps

1. **Resolve each test to a test class**

   **A. Index (preferred)**:
   ```bash
   python3 ~/.kiro/imports\ from\ cursor/version-prep/scripts/extract_test_index.py --repo /Users/llatin/mobile-tests
   ```
   Then for each fragment:
   ```bash
   python3 ~/.kiro/imports\ from\ cursor/version-prep/scripts/extract_test_index.py --repo /Users/llatin/mobile-tests --find "partial description"
   ```

   **B. Fallback** — If `--find` returns no matches, search `mobile-tests/src/test/kotlin` for Kotlin test files matching the description.

2. **Build the copy-paste line**
   - Format: comma-separated `*ClassName` entries (no quotes, no `--tests` flags)
   - Example: `*DepositChequeTest,*ToggleBiometricTest`
   - **Dedupe** classes when several failures map to the same class

3. **Build the verification table**

| # | Description | Test class |
|---|-------------|------------|
| 1 | User-provided test name | ClassNameTest |

## Output format

1. **Copy-paste line** (fenced code block):
```
*FirstTestClass,*SecondTestClass
```

2. **Verification table** (as above)

3. **Short note**: paste the line into the **Run specific test(s)** field in `run-specific-tests.yml`.

## Workspace

- If workspace is **mobile-tests**, use that repo for `--repo`.
- Otherwise use `/Users/llatin/mobile-tests` as the default.

## Rules

- One test class per test; if one class has multiple matching methods, one entry is enough.
- If a name matches no test, say so in the table and omit from the copy-paste line.
- Keep the copy-paste line as a **single line**, no line breaks.
```

---

## How to use in Kiro

Once the file is in place, type in Kiro chat:

```
#on-demand-specific-test-run
Mobility - mobility request - Joint Account
downgrade from existing plan
Dashboard - balances list - open banking is not connected - navigation
```

Kiro will look up each test name, resolve it to the correct Kotlin class, and output a ready-to-paste line + verification table.

---

## See also

- [On-demand tests — GitHub Actions guide](https://llatin10.github.io/on-demand-tests.html)
- [Firebender prompt (Android Studio)](https://llatin10.github.io/on-demand-tests-firebender-prompt.md)
