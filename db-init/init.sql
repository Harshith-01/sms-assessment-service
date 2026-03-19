-- Assessment service bootstrap SQL
-- Assessment domain tables are maintained through shared schema migrations.
-- Keep this file for deployment consistency.

BEGIN;

-- No-op marker to keep migration runners happy.
SELECT 1;

COMMIT;
