from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from app.database.base import Base


class SiteSettings(Base):
    """
    Singleton table — the application only ever reads/writes the row with
    id=1 (see SettingsService.get_or_create). One row is simpler and safer
    than a generic key/value table for a small, fixed set of fields that
    both the admin panel and the customer website read from.
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # General
    website_name = Column(String(150), nullable=False, default="Badariya Flowers")
    tagline = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    website_status = Column(String(20), nullable=False, default="active")  # active | inactive
    maintenance_mode = Column(Boolean, nullable=False, default=False)

    # Business Information
    business_name = Column(String(150), nullable=True)
    owner_name = Column(String(150), nullable=True)
    mobile_number = Column(String(30), nullable=True)
    whatsapp_number = Column(String(30), nullable=True)
    business_email = Column(String(150), nullable=True)
    map_link = Column(String(500), nullable=True)
    google_maps_embed = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    business_hours = Column(Text, nullable=True)

    # Website Settings
    currency = Column(String(10), nullable=False, default="INR")
    language = Column(String(10), nullable=False, default="en")
    default_product_image_url = Column(String(500), nullable=True)
    products_per_page = Column(Integer, nullable=False, default=12)
    default_wa_message = Column(Text, nullable=True)

    # Social Links
    facebook = Column(String(500), nullable=True)
    instagram = Column(String(500), nullable=True)
    youtube = Column(String(500), nullable=True)
    twitter = Column(String(500), nullable=True)
    pinterest = Column(String(500), nullable=True)
    linkedin = Column(String(500), nullable=True)

    # Footer
    footer_copyright = Column(String(255), nullable=True)
    footer_address = Column(Text, nullable=True)
    footer_phone = Column(String(30), nullable=True)
    footer_email = Column(String(150), nullable=True)
    footer_whatsapp = Column(String(30), nullable=True)

    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(255), nullable=True)
    og_image_url = Column(String(500), nullable=True)
    google_analytics_id = Column(String(100), nullable=True)
    facebook_pixel_id = Column(String(100), nullable=True)
    robots_txt = Column(String(50), nullable=True, default="index, follow")
    canonical_url = Column(String(500), nullable=True)

    # Home Page
    hero_title = Column(String(255), nullable=True)
    hero_subtitle = Column(String(500), nullable=True)
    hero_button_text = Column(String(100), nullable=True)
    hero_button_link = Column(String(500), nullable=True)
    hero_bg_image_url = Column(String(500), nullable=True)

    # Contact
    support_email = Column(String(150), nullable=True)
    support_phone = Column(String(30), nullable=True)

    # Security tab profile fields (password change has no backend yet —
    # intentionally no password_hash column here, see project notes)
    admin_name = Column(String(150), nullable=True)
    admin_email = Column(String(150), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())