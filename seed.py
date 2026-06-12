"""Run once to populate the database with sample data."""
from app.database import SessionLocal, engine
from app import models
from app.models import (
    User, Agent, District, Neighborhood, Property, PropertyImage,
    UserRole, PropertyType, ListingType, PropertyStatus, Currency,
)
from app.utils.auth import hash_password
from app.utils.slugify import new_id, unique_slug
from datetime import datetime

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clear existing data
from app.models import Inquiry
for model in [Inquiry, PropertyImage, Property, Neighborhood, District, Agent, User]:
    db.query(model).delete()
db.commit()

# ── Districts ────────────────────────────────────────────────
districts_data = [
    ("Konyaaltı",   "konyaalti",  "Popular beachfront district west of city centre."),
    ("Lara",        "lara",       "Upscale area east of Antalya, known for beach resorts."),
    ("Kepez",       "kepez",      "Affordable inland district, fast-growing residential area."),
    ("Muratpaşa",   "muratpasa",  "City centre district with historical sites."),
    ("Altıntaş",    "altintas",   "New development zone near Antalya Airport."),
    ("Alanya",      "alanya",     "Coastal resort town 125 km east of Antalya."),
    ("Belek",       "belek",      "Luxury resort and golf tourism hub."),
    ("Kalkan",      "kalkan",     "Boutique coastal town popular with British buyers."),
]
districts = {}
for name, slug, desc in districts_data:
    d = District(id=new_id(), name=name, slug=slug, description=desc)
    db.add(d)
    districts[slug] = d
db.flush()

# ── Neighborhoods ────────────────────────────────────────────
neighborhoods_data = {
    "konyaalti": ["Hurma", "Sarısu", "Arapsuyu"],
    "lara":      ["Kundu", "Güzeloba", "Şirinyalı"],
    "altintas":  ["Aksu", "Gündoğdu"],
    "alanya":    ["Mahmutlar", "Kestel", "Oba"],
}
hoods = {}
for d_slug, names in neighborhoods_data.items():
    for n in names:
        h = Neighborhood(
            id=new_id(),
            district_id=districts[d_slug].id,
            name=n,
            slug=n.lower().replace(" ", "-"),
        )
        db.add(h)
        hoods[n] = h
db.flush()

# ── Users / Agents ───────────────────────────────────────────
agents_data = [
    ("mehmet@property-antalya.com", "Mehmet", "Yılmaz", "+905551234567",
     "Senior property consultant specialising in luxury villas and sea-view apartments.",
     ["tr", "en", "de"], ["luxury", "investment"]),
    ("ayse@property-antalya.com",   "Ayşe",   "Kaya",   "+905559876543",
     "Expert in new-build projects and citizenship-eligible investments.",
     ["tr", "en", "ru"], ["new-build", "citizenship"]),
    ("ali@property-antalya.com",    "Ali",    "Demir",  "+905557654321",
     "Specialist in affordable residential properties and rental investments.",
     ["tr", "en"],        ["rental", "residential"]),
]
agent_objs = []
for email, fn, ln, phone, bio, langs, specs in agents_data:
    u = User(
        id=new_id(), email=email,
        password_hash=hash_password("Agent123!"),
        first_name=fn, last_name=ln, phone=phone,
        role=UserRole.AGENT, is_active=True,
    )
    db.add(u)
    db.flush()
    a = Agent(
        id=new_id(), user_id=u.id, bio=bio,
        rating=4.8, review_count=12, is_verified=True,
        languages=",".join(langs), specialties=",".join(specs),
    )
    db.add(a)
    agent_objs.append(a)
db.flush()

# ── Properties ───────────────────────────────────────────────
props_data = [
    {
        "title_en": "Luxury Sea-View Apartment | 2+1 | Liman, Konyaaltı",
        "title_tr": "Lüks Deniz Manzaralı Daire | 2+1 | Liman, Konyaaltı",
        "type": PropertyType.APARTMENT, "listing_type": ListingType.SALE,
        "status": PropertyStatus.ACTIVE,
        "price": 285000, "currency": Currency.EUR,
        "size_sqm": 100, "bedrooms": 2, "bathrooms": 1, "floor": 4, "total_floors": 8,
        "district": "konyaalti", "neighborhood": "Hurma",
        "description_en": "Stunning sea-view apartment in a premium complex with pool, 5 min walk to Konyaaltı Beach. Fully furnished, ready to move in.",
        "has_pool": True, "has_parking": True, "is_furnished": True, "has_balcony": True, "has_elevator": True,
        "eligible_for_citizenship": False,
        "agent_idx": 0,
    },
    {
        "title_en": "New Build 3+1 | Citizenship Eligible | Altıntaş near Airport",
        "title_tr": "Yeni Bina 3+1 | Vatandaşlığa Uygun | Altıntaş",
        "type": PropertyType.APARTMENT, "listing_type": ListingType.SALE,
        "status": PropertyStatus.ACTIVE,
        "price": 420000, "currency": Currency.EUR,
        "size_sqm": 131, "bedrooms": 3, "bathrooms": 2, "floor": 5, "total_floors": 14,
        "district": "altintas", "neighborhood": "Aksu",
        "description_en": "Brand new off-plan apartment 5 minutes from Antalya Airport. Qualifies for Turkish citizenship by investment.",
        "has_pool": True, "has_parking": True, "has_security": True, "has_elevator": True,
        "has_balcony": True, "eligible_for_citizenship": True,
        "agent_idx": 1,
    },
    {
        "title_en": "Beachfront Villa with Private Pool | Lara",
        "title_tr": "Özel Havuzlu Sahil Villası | Lara",
        "type": PropertyType.VILLA, "listing_type": ListingType.SALE,
        "status": PropertyStatus.ACTIVE,
        "price": 1250000, "currency": Currency.EUR,
        "size_sqm": 380, "bedrooms": 5, "bathrooms": 4, "floor": 1, "total_floors": 3,
        "district": "lara", "neighborhood": "Kundu",
        "description_en": "Exceptional beachfront villa with direct beach access, private heated pool and stunning Mediterranean views.",
        "has_pool": True, "has_parking": True, "is_furnished": True, "has_garden": True,
        "has_security": True, "has_terrace": True, "eligible_for_citizenship": True,
        "agent_idx": 0,
    },
    {
        "title_en": "Modern Studio | Short-Term Rental | City Centre",
        "title_tr": "Modern Stüdyo | Kısa Dönem Kiralık | Şehir Merkezi",
        "type": PropertyType.APARTMENT, "listing_type": ListingType.SHORT_TERM_RENT,
        "status": PropertyStatus.ACTIVE,
        "price": 800, "currency": Currency.EUR,
        "size_sqm": 45, "bedrooms": 1, "bathrooms": 1, "floor": 2, "total_floors": 6,
        "district": "muratpasa", "neighborhood": None,
        "description_en": "Fully equipped studio apartment in the heart of Antalya old city. Perfect for short stays.",
        "is_furnished": True, "has_elevator": True, "has_balcony": True,
        "eligible_for_citizenship": False,
        "agent_idx": 2,
    },
    {
        "title_en": "Golf Resort Penthouse | Belek",
        "title_tr": "Golf Tatil Köyü Çatı Katı | Belek",
        "type": PropertyType.PENTHOUSE, "listing_type": ListingType.SALE,
        "status": PropertyStatus.ACTIVE,
        "price": 695000, "currency": Currency.EUR,
        "size_sqm": 210, "bedrooms": 3, "bathrooms": 3, "floor": 8, "total_floors": 8,
        "district": "belek", "neighborhood": None,
        "description_en": "Spectacular penthouse overlooking Belek golf course. Wrap-around terrace with panoramic sea and green views.",
        "has_pool": True, "has_parking": True, "is_furnished": True,
        "has_security": True, "has_elevator": True, "has_terrace": True,
        "eligible_for_citizenship": True,
        "agent_idx": 1,
    },
    {
        "title_en": "Investment Apartment | High Rental Yield | Alanya",
        "title_tr": "Yatırım Dairesi | Yüksek Kira Getirisi | Alanya",
        "type": PropertyType.APARTMENT, "listing_type": ListingType.SALE,
        "status": PropertyStatus.ACTIVE,
        "price": 165000, "currency": Currency.EUR,
        "size_sqm": 65, "bedrooms": 2, "bathrooms": 1, "floor": 3, "total_floors": 7,
        "district": "alanya", "neighborhood": "Mahmutlar",
        "description_en": "Great investment opportunity in Mahmutlar. High rental yield, 300m to beach, managed complex.",
        "has_pool": True, "has_parking": True, "has_elevator": True, "has_balcony": True,
        "eligible_for_citizenship": False,
        "agent_idx": 2,
    },
]

for pd in props_data:
    agent = agent_objs[pd.pop("agent_idx")]
    d_slug = pd.pop("district")
    n_name = pd.pop("neighborhood")
    p = Property(
        id=new_id(),
        slug=unique_slug(pd["title_en"]),
        agent_id=agent.id,
        district_id=districts[d_slug].id,
        neighborhood_id=hoods[n_name].id if n_name and n_name in hoods else None,
        view_count=0,
        published_at=datetime.utcnow(),
        address=None,
        **pd,
    )
    db.add(p)

db.commit()
print("✓ Database seeded successfully!")
print("\nLogin credentials:")
for email, fn, ln, *_ in agents_data:
    print(f"  {email} / Agent123!")
