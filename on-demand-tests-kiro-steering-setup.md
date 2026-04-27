# Kiro Steering File Setup — OnDemand specific tests

This guide shows how to set up the `#on-demand-specific-test-run` steering file in your own Kiro installation.

## What is this?

A **Kiro steering file** that automates finding test class names for the GitHub Actions `run-specific-tests.yml` workflow. Instead of manually searching for test classes, just type:

```
#on-demand-specific-test-run
Mobility - mobility request - Joint Account
downgrade from existing plan
```

And Kiro will output the ready-to-paste line for GitHub Actions.

---

## Setup Instructions

### Step 1: Create the steering file

Create a new file at:

```
~/.kiro/steering/on-demand-specific-test-run.md
```

### Step 2: Copy this content

Copy the entire content below and paste it into that file:

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

### Step 3: Customize paths (if needed)

If your team uses a different path for `mobile-tests` or `extract_test_index.py`, update those paths in the file.

### Step 4: Use it

In Kiro chat, type:

```
#on-demand-specific-test-run
Test name 1
Test name 2
Test name 3
```

Kiro will automatically resolve them to class names and output the copy-paste line.

---

## Example Usage

**Input:**
```
#on-demand-specific-test-run
Mobility - mobility request - Joint Account
downgrade from existing plan
Dashboard - balances list - open banking is not connected - navigation
upgrade from existing plan
```

**Output:**
```
*MobilityFullFlowJointAccountTest,*DowngradeFromExistingPlanTest,*DashboardBalancesListOpenBankingIsNotConnectedNavigationTest,*UpgradeFromExistingPlanTest
```

| # | Description | Test class |
|---|-------------|------------|
| 1 | Mobility - mobility request - Joint Account | MobilityFullFlowJointAccountTest |
| 2 | downgrade from existing plan | DowngradeFromExistingPlanTest |
| 3 | Dashboard - balances list - open banking is not connected - navigation | DashboardBalancesListOpenBankingIsNotConnectedNavigationTest |
| 4 | upgrade from existing plan | UpgradeFromExistingPlanTest |

Then paste the first line into GitHub Actions **Run specific test(s)** field.

---

## See Also

- [On-demand tests — GitHub Actions guide](https://llatin10.github.io/on-demand-tests.html)
- [Firebender prompt (Android Studio)](https://llatin10.github.io/on-demand-tests-firebender-prompt.html)
- [Kiro Steering File — OnDemand specific tests](https://llatin10.github.io/on-demand-tests-kiro-steering.html)
