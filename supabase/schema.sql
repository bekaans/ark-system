-- ARK Intelligence - Supabase semasi
-- Bu dosyayi Supabase SQL Editor'a yapistirip calistir.
-- 5 tablo: sectors, businesses, audits, leads, conversations

create extension if not exists "pgcrypto";

-- 1) sectors: NACE tabanli sektor puanlama
create table if not exists sectors (
  id uuid primary key default gen_random_uuid(),
  nace_code text not null,
  name text not null,
  opportunity_score numeric,
  cpc numeric,
  business_volume int,
  digital_weakness_ratio numeric,
  weight numeric default 1.0,       -- haftalik kalibrasyonla guncellenir (S4/40)
  created_at timestamptz not null default now()
);

-- 2) businesses: toplanan isletmeler (Google Maps scraper)
create table if not exists businesses (
  id uuid primary key default gen_random_uuid(),
  place_id text unique,              -- mukerrer kontrolu
  sector_id uuid references sectors(id),
  name text not null,
  city text,
  address text,
  phone text,
  website text,
  created_at timestamptz not null default now()
);

-- 3) audits: site denetim sonuclari
create table if not exists audits (
  id uuid primary key default gen_random_uuid(),
  business_id uuid references businesses(id) not null,
  has_animation boolean default false,   -- GSAP/Three.js tespiti
  has_meta_pixel boolean default false,
  has_gtag boolean default false,
  seo_score numeric,
  lighthouse_score numeric,
  screenshot_url text,
  audited_at timestamptz not null default now()
);

-- 4) leads: skorlanmis lead'ler + tier
create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  business_id uuid references businesses(id) not null,
  sector_id uuid references sectors(id),
  lead_score numeric,
  tier text check (tier in ('A', 'B', 'C')),        -- on-satis: isletme/firsat degeri tier'i
  estimated_deal_value numeric,
  status text not null default 'new'
    check (status in ('new','contacted','qualified','meeting','proposal','won','lost')),
  outreach_draft text,
  -- dm-qualifier yanit gecikme durumu (mirroring - musteri hizina gore ayarlanir)
  response_stage int not null default 1,             -- 1=60-90sn, 2=stage1-20sn, 3=10-15sn
  last_delay_seconds numeric,
  -- sohbet-ici satisa-gecme tier'i (leads.tier'den BAGIMSIZ, konusma ilerledikce guncellenir)
  sales_tier text check (sales_tier in ('S','A','B','C','D')),  -- S = satis/kapanis
  sales_tier_score numeric,
  -- SEO 2.0 "ilk ay ucretsiz" hediyesi bir musteriye SADECE BIR KEZ verilir
  seo_gift_given boolean not null default false,
  -- NocoBase kanban panelinde surukle-birak siralamasi icin (s3-6)
  kanban_sort bigint,
  created_at timestamptz not null default now()
);

-- 5) conversations: dm-qualifier mesaj gecmisi + token yakalama
create table if not exists conversations (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references leads(id) not null,
  channel text check (channel in ('whatsapp','instagram')),
  direction text check (direction in ('inbound','outbound')),
  message text,
  token text check (token in ('APPOINTMENT','HUMAN', null)),
  created_at timestamptz not null default now()
);

-- 6) scrape_progress: s1-7 surekli-calisan dongu - hangi (sektor,sehir) tarandi
create table if not exists scrape_progress (
  id uuid primary key default gen_random_uuid(),
  sector_code text not null,
  city text not null,
  status text not null default 'pending' check (status in ('pending','done')),
  scraped_at timestamptz,
  created_at timestamptz not null default now(),
  unique (sector_code, city)
);

-- Indeksler (siklikla sorgulanacak alanlar)
create index if not exists idx_businesses_sector on businesses(sector_id);
create index if not exists idx_audits_business on audits(business_id);
create index if not exists idx_leads_business on leads(business_id);
create index if not exists idx_leads_status on leads(status);
create index if not exists idx_conversations_lead on conversations(lead_id);
create index if not exists idx_scrape_progress_status on scrape_progress(status);

-- Row Level Security: varsayilan olarak KAPALI erisim.
-- Backend ajanlari (server-side) service_role key ile RLS'i atlar - bu normal ve guvenlidir.
-- Publishable/anon key ile hicbir client bu tablolara dogrudan erisemez (politika eklenmedikce).
alter table sectors enable row level security;
alter table businesses enable row level security;
alter table audits enable row level security;
alter table leads enable row level security;
alter table conversations enable row level security;
alter table scrape_progress enable row level security;
