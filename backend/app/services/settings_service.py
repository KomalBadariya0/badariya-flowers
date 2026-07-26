from sqlalchemy.orm import Session

from app.models.settings import SiteSettings
from app.schemas.settings import SettingsRead, SettingsUpdate


def to_read(row: SiteSettings) -> SettingsRead:
    return SettingsRead(
        websiteName=row.website_name,
        tagline=row.tagline,
        logo=row.logo_url,
        favicon=row.favicon_url,
        websiteStatus=row.website_status,
        maintenanceMode=row.maintenance_mode,
        businessName=row.business_name,
        ownerName=row.owner_name,
        mobileNumber=row.mobile_number,
        whatsappNumber=row.whatsapp_number,
        businessEmail=row.business_email,
        mapLink=row.map_link,
        googleMapsEmbed=row.google_maps_embed,
        address=row.address,
        city=row.city,
        state=row.state,
        country=row.country,
        pincode=row.pincode,
        businessHours=row.business_hours,
        currency=row.currency,
        language=row.language,
        defaultProductImage=row.default_product_image_url,
        productsPerPage=row.products_per_page,
        defaultWaMessage=row.default_wa_message,
        facebook=row.facebook,
        instagram=row.instagram,
        youtube=row.youtube,
        twitter=row.twitter,
        pinterest=row.pinterest,
        linkedin=row.linkedin,
        footerCopyright=row.footer_copyright,
        footerAddress=row.footer_address,
        footerPhone=row.footer_phone,
        footerEmail=row.footer_email,
        footerWhatsapp=row.footer_whatsapp,
        metaTitle=row.meta_title,
        metaDescription=row.meta_description,
        metaKeywords=row.meta_keywords,
        ogImage=row.og_image_url,
        googleAnalyticsId=row.google_analytics_id,
        facebookPixelId=row.facebook_pixel_id,
        robotsTxt=row.robots_txt,
        canonicalUrl=row.canonical_url,
        heroTitle=row.hero_title,
        heroSubtitle=row.hero_subtitle,
        heroButtonText=row.hero_button_text,
        heroButtonLink=row.hero_button_link,
        heroBgImage=row.hero_bg_image_url,
        supportEmail=row.support_email,
        supportPhone=row.support_phone,
        adminName=row.admin_name,
        adminEmail=row.admin_email,
        updatedAt=row.updated_at,
    )


def get_or_create(db: Session) -> SiteSettings:
    row = db.query(SiteSettings).filter(SiteSettings.id == 1).first()
    if row:
        return row
    row = SiteSettings(id=1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


_FIELD_MAP = {
    "websiteName": "website_name",
    "tagline": "tagline",
    "logo": "logo_url",
    "favicon": "favicon_url",
    "websiteStatus": "website_status",
    "maintenanceMode": "maintenance_mode",
    "businessName": "business_name",
    "ownerName": "owner_name",
    "mobileNumber": "mobile_number",
    "whatsappNumber": "whatsapp_number",
    "businessEmail": "business_email",
    "mapLink": "map_link",
    "googleMapsEmbed": "google_maps_embed",
    "address": "address",
    "city": "city",
    "state": "state",
    "country": "country",
    "pincode": "pincode",
    "businessHours": "business_hours",
    "currency": "currency",
    "language": "language",
    "defaultProductImage": "default_product_image_url",
    "productsPerPage": "products_per_page",
    "defaultWaMessage": "default_wa_message",
    "facebook": "facebook",
    "instagram": "instagram",
    "youtube": "youtube",
    "twitter": "twitter",
    "pinterest": "pinterest",
    "linkedin": "linkedin",
    "footerCopyright": "footer_copyright",
    "footerAddress": "footer_address",
    "footerPhone": "footer_phone",
    "footerEmail": "footer_email",
    "footerWhatsapp": "footer_whatsapp",
    "metaTitle": "meta_title",
    "metaDescription": "meta_description",
    "metaKeywords": "meta_keywords",
    "ogImage": "og_image_url",
    "googleAnalyticsId": "google_analytics_id",
    "facebookPixelId": "facebook_pixel_id",
    "robotsTxt": "robots_txt",
    "canonicalUrl": "canonical_url",
    "heroTitle": "hero_title",
    "heroSubtitle": "hero_subtitle",
    "heroButtonText": "hero_button_text",
    "heroButtonLink": "hero_button_link",
    "heroBgImage": "hero_bg_image_url",
    "supportEmail": "support_email",
    "supportPhone": "support_phone",
    "adminName": "admin_name",
    "adminEmail": "admin_email",
}

def update_settings(db: Session, payload: SettingsUpdate) -> SiteSettings:
    row = get_or_create(db)
    data = payload.model_dump(exclude_unset=True)
    for camel_key, value in data.items():
        column = _FIELD_MAP.get(camel_key)
        if column and value is not None:
            setattr(row, column, value)
    db.commit()
    db.refresh(row)
    return row
