# tests

Result-compatibility tests against flutter_ilib (not added yet).

- Expected values are extracted from the flutter_ilib test suite
  (open-source expectations + webOS-specific expectations) into
  language-neutral data files, so Dart and Rust can share them.
- Acceptance criterion: identical strings (no normalization), for both the
  open-source data and the webOS data.
