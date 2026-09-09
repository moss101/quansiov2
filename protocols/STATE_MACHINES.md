# Canonical state-machine notes

Runtime graph/node, agent, effect, approval, machine, browser, automation and release states are explicit durable values. State transitions occur only through the owning service and are represented by canonical events. Retry is never modeled by silently reverting a committed state. Ambiguous consequential outcomes enter `UNKNOWN` reconciliation instead of speculative replay.
