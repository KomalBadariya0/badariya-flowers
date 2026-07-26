-- Run this once against your MySQL database (badariya_flowers by default).
-- Base.metadata.create_all() only creates tables that don't exist yet — it
-- will NOT alter an index on a table that's already there — so the old
-- UNIQUE index on products.seo_slug (the actual cause of the 500 error /
-- "Duplicate entry ... for key 'products.ix_products_seo_slug'") has to be
-- dropped manually. This replaces it with a normal (non-unique) index so
-- lookups by slug stay fast, but duplicate SEO slugs are allowed.

ALTER TABLE products DROP INDEX ix_products_seo_slug;
CREATE INDEX ix_products_seo_slug ON products (seo_slug);
