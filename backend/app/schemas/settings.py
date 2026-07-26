from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

Status = Literal["active", "inactive"]
RobotsOption = Literal["index, follow", "noindex, nofollow", "index, nofollow", "noindex, follow"]


class SettingsUpdate(BaseModel):
    """All fields optional — PUT /api/settings (and POST /admin/settings)
    merge into the single existing row rather than requiring a full
    payload every time, even though both the old admin settings.js form
    and the new HTMX Settings page always submit their full field set."""

    # General
    websiteName: Optional[str] = Field(None, min_length=1, max_length=150)
    tagline: Optional[str] = None
    logo: Optional[str] = None
    favicon: Optional[str] = None
    websiteStatus: Optional[Status] = None
    maintenanceMode: Optional[bool] = None

    # Business Information
    businessName: Optional[str] = None
    ownerName: Optional[str] = None
    mobileNumber: Optional[str] = None
    whatsappNumber: Optional[str] = None
    businessEmail: Optional[EmailStr] = None
    mapLink: Optional[str] = None
    googleMapsEmbed: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    businessHours: Optional[str] = None

    # Website Settings
    currency: Optional[str] = None
    language: Optional[str] = None
    defaultProductImage: Optional[str] = None
    productsPerPage: Optional[int] = Field(None, ge=4, le=96)
    defaultWaMessage: Optional[str] = None

    # Social Links
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    youtube: Optional[str] = None
    twitter: Optional[str] = None
    pinterest: Optional[str] = None
    linkedin: Optional[str] = None

    # Footer
    footerCopyright: Optional[str] = None
    footerAddress: Optional[str] = None
    footerPhone: Optional[str] = None
    footerEmail: Optional[EmailStr] = None
    footerWhatsapp: Optional[str] = None

    # SEO
    metaTitle: Optional[str] = None
    metaDescription: Optional[str] = None
    metaKeywords: Optional[str] = None
    ogImage: Optional[str] = None
    googleAnalyticsId: Optional[str] = None
    facebookPixelId: Optional[str] = None
    robotsTxt: Optional[RobotsOption] = None
    canonicalUrl: Optional[str] = None

    # Home Page
    heroTitle: Optional[str] = None
    heroSubtitle: Optional[str] = None
    heroButtonText: Optional[str] = None
    heroButtonLink: Optional[str] = None
    heroBgImage: Optional[str] = None

    # Contact
    supportEmail: Optional[EmailStr] = None
    supportPhone: Optional[str] = None

    # Security (profile only — no password field here, see project notes)
    adminName: Optional[str] = None
    adminEmail: Optional[EmailStr] = None

    @field_validator("websiteName")
    @classmethod
    def not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Website name cannot be blank")
        return v.strip() if v else v


class SettingsRead(BaseModel):
    websiteName: str
    tagline: Optional[str] = None
    logo: Optional[str] = None
    favicon: Optional[str] = None
    websiteStatus: Status
    maintenanceMode: bool

    businessName: Optional[str] = None
    ownerName: Optional[str] = None
    mobileNumber: Optional[str] = None
    whatsappNumber: Optional[str] = None
    businessEmail: Optional[str] = None
    mapLink: Optional[str] = None
    googleMapsEmbed: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    businessHours: Optional[str] = None

    currency: str
    language: str
    defaultProductImage: Optional[str] = None
    productsPerPage: int
    defaultWaMessage: Optional[str] = None

    facebook: Optional[str] = None
    instagram: Optional[str] = None
    youtube: Optional[str] = None
    twitter: Optional[str] = None
    pinterest: Optional[str] = None
    linkedin: Optional[str] = None

    footerCopyright: Optional[str] = None
    footerAddress: Optional[str] = None
    footerPhone: Optional[str] = None
    footerEmail: Optional[str] = None
    footerWhatsapp: Optional[str] = None

    metaTitle: Optional[str] = None
    metaDescription: Optional[str] = None
    metaKeywords: Optional[str] = None
    ogImage: Optional[str] = None
    googleAnalyticsId: Optional[str] = None
    facebookPixelId: Optional[str] = None
    robotsTxt: Optional[str] = None
    canonicalUrl: Optional[str] = None

    heroTitle: Optional[str] = None
    heroSubtitle: Optional[str] = None
    heroButtonText: Optional[str] = None
    heroButtonLink: Optional[str] = None
    heroBgImage: Optional[str] = None

    supportEmail: Optional[str] = None
    supportPhone: Optional[str] = None

    adminName: Optional[str] = None
    adminEmail: Optional[str] = None

    updatedAt: datetime
