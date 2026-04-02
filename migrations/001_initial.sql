-- Finance Dashboard: Initial Schema
-- Run this in Supabase SQL Editor

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- Users table
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer'
        CHECK (role IN ('viewer', 'analyst', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role ON users (role);

-- ============================================
-- Financial records table
-- ============================================
CREATE TABLE records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amount NUMERIC NOT NULL CHECK (amount > 0),
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    category TEXT NOT NULL,
    date DATE NOT NULL,
    notes TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_records_type ON records (type);
CREATE INDEX idx_records_category ON records (category);
CREATE INDEX idx_records_date ON records (date);
CREATE INDEX idx_records_user_id ON records (user_id);
CREATE INDEX idx_records_is_deleted ON records (is_deleted);

-- ============================================
-- Auto-update updated_at on row modification
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER records_updated_at
    BEFORE UPDATE ON records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- RPC functions for dashboard aggregations
-- ============================================

-- Summary: total income, total expenses, net balance
CREATE OR REPLACE FUNCTION get_financial_summary()
RETURNS TABLE (type TEXT, total NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT r.type, COALESCE(SUM(r.amount), 0) AS total
    FROM records r
    WHERE r.is_deleted = false
    GROUP BY r.type;
END;
$$ LANGUAGE plpgsql;

-- Category-wise totals
CREATE OR REPLACE FUNCTION get_category_totals()
RETURNS TABLE (category TEXT, type TEXT, total NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT r.category, r.type, COALESCE(SUM(r.amount), 0) AS total
    FROM records r
    WHERE r.is_deleted = false
    GROUP BY r.category, r.type
    ORDER BY total DESC;
END;
$$ LANGUAGE plpgsql;

-- Monthly trends
CREATE OR REPLACE FUNCTION get_monthly_trends(months_back INT DEFAULT 6)
RETURNS TABLE (period TEXT, income NUMERIC, expense NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT
        TO_CHAR(r.date, 'YYYY-MM') AS period,
        COALESCE(SUM(CASE WHEN r.type = 'income' THEN r.amount ELSE 0 END), 0) AS income,
        COALESCE(SUM(CASE WHEN r.type = 'expense' THEN r.amount ELSE 0 END), 0) AS expense
    FROM records r
    WHERE r.is_deleted = false
      AND r.date >= (CURRENT_DATE - (months_back || ' months')::INTERVAL)
    GROUP BY TO_CHAR(r.date, 'YYYY-MM')
    ORDER BY period ASC;
END;
$$ LANGUAGE plpgsql;

-- Weekly trends
CREATE OR REPLACE FUNCTION get_weekly_trends(weeks_back INT DEFAULT 12)
RETURNS TABLE (period TEXT, income NUMERIC, expense NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT
        TO_CHAR(DATE_TRUNC('week', r.date), 'YYYY-"W"IW') AS period,
        COALESCE(SUM(CASE WHEN r.type = 'income' THEN r.amount ELSE 0 END), 0) AS income,
        COALESCE(SUM(CASE WHEN r.type = 'expense' THEN r.amount ELSE 0 END), 0) AS expense
    FROM records r
    WHERE r.is_deleted = false
      AND r.date >= (CURRENT_DATE - (weeks_back || ' weeks')::INTERVAL)
    GROUP BY DATE_TRUNC('week', r.date)
    ORDER BY period ASC;
END;
$$ LANGUAGE plpgsql;

-- Category breakdown with percentages
CREATE OR REPLACE FUNCTION get_category_breakdown()
RETURNS TABLE (category TEXT, type TEXT, total NUMERIC, percentage NUMERIC) AS $$
BEGIN
    RETURN QUERY
    WITH totals AS (
        SELECT r.category, r.type, SUM(r.amount) AS total
        FROM records r
        WHERE r.is_deleted = false
        GROUP BY r.category, r.type
    ),
    grand_totals AS (
        SELECT t.type, SUM(t.total) AS grand_total
        FROM totals t
        GROUP BY t.type
    )
    SELECT
        t.category,
        t.type,
        t.total,
        ROUND((t.total / gt.grand_total) * 100, 2) AS percentage
    FROM totals t
    JOIN grand_totals gt ON t.type = gt.type
    ORDER BY t.type, t.total DESC;
END;
$$ LANGUAGE plpgsql;

-- Disable RLS for these tables (we handle auth in the application layer)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE records ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access on users"
    ON users FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on records"
    ON records FOR ALL
    USING (true)
    WITH CHECK (true);
