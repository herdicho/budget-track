-- Create categories table
CREATE TABLE IF NOT EXISTS public.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    name TEXT UNIQUE NOT NULL,
    emoji TEXT NOT NULL DEFAULT '📦',
    color TEXT NOT NULL DEFAULT '#ff5555'
);

-- Create payment_sources table
CREATE TABLE IF NOT EXISTS public.payment_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL DEFAULT 'bank' -- 'bank', 'ewallet', 'cash'
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    merchant TEXT NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    category TEXT NOT NULL REFERENCES public.categories(name) ON UPDATE CASCADE,
    payment_source TEXT NOT NULL REFERENCES public.payment_sources(name) ON UPDATE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    user_name TEXT NOT NULL DEFAULT 'Suami', -- 'Suami' atau 'Istri'
    items JSONB DEFAULT '[]'::jsonb,
    receipt_url TEXT,
    transfer_to TEXT REFERENCES public.payment_sources(name) ON UPDATE CASCADE -- Tujuan transfer jika category = 'Transfer'
);

-- Create budgets table
CREATE TABLE IF NOT EXISTS public.budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    month TEXT UNIQUE NOT NULL, -- Format YYYY-MM (e.g. "2026-06")
    amount NUMERIC(12, 2) NOT NULL,
    income NUMERIC(12, 2) NOT NULL DEFAULT 0.00 -- Pendapatan bulanan
);

-- Insert a default budget and income for the current month (5,000,000 IDR budget, 0.00 income)
INSERT INTO public.budgets (month, amount, income)
VALUES (to_char(CURRENT_DATE, 'YYYY-MM'), 5000000.00, 0.00)
ON CONFLICT (month) DO NOTHING;

-- Seed default payment sources
INSERT INTO public.payment_sources (name, type) VALUES
('Cash', 'cash'),
('BCA', 'bank'),
('Mandiri', 'bank'),
('Gopay', 'ewallet'),
('OVO', 'ewallet'),
('ShopeePay', 'ewallet')
ON CONFLICT (name) DO NOTHING;

-- Seed default categories
INSERT INTO public.categories (name, emoji, color) VALUES
('Makanan', '🍔', '#ff79c6'),
('Transportasi', '🚗', '#8be9fd'),
('Kebutuhan Bulanan', '🛒', '#50fa7b'),
('Kebutuhan Bayi', '👶', '#ffb86c'),
('Hiburan', '🎬', '#bd93f9'),
('Transfer', '🔄', '#0ea5e9'),
('Pendapatan', '💰', '#50fa7b'),
('Lain-lain', '📦', '#ff5555')
ON CONFLICT (name) DO NOTHING;
