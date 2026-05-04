SELECT current_database();
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'meerkat_pjt';

SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'meerkat_pjt'
ORDER BY table_name;

SELECT COUNT(*) FROM meerkat_pjt.law_documents;
SELECT COUNT(*) FROM meerkat_pjt.law_articles;
SELECT COUNT(*) FROM meerkat_pjt.law_embeddings;

