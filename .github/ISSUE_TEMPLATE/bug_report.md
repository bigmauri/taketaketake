---
name: Bug Report
about: Report a reproducible defect in TakeTakeTake
title: "fix: <short description of the bug>"
labels: ["bug", "needs-triage"]
assignees: []
---

<!--
  Thank you for taking the time to report a bug!
  Please fill in every section below. Issues with insufficient
  information may be closed without investigation.
-->

## Summary

<!-- One or two sentences describing what goes wrong. -->


## Environment

| Field | Value |
|-------|-------|
| OS | <!-- e.g. Ubuntu 24.04 / Windows 11 / macOS 14 --> |
| Python version | <!-- python --version --> |
| TakeTakeTake version | <!-- check taketaketake/__init__.py or pip show taketaketake --> |
| tkinter version | <!-- python -c "import tkinter; print(tkinter.TkVersion)" --> |
| Installation method | <!-- pip install / editable (pip install -e .) / cloned directly --> |

## Steps to Reproduce

<!--
  List the exact steps needed to trigger the bug.
  Be as specific as possible — include PGN snippets, move sequences,
  or file paths where relevant.
-->

1. 
2. 
3. 

## Expected Behaviour

<!-- What should happen? -->


## Actual Behaviour

<!-- What actually happens? Include any error messages verbatim. -->


## Traceback / Error Output

<!--
  Paste the full traceback here (if any).
  Use a code block so it renders correctly.
-->

```
paste traceback here
```

## PGN or Move Sequence (if applicable)

<!--
  If the bug is triggered by a specific game or position, paste the PGN
  or the sequence of moves that reproduce it.
-->

```pgn
[Event "Bug reproduction"]
[White "?"]
[Black "?"]
[Result "*"]

* 
```

## Screenshots (if applicable)

<!-- Drag and drop images here, or delete this section if not needed. -->


## Additional Context

<!-- Any other information that might help — related issues, commit SHAs, etc. -->


## Checklist

- [ ] I have searched the [existing issues](../../issues) and this is not a duplicate.
- [ ] I can reproduce the bug on the latest commit of `develop`.
- [ ] I have included all information requested above.
