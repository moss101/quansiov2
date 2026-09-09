# 14 — Quansio Box execution architecture

## Target classes
- Hosted isolated task runtime
- Persistent workspace computer
- Local virtualized target when qualified
- Private worker target when qualified
- Personal endpoint relay

## Quansio Box
A hosted target is a tenant-bound microVM-class environment containing `qworkerd`, workspace mounts/artifact inputs, managed browser where required and deny-by-default networking. Credentials remain outside the guest where practical; scoped handles or mediated network/session injection are preferred.

```text
Runtime
  |
Worker Gateway -- authenticated envelope / ACK / cancellation
  |
Machine Control -- target / lease / generation / fence / snapshot
  |
Quansio Box
  |- qworkerd typed RPC
  |- filesystem / terminal / process
  |- managed browser / computer
  |- policy-controlled egress
  `- task-scoped capabilities only
```

## Lifecycle
`PROVISIONING → READY → LEASED → HIBERNATED/MIGRATING/UNHEALTHY → READY or TERMINATED`.

Placement must hold an exclusive lease and fence. Restore/migration invalidates stale actors through generation/fence changes.

## Checkpoints
Workspace snapshots occur more frequently than full-machine checkpoints. `RESTORABLE` is assigned only after every referenced state/artifact/snapshot object is durable and digest-verified. Warm pools and copy-on-write optimization are performance work after isolation/recovery correctness passes.
