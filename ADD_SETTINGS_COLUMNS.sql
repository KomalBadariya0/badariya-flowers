-- Run this once against your MySQL database (badariya_flowers by default).
-- Base.metadata.create_all() only creates tables that don't exist yet — it
-- will NOT add new columns to the `settings` table that's already there
-- from before this update. Run this so the new admin Settings page
-- (/admin/settings) has somewhere to save its new fields.
-- Safe to re-run: each statement only adds a column that doesn't exist yet.

ALTER TABLE settings ADD COLUMN tagline VARCHAR(255) NULL;
ALTER TABLE settings ADD COLUMN google_maps_embed TEXT NULL;
ALTER TABLE settings ADD COLUMN city VARCHAR(100) NULL;
ALTER TABLE settings ADD COLUMN state VARCHAR(100) NULL;
ALTER TABLE settings ADD COLUMN country VARCHAR(100) NULL;
ALTER TABLE settings ADD COLUMN pincode VARCHAR(20) NULL;
ALTER TABLE settings ADD COLUMN business_hours TEXT NULL;
ALTER TABLE settings ADD COLUMN twitter VARCHAR(500) NULL;

ALTER TABLE settings ADD COLUMN meta_title VARCHAR(255) NULL;
ALTER TABLE settings ADD COLUMN meta_description VARCHAR(500) NULL;
ALTER TABLE settings ADD COLUMN meta_keywords VARCHAR(255) NULL;
ALTER TABLE settings ADD COLUMN og_image_url VARCHAR(500) NULL;
ALTER TABLE settings ADD COLUMN google_analytics_id VARCHAR(100) NULL;
ALTER TABLE settings ADD COLUMN facebook_pixel_id VARCHAR(100) NULL;
ALTER TABLE settings ADD COLUMN robots_txt VARCHAR(50) NULL DEFAULT 'index, follow';
ALTER TABLE settings ADD COLUMN canonical_url VARCHAR(500) NULL;

ALTER TABLE settings ADD COLUMN hero_title VARCHAR(255) NULL;
ALTER TABLE settings ADD COLUMN hero_subtitle VARCHAR(500) NULL;
ALTER TABLE settings ADD COLUMN hero_button_text VARCHAR(100) NULL;
ALTER TABLE settings ADD COLUMN hero_button_link VARCHAR(500) NULL;
ALTER TABLE settings ADD COLUMN hero_bg_image_url VARCHAR(500) NULL;

ALTER TABLE settings ADD COLUMN support_email VARCHAR(150) NULL;
ALTER TABLE settings ADD COLUMN support_phone VARCHAR(30) NULL;
