-- ARK - Migration 007: businesses.instagram alani + website'i aslinda
-- Instagram linki olan kayitlardan otomatik backfill.
-- SADECE bu dosyayi SQL Editor'a yapistir, eski scriptleri tekrar calistirma.

alter table businesses
  add column if not exists instagram text;

update businesses
set instagram = website
where instagram is null
  and website ilike '%instagram.com%';
