import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    AGENT = "AGENT"
    USER = "USER"


class PropertyType(str, enum.Enum):
    APARTMENT = "APARTMENT"
    VILLA = "VILLA"
    PENTHOUSE = "PENTHOUSE"
    DUPLEX = "DUPLEX"
    TOWNHOUSE = "TOWNHOUSE"
    LAND = "LAND"
    COMMERCIAL = "COMMERCIAL"
    OFFICE = "OFFICE"


class ListingType(str, enum.Enum):
    SALE = "SALE"
    RENT = "RENT"
    SHORT_TERM_RENT = "SHORT_TERM_RENT"


class PropertyStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    UNDER_OFFER = "UNDER_OFFER"
    SOLD = "SOLD"
    ARCHIVED = "ARCHIVED"


class Currency(str, enum.Enum):
    EUR = "EUR"
    USD = "USD"
    TRY = "TRY"
    GBP = "GBP"
    RUB = "RUB"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    role = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="user", uselist=False)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(Text)
    avatar_url = Column(String)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    languages = Column(String, default="en")  # comma-separated
    specialties = Column(String, default="")  # comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="agent")
    properties = relationship("Property", back_populates="agent")


class District(Base):
    __tablename__ = "districts"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String)

    neighborhoods = relationship("Neighborhood", back_populates="district")
    properties = relationship("Property", back_populates="district")


class Neighborhood(Base):
    __tablename__ = "neighborhoods"

    id = Column(String, primary_key=True)
    district_id = Column(String, ForeignKey("districts.id"), nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)

    district = relationship("District", back_populates="neighborhoods")
    properties = relationship("Property", back_populates="neighborhood")


class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    district_id = Column(String, ForeignKey("districts.id"))
    neighborhood_id = Column(String, ForeignKey("neighborhoods.id"), nullable=True)

    type = Column(SAEnum(PropertyType), nullable=False)
    listing_type = Column(SAEnum(ListingType), nullable=False)
    status = Column(SAEnum(PropertyStatus), default=PropertyStatus.DRAFT, nullable=False)

    title_en = Column(String, nullable=False)
    title_tr = Column(String)
    title_de = Column(String)
    description_en = Column(Text)
    description_tr = Column(Text)
    description_de = Column(Text)

    price = Column(Float, nullable=False)
    currency = Column(SAEnum(Currency), default=Currency.EUR)
    size_sqm = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    floor = Column(Integer)
    total_floors = Column(Integer)
    address = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    has_pool = Column(Boolean, default=False)
    has_parking = Column(Boolean, default=False)
    is_furnished = Column(Boolean, default=False)
    has_garden = Column(Boolean, default=False)
    has_security = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    has_balcony = Column(Boolean, default=False)
    has_terrace = Column(Boolean, default=False)
    eligible_for_citizenship = Column(Boolean, default=False)

    view_count = Column(Integer, default=0)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="properties")
    district = relationship("District", back_populates="properties")
    neighborhood = relationship("Neighborhood", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property", order_by="PropertyImage.sort_order")
    inquiries = relationship("Inquiry", back_populates="property")

    @property
    def cover_image(self):
        for img in self.images:
            if img.is_cover:
                return img
        return self.images[0] if self.images else None

    @property
    def title(self):
        return self.title_en

    @property
    def formatted_price(self):
        symbols = {"EUR": "€", "USD": "$", "TRY": "₺", "GBP": "£", "RUB": "₽"}
        symbol = symbols.get(self.currency.value if hasattr(self.currency, 'value') else self.currency, "€")
        return f"{symbol}{int(self.price):,}"


class PropertyImage(Base):
    __tablename__ = "property_images"

    id = Column(String, primary_key=True)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    url = Column(String, nullable=False)
    is_cover = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    property = relationship("Property", back_populates="images")


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(String, primary_key=True)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="inquiries")
