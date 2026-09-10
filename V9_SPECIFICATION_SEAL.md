# Quansio V9 Specification Seal

**Schema revision:** `9.0.0`  
**Manifest SHA-256:** `18867f54eb48853523b9163cfe3d5535c5f9589d0ee0ef585b702b561746ed03`  
**Canonical tasks:** 135  
**Normative requirements:** 111  
**Canonical schemas:** 43  
**Dependency edges:** 338

This seal binds the exact non-circular authority payload listed by `MANIFEST.json`. The manifest excludes itself, this seal, `VALIDATION_REPORT.md` and `CHECKSUMS.sha256`. `CHECKSUMS.sha256` then covers every package file except itself.
