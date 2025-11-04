-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'caster', 'filer', 'setter', 'polisher')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
    id BIGSERIAL PRIMARY KEY,
    design_no VARCHAR(50) NOT NULL,
    item_category VARCHAR(50) NOT NULL,
    initial_weight DECIMAL(10, 3) NOT NULL CHECK (initial_weight > 0),
    total_loss DECIMAL(10, 3) DEFAULT 0.0,
    loss_percentage DECIMAL(5, 2) DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'in_progress', 'pending_assignment', 'completed', 'cancelled')),
    current_stage VARCHAR(20),
    current_worker_id BIGINT REFERENCES users(id),
    created_by BIGINT NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

-- Transactions table
CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    worker_id BIGINT NOT NULL REFERENCES users(id),
    stage VARCHAR(20) NOT NULL CHECK (stage IN ('casting', 'filing', 'setting', 'polishing')),
    issued_weight DECIMAL(10, 3) NOT NULL CHECK (issued_weight > 0),
    returned_weight DECIMAL(10, 3),
    loss DECIMAL(10, 3),
    loss_percentage DECIMAL(5, 2),
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    returned_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'cancelled')),
    notes TEXT
);

-- Indexes for performance
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_current_worker ON jobs(current_worker_id);
CREATE INDEX idx_transactions_job ON transactions(job_id);
CREATE INDEX idx_transactions_worker ON transactions(worker_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
