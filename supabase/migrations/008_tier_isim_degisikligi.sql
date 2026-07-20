-- ARK - Migration 008: leads.tier ve leads.sales_tier icin harf-tabanli
-- isimler (A/B/C, S/A/B/C/D) yerine tanimlayici Turkce isimler.
-- SADECE bu dosyayi SQL Editor'a yapistir, eski scriptleri tekrar calistirma.
--
-- Sebep: yeni website urun tier'i (B/A/S/S+) ile leads.tier/sales_tier
-- harfleri karisiyordu (bkz. README.md tier yeniden adlandirma notu,
-- 2026-07-19). Mapping:
--   leads.tier:        A->eski_sistem, B->ortalama, C->iyi
--   leads.sales_tier:  S->potansiyel_musteri, A->potansiyel_olabilir,
--                      B->soguk_satis, C->kararsiz, D->sadece_merak
--
-- Eski CHECK kisitlarinin otomatik-uretilen adini varsaymak yerine, mevcut
-- kisitlari pg_constraint uzerinden bulup dinamik olarak kaldiriyoruz -
-- boylece Postgres surumune/adlandirma farkina bagli kalmiyoruz.

do $$
declare
  con record;
begin
  for con in
    select conname
    from pg_constraint
    where conrelid = 'leads'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) ilike '%tier%'
  loop
    execute format('alter table leads drop constraint %I', con.conname);
  end loop;
end $$;

update leads set tier = case tier
  when 'A' then 'eski_sistem'
  when 'B' then 'ortalama'
  when 'C' then 'iyi'
  else tier
end
where tier in ('A', 'B', 'C');

update leads set sales_tier = case sales_tier
  when 'S' then 'potansiyel_musteri'
  when 'A' then 'potansiyel_olabilir'
  when 'B' then 'soguk_satis'
  when 'C' then 'kararsiz'
  when 'D' then 'sadece_merak'
  else sales_tier
end
where sales_tier in ('S', 'A', 'B', 'C', 'D');

alter table leads add constraint leads_tier_check
  check (tier in ('eski_sistem', 'ortalama', 'iyi'));

alter table leads add constraint leads_sales_tier_check
  check (sales_tier in ('sadece_merak', 'kararsiz', 'soguk_satis', 'potansiyel_olabilir', 'potansiyel_musteri'));
