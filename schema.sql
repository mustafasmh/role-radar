CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'applied',
    job_description TEXT,
    job_url TEXT,
    applied_date DATE,
    notes TEXT,
    ai_draft TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- single-row table holding your base resume/profile — this feeds every AI draft
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    resume_text TEXT NOT NULL DEFAULT ''
);
INSERT OR IGNORE INTO profile (id, resume_text) VALUES (1, '');