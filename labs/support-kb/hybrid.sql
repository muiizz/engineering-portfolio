\set ON_ERROR_STOP on
BEGIN;
\ir catalog.sql

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
