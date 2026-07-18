-- ARK - Migration 006: leads.business_id icin UNIQUE kisit
-- SADECE bu dosyayi SQL Editor'a yapistir, eski scriptleri tekrar calistirma.
--
-- score_leads.py upsert(..., on_conflict="business_id") kullaniyor ama
-- business_id uzerinde sadece duz bir index vardi (UNIQUE degil) - Postgres
-- ON CONFLICT icin gercek bir UNIQUE/EXCLUSION kisiti sart kosuyor, bu yuzden
-- her calistirma "there is no unique or exclusion constraint matching the
-- ON CONFLICT specification" (42P10) hatasiyla cakiliyordu. Mevcut 2661
-- satirda mukerrer business_id olmadigi dogrulandi, kisit güvenle eklenebilir.

alter table leads add constraint leads_business_id_key unique (business_id);
