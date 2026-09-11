"""quansio-integration-broker: governed connector mediation and webhook
ingress (canonical owner).

The broker owns connector adapters, typed external operations and
authenticated idempotent webhook ingress. Connector operations run only
through credential handles issued by the scoped credential broker and only
over an authorized EffectRecord; reusable secret material never reaches
callers. The Tool Registry itself remains control-owned
(``quansio.control.connectors.ToolRegistry``).
"""
