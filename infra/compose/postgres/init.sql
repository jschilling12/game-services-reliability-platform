CREATE TABLE IF NOT EXISTS queue (
  id          BIGSERIAL    PRIMARY KEY,
  player_id   TEXT         NOT NULL,
  rank        INTEGER      NOT NULL,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS queue_rank_idx ON queue (rank);

CREATE TABLE IF NOT EXISTS matches (
  id          UUID         PRIMARY KEY,
  player_a    TEXT         NOT NULL,
  player_b    TEXT         NOT NULL,
  status      TEXT         NOT NULL DEFAULT 'pending',
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
