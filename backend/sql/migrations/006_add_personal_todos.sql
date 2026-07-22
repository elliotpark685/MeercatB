-- The application ORM uses DB_SCHEMA=meerkat_pjt (not PostgreSQL's public schema).
CREATE TABLE IF NOT EXISTS meerkat_pjt.todos (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES meerkat_pjt.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    due_date DATE NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_todos_user_id ON meerkat_pjt.todos(user_id);
CREATE INDEX IF NOT EXISTS ix_todos_due_date ON meerkat_pjt.todos(due_date);
