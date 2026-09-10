# Quansio V9 Specification Seal

**Schema revision:** `9.0.0`  
**Manifest SHA-256:** `45a48be5df2dce81e667b369b12e02aa4dc7e9382a7bf8c068a3e762a3a2f381`  
**Canonical tasks:** 135  
**Normative requirements:** 111  
**Canonical schemas:** 43  
**Dependency edges:** 338

This seal binds the exact non-circular authority payload listed by `MANIFEST.json`. The manifest excludes itself, this seal, `VALIDATION_REPORT.md` and `CHECKSUMS.sha256`. `CHECKSUMS.sha256` then covers every package file except itself.
