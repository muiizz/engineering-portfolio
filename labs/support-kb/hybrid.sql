\set ON_ERROR_STOP on
BEGIN;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE support_kb_lab (
  slug text PRIMARY KEY,
  answer text NOT NULL,
  terms tsvector NOT NULL,
  embedding vector(4) NOT NULL
);
INSERT INTO support_kb_lab VALUES
 ('receipts','Open Trips, select your booking, then choose Receipts.',
  to_tsvector('simple','receipt invoice rasid رسید'), '[1,0,0,0]'),
 ('hours','The support desk is open from 09:00 to 17:00 UTC.',
  to_tsvector('simple','hours schedule waqt اوقات'), '[0,1,0,0]'),
 ('itinerary','Open Trips and choose your booking to view its itinerary.',
  to_tsvector('simple','itinerary confirmation ticket ٹکٹ'), '[0,0,1,0]'),
 ('account','Open Settings and choose Account.',
  to_tsvector('simple','account profile settings'), '[0,0,0,1]');
CREATE INDEX ON support_kb_lab USING gin(terms);
CREATE INDEX ON support_kb_lab USING hnsw(embedding vector_cosine_ops);

CREATE TEMP TABLE retrieval_results AS
WITH cases(id, phrase, embedding, expected) AS (VALUES
 (1,'invoice','[1,0,0,0]'::vector,'receipts'),
 (2,'rasid','[1,0,0,0]'::vector,'receipts'),
 (3,'رسید','[1,0,0,0]'::vector,'receipts'),
 (4,'opening times','[0,1,0,0]'::vector,'hours'),
 (5,'itinerary','[0,0,1,0]'::vector,'itinerary'),
 (6,'profile','[0,0,0.8,0.2]'::vector,'account')
)
SELECT c.id, c.expected,
 (SELECT slug FROM support_kb_lab WHERE terms @@ plainto_tsquery('simple',c.phrase)
  ORDER BY ts_rank(terms,plainto_tsquery('simple',c.phrase)) DESC,slug LIMIT 1) AS keyword,
 (SELECT slug FROM support_kb_lab ORDER BY embedding <=> c.embedding,slug LIMIT 1) AS vector
FROM cases c;

SELECT count(*) AS cases, count(*) FILTER (WHERE keyword=expected) AS keyword_hits,
 count(*) FILTER (WHERE vector=expected) AS vector_hits,
 count(*) FILTER (WHERE coalesce(keyword,vector)=expected) AS hybrid_hits
FROM retrieval_results;
DO $$
BEGIN
  IF (SELECT count(*) FROM retrieval_results WHERE keyword=expected) <> 5
     OR (SELECT count(*) FROM retrieval_results WHERE vector=expected) <> 5
     OR EXISTS (SELECT FROM retrieval_results WHERE coalesce(keyword,vector) IS DISTINCT FROM expected)
  THEN RAISE EXCEPTION 'unexpected retrieval scores'; END IF;
END;
$$;
ROLLBACK;
