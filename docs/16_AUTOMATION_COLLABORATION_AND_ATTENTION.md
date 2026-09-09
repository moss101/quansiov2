# 16 — Automations, collaboration and attention

## Automations
Schedules include timezone, local rule, DST gap/fold policy, missed-fire policy and logical fire identity. `CATCH_UP_BOUNDED` has explicit maximum. Every fire resolves current agent/capability/policy/support/target state; schedule creation does not freeze authority.

Pause/resume/delete serialize against scheduler claim. Scheduler restart uses durable fire history to prevent duplicate logical work.

## Collaboration
Collaboration is a projection over agents, messages, handoffs and WorkGraph turns. It does not own a second work scheduler. Typed handoffs carry sender/recipient, target work/turn, payload/artifact refs, capability context and delivery identity.

## Notifications
Notifications carry recipient, attention type, urgency, expiry/deep-link and delivery/ack state. Notification delivery never becomes approval truth; approval lives in the control/effect contract.
