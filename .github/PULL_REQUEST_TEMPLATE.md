<!--
  Thank you for contributing to TakeTakeTake!
  Please fill in this template before requesting a review.
  Delete any section that is not applicable to your change.
-->

## Summary

<!--
  One paragraph describing *what* this PR changes and *why*.
  Link the related issue if one exists.

  Closes #<issue-number>
-->


## Type of Change

<!--
  Place an `x` inside the boxes that apply.
-->

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `refactor` — code change without behaviour change
- [ ] `test` — adding or updating tests only
- [ ] `docs` — documentation only
- [ ] `chore` — build scripts, CI, configuration
- [ ] `perf` — performance improvement
- [ ] `style` — formatting / whitespace

## What Changed

<!--
  Bullet-point list of the notable changes.
  Keep it concise — the diff is always available.
-->

- 
- 

## How to Test Manually

<!--
  Step-by-step instructions to verify the change works as intended.
  Include a PGN snippet or move sequence if the fix is chess-logic related.
-->

1. 
2. 
3. 

## Screenshots (if UI changed)

<!--
  Before / after screenshots help reviewers understand visual changes quickly.
  Delete this section if the PR does not touch the GUI.
-->

| Before | After |
|--------|-------|
| <!-- screenshot --> | <!-- screenshot --> |

## Checklist

### Code quality
- [ ] The code follows the style guidelines described in `CONTRIBUTING.md`.
- [ ] All public functions and classes have docstrings and type annotations.
- [ ] No new external (non-stdlib) dependencies have been introduced.
- [ ] `pyflakes` reports no errors on the changed files.

### Tests
- [ ] All existing tests pass: `python -m pytest tests/ -v`
- [ ] New behaviour is covered by at least one new test.
- [ ] Edge cases and failure paths are tested where relevant.

### Documentation
- [ ] `CHANGELOG.md` has been updated under `[Unreleased]`.
- [ ] `README.md` has been updated if user-facing behaviour changed.
- [ ] Inline comments are clear and necessary (not just paraphrasing the code).

### Git hygiene
- [ ] The branch is rebased on the latest `develop` (not `main`).
- [ ] Commits follow the Conventional Commits format described in `CONTRIBUTING.md`.
- [ ] There are no merge commits in the branch history.
- [ ] Temporary debug code, `print()` statements, and commented-out blocks have been removed.

## Breaking Changes

<!--
  Does this PR change any public API, CLI behaviour, or PGN file format
  compatibility in a way that could break existing users?

  If yes, describe what breaks and what the migration path is.
  If no, delete this section or write "None".
-->

None.

## Additional Notes for Reviewers

<!--
  Anything you want reviewers to pay special attention to, known limitations,
  design decisions you are unsure about, or follow-up work planned.
-->
