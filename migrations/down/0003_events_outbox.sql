-- 0003 (down)
BEGIN;
DROP TABLE IF EXISTS event_outbox;
DROP TABLE IF EXISTS event_cursors;
DROP TABLE IF EXISTS runtime_events;
COMMIT;
