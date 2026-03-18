-- Create portfolio table in Supabase
-- Run this SQL in your Supabase dashboard: https://app.supabase.com/project/_/editor

CREATE TABLE IF NOT EXISTS portfolios (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol VARCHAR(20) NOT NULL,
  company_name VARCHAR(100),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  buy_price DECIMAL(12, 2) NOT NULL CHECK (buy_price > 0),
  buy_date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster user portfolio lookups
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);

-- Enable Row Level Security
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own portfolio
CREATE POLICY "Users can view own portfolio" 
  ON portfolios FOR SELECT 
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own portfolio items
CREATE POLICY "Users can insert own portfolio" 
  ON portfolios FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own portfolio items
CREATE POLICY "Users can update own portfolio" 
  ON portfolios FOR UPDATE 
  USING (auth.uid() = user_id);

-- Policy: Users can delete their own portfolio items
CREATE POLICY "Users can delete own portfolio" 
  ON portfolios FOR DELETE 
  USING (auth.uid() = user_id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on row update
CREATE TRIGGER update_portfolios_updated_at
  BEFORE UPDATE ON portfolios
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
