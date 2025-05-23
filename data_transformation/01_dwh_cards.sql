DROP TABLE IF EXISTS dwh_cards;

CREATE TABLE dwh_cards (
  card_type TEXT,
  card_name TEXT,
  card_url TEXT
);

INSERT INTO dwh_cards (card_type, card_name, card_url)
SELECT DISTINCT card_type, card_name, card_url
FROM wrk_decklists;