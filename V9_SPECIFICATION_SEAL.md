# Quansio V9 Specification Seal

**Schema revision:** `9.0.0`  
**Manifest SHA-256:** `44497f8b5eee247290676c4cc84953c24b14bc68b303932e7634cc8620437614`  
**Canonical tasks:** 135  
**Normative requirements:** 111  
**Canonical schemas:** 43  
**Dependency edges:** 338

This seal binds the exact non-circular authority payload listed by `MANIFEST.json`. The manifest excludes itself, this seal, `VALIDATION_REPORT.md` and `CHECKSUMS.sha256`. `CHECKSUMS.sha256` then covers every package file except itself.
