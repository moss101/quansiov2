# Validation Report

**Schema revision:** `9.0.0`

**Tasks:** 135  
**Requirements:** 111  
**Schemas:** 43  
**Dependency edges:** 338

## Executed authority checks

### `validate_contracts.py`

Exit code: `0`

```text
CONTRACT VALIDATION: PASS (43 schemas, 43 valid and 43 invalid fixtures)
```

### `validate_authority.py`

Exit code: `0`

```text
AUTHORITY VALIDATION: PASS (135 tasks, 111 requirements, 43 schemas, 338 dependency edges)
```

### `self_test_validators.py`

Exit code: `0`

```text
VALIDATOR SELF-TEST: PASS
```

## Integrity model

`MANIFEST.json` hashes every payload file except the four integrity/reporting artifacts that would create circularity: `MANIFEST.json`, `V9_SPECIFICATION_SEAL.md`, `VALIDATION_REPORT.md`, and `CHECKSUMS.sha256`. The specification seal binds the manifest digest. `CHECKSUMS.sha256` covers every package file except itself. `scripts/validate_integrity.py` enforces exact coverage, digests, sizes and seal counts.

The packaging pipeline runs `validate_integrity.py` after writing the manifest, seal and checksums. Its executed result is emitted by the finalization command rather than embedded here, so the report bytes remain stable after sealing.
