---
name: Feature Request
about: Propose a new feature or an improvement to an existing one
title: "feat: <short description of the feature>"
labels: ["enhancement", "needs-triage"]
assignees: []
---

<!--
  Thank you for suggesting an improvement to TakeTakeTake!
  Please fill in every relevant section below.
  Incomplete proposals may be closed or deprioritised.
-->

## Summary

<!--
  One clear sentence describing the feature.
  Focus on the *outcome*, not the implementation.

  Good:  "Allow the user to export the current board position as a FEN string."
  Avoid: "Add a to_fen() method to GameTree."
-->


## Motivation / Problem Statement

<!--
  Why is this feature needed?
  Describe the concrete use case or pain point it addresses.
  If this is related to an existing issue or discussion, link it here.
-->


## Proposed Solution

<!--
  Describe your preferred solution in as much detail as you have.
  If you have a specific API in mind, show a usage example.
  If you are unsure about the implementation, just describe the desired behaviour.
-->

### Example usage (optional)

```python
# If the feature involves a public API, show how you'd like to use it.
from taketaketake import ...

```

## Alternatives Considered

<!--
  Have you considered any other approaches?
  Why do you prefer the proposed solution over them?
-->


## Affected Module(s)

<!--
  Which part(s) of the codebase would this feature touch?
  Select all that apply and delete the rest.
-->

- [ ] `engine.py` — chess logic
- [ ] `tree.py` — move tree / data structures
- [ ] `pgn.py` — PGN parser / serialiser
- [ ] `app.py` — GUI
- [ ] `constants.py` — colours, symbols, NAG
- [ ] `__main__.py` — CLI
- [ ] `tests/` — test suite
- [ ] `.github/` — CI / workflows
- [ ] `docs/` — documentation only

## Acceptance Criteria

<!--
  List the conditions that must be true for this feature to be considered done.
  Written as testable statements where possible.
-->

- [ ] 
- [ ] 
- [ ] 

## Additional Context

<!--
  Screenshots, mockups, links to similar implementations in other projects,
  relevant PGN examples, or anything else that helps clarify the request.
-->


## Checklist

- [ ] I have searched the [existing issues](../../issues) and this is not a duplicate.
- [ ] This feature does not require any external (non-stdlib) dependency.
- [ ] I am willing to implement this feature myself and open a pull request.
      *(Not required — feel free to leave unchecked if you are just proposing.)*
