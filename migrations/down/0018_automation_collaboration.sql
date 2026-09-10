-- 0018 (down)
BEGIN;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS room_messages;
DROP TABLE IF EXISTS room_participants;
DROP TABLE IF EXISTS collaborator_rooms;
DROP TABLE IF EXISTS automation_occurrences;
DROP TABLE IF EXISTS automations;
COMMIT;
