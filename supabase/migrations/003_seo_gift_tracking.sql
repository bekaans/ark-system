-- ARK - Migration 003: SEO 2.0 "ilk ay ucretsiz" hediyesinin tekrarini engelleme
-- SADECE bu dosyayi SQL Editor'a yapistir, eski scriptleri tekrar calistirma.

alter table leads
  add column if not exists seo_gift_given boolean not null default false;
