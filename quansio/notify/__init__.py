"""quansio-notify: durable attention/notification delivery (canonical owner).

Notification delivery and receipt tracking are owned by the
``quansio-notify`` service. The service derives notifications from canonical
events, delivers idempotently with expiry, tracks receipts (delivery and
acknowledgement) and never owns approval or task-state authority.
"""
