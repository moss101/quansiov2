# 21 — Canonical wiring

## Command to outcome
`Client → quansio-api → quansio-control/auth-policy → quansio-runtime → Context/Model/Tool/Machine owners → RuntimeEvent → client projections`

## Model
`runtime → context projection → budget/privacy/routing → model-gateway → provider adapter → ModelEvent → runtime`

## Research
`runtime → context → SearchProgram → retrieval/index/browser tools → ResearchRecord/evidence → Context Projection/artifact`

## External effect
`runtime/tool proposal → capability → policy/privacy/sequence → approval if required → EffectRecord → integration-broker/browser/machine → receipt/evidence → reconciliation`

## Machine
`runtime → worker-gateway → machine-control lease/generation/fence → qworkerd → typed result/ACK → runtime`

## Business capability
`authoritative material → Capability Compiler → candidate pack → evaluation/publish → runtime resolution → normal WorkGraph/skills/tools/policy/effects/evidence`

## Notifications
`canonical attention event → quansio-notify → delivery receipt`; approval decisions still update control/effect authority, not notification state.

See `wiring/service-wiring.json` for machine-readable producer/consumer boundaries.
