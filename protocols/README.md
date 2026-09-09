# Canonical protocol rules

All canonical envelopes use `schema_revision = "9.0.0"`. Unknown or omitted revisions are rejected at the canonical boundary. Compatibility adapters, if ever required for an actually deployed consumer, live only in the existing owning service, are explicit and time-bounded, and may never invent absent capability, policy, approval, budget, generation or provenance fields.
