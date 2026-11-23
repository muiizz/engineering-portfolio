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
