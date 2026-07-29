-- Subscription plan is separate from the administrative role.
BEGIN;

ALTER TABLE IF EXISTS meerkat_pjt.users
ADD COLUMN IF NOT EXISTS plan VARCHAR(20);

UPDATE meerkat_pjt.users
SET plan = 'free'
WHERE plan IS NULL;

ALTER TABLE meerkat_pjt.users
ALTER COLUMN plan SET DEFAULT 'free';

ALTER TABLE meerkat_pjt.users
ALTER COLUMN plan SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'users_plan_check'
          AND conrelid = 'meerkat_pjt.users'::regclass
    ) THEN
        ALTER TABLE meerkat_pjt.users
        ADD CONSTRAINT users_plan_check CHECK (plan IN ('free', 'premium'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_plan ON meerkat_pjt.users(plan);

COMMIT;
