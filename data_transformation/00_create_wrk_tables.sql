-- Suppression des tables si elles existent
DROP TABLE IF EXISTS wrk_tournaments;
DROP TABLE IF EXISTS wrk_decklists;
DROP TABLE IF EXISTS fin_decklists;

-- Création de la table wrk_tournaments
CREATE TABLE wrk_tournaments (
  tournament_id TEXT NULL,
  tournament_name TEXT NULL,
  tournament_date TEXT NULL,  
  tournament_organizer TEXT NULL,
  tournament_format TEXT NULL,
  tournament_nb_players INTEGER NULL
);

-- Création de la table wrk_decklists
CREATE TABLE wrk_decklists (
  tournament_id TEXT NULL,
  player_id TEXT NULL,
  card_type TEXT NULL,
  card_name TEXT NULL,
  card_url TEXT NULL,
  card_count INTEGER NULL
);


-- Création de la table wrk_decklists
CREATE TABLE fin_decklists (
  tournament_id TEXT NULL,
  player_id TEXT NULL,
  card_type TEXT NULL,
  card_name TEXT NULL,
  card_url TEXT NULL,
  card_count INTEGER NULL,
  extension text null
);