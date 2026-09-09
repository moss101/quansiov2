# 11 — Quansio for Business: Business Capability Packs

A Business Capability Pack is a deployable, versioned, evaluated enterprise capability. It is intentionally broader than a skill.

Required composition:
- authoritative knowledge requirements
- qualified skills
- typed tool and connector requirements
- role and permission requirements
- credential-handle requirements
- policies and approval rules
- WorkGraph/workflow templates
- input/output contracts
- evidence requirements
- evaluation cases and mandatory thresholds
- compatibility, migration, deprecation and rollback policy

## Capability Compiler

```text
Authoritative docs / SOPs / policies / APIs / process definitions
Permissions / schemas / successful-work evidence
                  |
                  v
        semantic decomposition
        process reconstruction
        candidate skill resolution
        tool/connector binding
        RBAC + policy + approval binding
        workflow compilation
        evaluation generation
        compatibility analysis
                  |
                  v
          Candidate Capability Pack
                  |
             qualification
                  |
                  v
          Published Capability Pack
```

The compiler does not execute production work. Published packs resolve into canonical WorkGraph, SkillPackage, ToolOperation, CapabilitySnapshot, PolicyDecision, approvals, effects and evidence at runtime.
