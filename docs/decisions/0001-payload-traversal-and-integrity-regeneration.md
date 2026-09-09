# ADR-0001: Payload traversal rules and integrity artifact regeneration

- **Status:** Accepted
- **Owner:** governance
- **Date:** 2026-09-10
- **Task context:** GOV-001, GOV-004, GOV-005

## Context

The sealed authority package was finalized before the repository was placed
under git (`git init` + push to github.com/moss101/quansiov2 happened after
sealing). `scripts/validate_integrity.py` and `scripts/finalize_package.py`
therefore traversed the whole tree without excluding VCS internals: `.git/**`
objects and `.gitignore` entered the coverage comparison and integrity
validation failed on any committed checkout. Additionally, `.git/**` contents
mutate on every git operation, so including them would make integrity
coverage non-deterministic. Independently, `scripts/validate_authority.py`
and `scripts/scan_production_placeholders.py` scanned `.venv/**` dependency
trees once a local project venv existed, producing false marker/term hits
against vendor code, and `scripts/self_test_validators.py` legitimately
embeds placeholder markers as test data.

## Decision

1. Introduce `tools/governance/repo_paths.py` as the single source of truth
   for payload traversal: VCS internals (`.git`, `.hg`, `.svn`), caches
   (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`), dependency
   and environment trees (`.venv`, `venv`, `node_modules`, `.tox`, `.eggs`)
   and build outputs (`dist`, `build`) are never authority payload.
2. `finalize_package.py` and `validate_integrity.py` traverse through
   `repo_paths`; manifest, checksums and seal were regenerated with the
   tooling (no hand-edited digests).
3. `validate_authority.py` term scans traverse payload files only.
4. The placeholder scanner gains an explicit, reason-class-checked exclusion
   list (`scripts/scan_exclusions.json`) that may only exclude paths of class
   `self_test`, `fixture`, `vendor` or `generated`; it registers the scanner
   itself (pattern literals) and the validator self-test (embedded markers).
5. The project virtual environment lives at `.venv/` and is never payload.

## Alternatives rejected

- Hand-strip `.git` after each operation: fragile, non-reproducible.
- Exclude only `.git` and keep ad-hoc rglob in each validator: three
  traversal implementations would drift; GOV-004 determinism requires one.
- Move the self-test markers out of the validator: weakens the authority's
  own adversarial self-coverage.

## Affected invariants

- None at the architectural-invariant level; canonical tasks (135),
  requirements (111), schemas (43) and dependency edges (338) are unchanged.
- Strengthens GOV-004 (deterministic generation) and GOV-005 (scan only the
  production tree) enforcement.

## Threat impact

Reduces false positives that would normalize scan failures (alert fatigue);
closes a hole where derived/vendor trees could mask missing production
coverage; keeps the seal binding an exact, reproducible payload.

## Migration / rollback

Regeneration is tool-executed and byte-deterministic. Rollback: revert
`tools/governance/repo_paths.py` and the two validator scripts, then rerun
`scripts/finalize_package.py`.

## Review trigger

Any change to packaging layout, introduction of new derived directories, or
CI build isolation work (doc 50) must re-evaluate the exclusion set.
