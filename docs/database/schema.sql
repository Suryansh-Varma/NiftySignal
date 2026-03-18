-- Supabase PostgreSQL Schema for NiftySignal
-- Run this SQL in Supabase SQL Editor

-- Users table (handled by Supabase Auth, but we'll extend it)
create table public.user_profiles (
  id uuid references auth.users(id) on delete cascade not null,
  email text unique not null,
  full_name text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);

-- Portfolio table
create table public.portfolios (
  id uuid default gen_random_uuid() not null,
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null,
  description text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);

-- Portfolio positions (stocks in a portfolio)
create table public.portfolio_positions (
  id uuid default gen_random_uuid() not null,
  portfolio_id uuid references public.portfolios(id) on delete cascade not null,
  symbol text not null, -- e.g., "RELIANCE.NS"
  company_name text not null, -- e.g., "Reliance Industries"
  quantity integer not null,
  buy_price numeric(12, 2) not null,
  buy_date date not null,
  notes text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);

-- NIFTY universe (all valid companies)
create table public.nifty_universe (
  id uuid default gen_random_uuid() not null,
  symbol text unique not null, -- e.g., "RELIANCE.NS"
  company_name text not null, -- e.g., "Reliance Industries"
  sector text, -- e.g., "Energy"
  market_cap_cr bigint, -- In crores
  description text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);

-- Recent recommendations (imported from backend)
create table public.recommendations (
  id uuid default gen_random_uuid() not null,
  symbol text not null,
  company_name text not null,
  recommendation text not null, -- BUY, SELL, HOLD
  confidence numeric(5, 3),
  expected_return numeric(8, 4),
  risk_score numeric(5, 3),
  last_price numeric(10, 2),
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (id)
);

-- Enable RLS (Row Level Security)
alter table public.user_profiles enable row level security;
alter table public.portfolios enable row level security;
alter table public.portfolio_positions enable row level security;

-- RLS Policies
-- Users can only access their own profile
create policy "Users can view own profile"
  on public.user_profiles
  for select
  using ( auth.uid() = id );

create policy "Users can update own profile"
  on public.user_profiles
  for update
  using ( auth.uid() = id );

-- Users can only access their own portfolios
create policy "Users can view own portfolios"
  on public.portfolios
  for select
  using ( auth.uid() = user_id );

create policy "Users can insert own portfolios"
  on public.portfolios
  for insert
  with check ( auth.uid() = user_id );

create policy "Users can update own portfolios"
  on public.portfolios
  for update
  using ( auth.uid() = user_id );

create policy "Users can delete own portfolios"
  on public.portfolios
  for delete
  using ( auth.uid() = user_id );

-- Users can only access positions in their portfolios
create policy "Users can view own portfolio positions"
  on public.portfolio_positions
  for select
  using (
    portfolio_id in (
      select id from public.portfolios where user_id = auth.uid()
    )
  );

create policy "Users can insert positions in own portfolios"
  on public.portfolio_positions
  for insert
  with check (
    portfolio_id in (
      select id from public.portfolios where user_id = auth.uid()
    )
  );

-- Public tables (anyone can read)
create policy "Anyone can view NIFTY universe"
  on public.nifty_universe
  for select
  using ( true );

create policy "Anyone can view recommendations"
  on public.recommendations
  for select
  using ( true );

-- Create indexes for performance
create index user_profiles_email_idx on public.user_profiles(email);
create index portfolios_user_id_idx on public.portfolios(user_id);
create index portfolio_positions_portfolio_id_idx on public.portfolio_positions(portfolio_id);
create index nifty_universe_symbol_idx on public.nifty_universe(symbol);
create index recommendations_symbol_idx on public.recommendations(symbol);
