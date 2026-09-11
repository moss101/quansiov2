# Quansio V9 Specification Seal

**Schema revision:** `9.0.0`  
**Manifest SHA-256:** `3c17c5e0a27ad2b58c686abd093483c4802cba13a7912751139707422d49cdd1`  
**Canonical tasks:** 135  
**Normative requirements:** 111  
**Canonical schemas:** 43  
**Dependency edges:** 338

This seal binds the exact non-circular authority payload listed by `MANIFEST.json`. The manifest excludes itself, this seal, `VALIDATION_REPORT.md` and `CHECKSUMS.sha256`. `CHECKSUMS.sha256` then covers every package file except itself.
