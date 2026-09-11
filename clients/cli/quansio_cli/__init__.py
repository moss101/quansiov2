"""Quansio packaged command-line client (UX-008).

Thin projection over canonical server APIs: the CLI authenticates against
quansio-api, submits admitted commands, reads run state and canonical events
from quansio-runtime, answers scoped approvals in quansio-control and looks
up artifacts in quansio-artifact. It owns no execution, model, effect or
task authority locally; its only durable state is the session token and the
last-seen event cursor.
"""
