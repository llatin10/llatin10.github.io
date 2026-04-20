# Firebender “OnDemand specific tests” prompt (copy/paste)

Use this prompt in **Android Studio → Firebender Agent** to generate the exact string to paste into the GitHub Actions workflow field:

> **Run specific test class pattern(s), comma-separated. Takes precedence over testTag.**

This is meant for developers who **do not use Cursor** and **do not have** `/on-demand-specific-test-run`.

---

## Instructions for the agent (copy/paste everything below)

You are helping me run **OnDemand specific tests** in the repo **mobile-tests**.

### Goal
Given one or more test names/descriptions/keywords I provide, find the matching **Kotlin test class name(s)** under `src/test/kotlin` and output:

1) A **single copy-paste line** for the GitHub Actions field **Run specific test class pattern(s)**, formatted as:
- comma-separated list of `*ClassName` entries
- no quotes
- no `--tests` flags
- dedupe classes (if several matches map to the same class, output it once)

2) A **verification table**:

| # | Description | Test class | Evidence |
|---|-------------|------------|----------|

Where **Evidence** is either:
- file path + the matching `fun \`...\`` line, or
- file path + the matching `@ParameterizedTest(name = \"...\")` line.

### How to search (manual, local repo)
Search only under `src/test/kotlin` for these patterns:
- Backtick test titles: `fun \`...\`(`  (Kotlin functions with backtick names)
- Parameterized display templates: `@ParameterizedTest(name = \"...\")`

When you find a match, open that `.kt` file and extract the **top-level test class name**, e.g.:
- `class DepositChequeTest`
- `class ToggleBiometricTest`

### Output format (STRICT)
First output exactly this section:

**Copy-paste line**
```text
*FirstTestClass,*SecondTestClass
```

Then the table:

| # | Description | Test class | Evidence |
|---|-------------|------------|----------|
| 1 | ... | ... | `src/test/kotlin/.../File.kt` — `fun \`...\`(` |

### No match rule
If you cannot find a match for an input, include a row with:
- Test class: `No match found`
- Evidence: what you searched for (keywords/pattern)
Do **not** include it in the copy-paste line.

### Reminder
The GitHub Actions field **Run specific test class pattern(s)** takes precedence over `testTag` for which tests run.

---

## My inputs (I will fill these)

Paste the test names/descriptions/keywords below, one per line:

- <TEST 1>
- <TEST 2>
- <TEST 3>

