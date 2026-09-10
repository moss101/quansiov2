# Quansio V9 Specification Seal

**Schema revision:** `9.0.0`  
**Manifest SHA-256:** `d3f6182a8817b3a3c1c544f0213882e44034b3f13ccd2d0c287ec559ef3d4c53`  
**Canonical tasks:** 135  
**Normative requirements:** 111  
**Canonical schemas:** 43  
**Dependency edges:** 338

This seal binds the exact non-circular authority payload listed by `MANIFEST.json`. The manifest excludes itself, this seal, `VALIDATION_REPORT.md` and `CHECKSUMS.sha256`. `CHECKSUMS.sha256` then covers every package file except itself.
