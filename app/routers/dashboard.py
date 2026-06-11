import os
import shutil
from fastapi import APIRouter, Request, Form, Depends, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    Property, PropertyImage, Inquiry, Agent,
    PropertyType, ListingType, PropertyStatus, Currency, District, Neighborhood
)
from app.utils.auth import get_current_user
from app.utils.slugify import unique_slug, new_id
from app.config import UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_agent(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return None
    return user


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    props = db.query(Property).filter(Property.agent_id == agent.id).order_by(Property.created_at.desc()).all() if agent else []
    inquiries = []
    if agent:
        prop_ids = [p.id for p in props]
        if prop_ids:
            inquiries = db.query(Inquiry).filter(Inquiry.property_id.in_(prop_ids)).order_by(Inquiry.created_at.desc()).limit(10).all()
    return templates.TemplateResponse("dashboard/home.html", {
        "request": request, "user": user, "agent": agent,
        "properties": props, "inquiries": inquiries,
        "active": "home",
    })


@router.get("/dashboard/listings", response_class=HTMLResponse)
def dashboard_listings(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    props = db.query(Property).filter(Property.agent_id == agent.id).order_by(Property.created_at.desc()).all() if agent else []
    prop_ids = [p.id for p in props]
    from sqlalchemy import func
    inq_counts = {}
    if prop_ids:
        rows = db.query(Inquiry.property_id, func.count(Inquiry.id)).filter(
            Inquiry.property_id.in_(prop_ids)
        ).group_by(Inquiry.property_id).all()
        inq_counts = {r[0]: r[1] for r in rows}
    return templates.TemplateResponse("dashboard/listings.html", {
        "request": request, "user": user, "agent": agent,
        "properties": props, "inq_counts": inq_counts, "active": "listings",
    })


@router.get("/dashboard/listings/new", response_class=HTMLResponse)
def new_listing_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    districts = db.query(District).order_by(District.name).all()
    return templates.TemplateResponse("dashboard/listing_form.html", {
        "request": request, "user": user,
        "prop": None, "districts": districts,
        "property_types": [t.value for t in PropertyType],
        "listing_types": [t.value for t in ListingType],
        "statuses": [s.value for s in PropertyStatus],
        "currencies": [c.value for c in Currency],
        "active": "listings", "error": None,
    })


@router.post("/dashboard/listings/new")
async def create_listing(
    request: Request,
    db: Session = Depends(get_db),
    title_en: str = Form(...),
    title_tr: str = Form(""),
    title_de: str = Form(""),
    type: str = Form(...),
    listing_type: str = Form(...),
    status: str = Form("ACTIVE"),
    district_id: str = Form(...),
    neighborhood_id: str = Form(""),
    address: str = Form(""),
    latitude: str = Form(""),
    longitude: str = Form(""),
    price: float = Form(...),
    currency: str = Form("EUR"),
    size_sqm: float = Form(None),
    bedrooms: int = Form(None),
    bathrooms: int = Form(None),
    floor: int = Form(None),
    total_floors: int = Form(None),
    description_en: str = Form(""),
    description_tr: str = Form(""),
    description_de: str = Form(""),
    has_pool: bool = Form(False),
    has_parking: bool = Form(False),
    is_furnished: bool = Form(False),
    has_garden: bool = Form(False),
    has_security: bool = Form(False),
    has_elevator: bool = Form(False),
    has_balcony: bool = Form(False),
    has_terrace: bool = Form(False),
    eligible_for_citizenship: bool = Form(False),
    images: list[UploadFile] = File(default=[]),
):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()

    prop = Property(
        id=new_id(),
        slug=unique_slug(title_en),
        agent_id=agent.id,
        district_id=district_id or None,
        neighborhood_id=neighborhood_id or None,
        type=PropertyType(type),
        listing_type=ListingType(listing_type),
        status=PropertyStatus(status),
        title_en=title_en,
        title_tr=title_tr or None,
        title_de=title_de or None,
        price=price,
        currency=Currency(currency),
        size_sqm=size_sqm,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        floor=floor,
        total_floors=total_floors,
        address=address or None,
        latitude=float(latitude) if latitude else None,
        longitude=float(longitude) if longitude else None,
        description_en=description_en or None,
        description_tr=description_tr or None,
        description_de=description_de or None,
        has_pool=has_pool, has_parking=has_parking, is_furnished=is_furnished,
        has_garden=has_garden, has_security=has_security, has_elevator=has_elevator,
        has_balcony=has_balcony, has_terrace=has_terrace,
        eligible_for_citizenship=eligible_for_citizenship,
    )
    db.add(prop)
    db.flush()

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    for i, img in enumerate(images):
        if not img.filename:
            continue
        ext = img.filename.rsplit(".", 1)[-1].lower()
        filename = f"{new_id()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        db.add(PropertyImage(
            id=new_id(), property_id=prop.id,
            url=f"/uploads/{filename}", is_cover=(i == 0), sort_order=i,
        ))

    db.commit()
    return RedirectResponse("/dashboard/listings", status_code=302)


@router.get("/dashboard/listings/{prop_id}/edit", response_class=HTMLResponse)
def edit_listing_form(prop_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    prop = db.query(Property).filter(Property.id == prop_id, Property.agent_id == agent.id).first()
    if not prop:
        raise HTTPException(status_code=404)
    districts = db.query(District).order_by(District.name).all()
    neighborhoods = db.query(Neighborhood).filter(Neighborhood.district_id == prop.district_id).all() if prop.district_id else []
    return templates.TemplateResponse("dashboard/listing_form.html", {
        "request": request, "user": user, "prop": prop,
        "districts": districts, "neighborhoods": neighborhoods,
        "property_types": [t.value for t in PropertyType],
        "listing_types": [t.value for t in ListingType],
        "statuses": [s.value for s in PropertyStatus],
        "currencies": [c.value for c in Currency],
        "active": "listings", "error": None,
    })


@router.post("/dashboard/listings/{prop_id}/edit")
async def update_listing(
    prop_id: str,
    request: Request,
    db: Session = Depends(get_db),
    title_en: str = Form(...),
    title_tr: str = Form(""),
    title_de: str = Form(""),
    type: str = Form(...),
    listing_type: str = Form(...),
    status: str = Form("ACTIVE"),
    district_id: str = Form(...),
    neighborhood_id: str = Form(""),
    address: str = Form(""),
    latitude: str = Form(""),
    longitude: str = Form(""),
    price: float = Form(...),
    currency: str = Form("EUR"),
    size_sqm: float = Form(None),
    bedrooms: int = Form(None),
    bathrooms: int = Form(None),
    floor: int = Form(None),
    total_floors: int = Form(None),
    description_en: str = Form(""),
    description_tr: str = Form(""),
    description_de: str = Form(""),
    has_pool: bool = Form(False),
    has_parking: bool = Form(False),
    is_furnished: bool = Form(False),
    has_garden: bool = Form(False),
    has_security: bool = Form(False),
    has_elevator: bool = Form(False),
    has_balcony: bool = Form(False),
    has_terrace: bool = Form(False),
    eligible_for_citizenship: bool = Form(False),
    images: list[UploadFile] = File(default=[]),
):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    prop = db.query(Property).filter(Property.id == prop_id, Property.agent_id == agent.id).first()
    if not prop:
        raise HTTPException(status_code=404)

    prop.title_en = title_en
    prop.title_tr = title_tr or None
    prop.title_de = title_de or None
    prop.type = PropertyType(type)
    prop.listing_type = ListingType(listing_type)
    prop.status = PropertyStatus(status)
    prop.district_id = district_id or None
    prop.neighborhood_id = neighborhood_id or None
    prop.address = address or None
    prop.latitude = float(latitude) if latitude else None
    prop.longitude = float(longitude) if longitude else None
    prop.price = price
    prop.currency = Currency(currency)
    prop.size_sqm = size_sqm
    prop.bedrooms = bedrooms
    prop.bathrooms = bathrooms
    prop.floor = floor
    prop.total_floors = total_floors
    prop.description_en = description_en or None
    prop.description_tr = description_tr or None
    prop.description_de = description_de or None
    prop.has_pool = has_pool
    prop.has_parking = has_parking
    prop.is_furnished = is_furnished
    prop.has_garden = has_garden
    prop.has_security = has_security
    prop.has_elevator = has_elevator
    prop.has_balcony = has_balcony
    prop.has_terrace = has_terrace
    prop.eligible_for_citizenship = eligible_for_citizenship

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    existing_count = len(prop.images)
    for i, img in enumerate(images):
        if not img.filename:
            continue
        ext = img.filename.rsplit(".", 1)[-1].lower()
        filename = f"{new_id()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        db.add(PropertyImage(
            id=new_id(), property_id=prop.id,
            url=f"/uploads/{filename}",
            is_cover=(existing_count == 0 and i == 0),
            sort_order=existing_count + i,
        ))

    db.commit()
    return RedirectResponse("/dashboard/listings", status_code=302)


@router.post("/dashboard/listings/{prop_id}/delete")
def delete_listing(prop_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    prop = db.query(Property).filter(Property.id == prop_id, Property.agent_id == agent.id).first()
    if prop:
        prop.status = PropertyStatus.ARCHIVED
        db.commit()
    return RedirectResponse("/dashboard/listings", status_code=302)


@router.get("/dashboard/inquiries", response_class=HTMLResponse)
def dashboard_inquiries(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role.value not in ("AGENT", "ADMIN"):
        return RedirectResponse("/login", status_code=302)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    props = db.query(Property).filter(Property.agent_id == agent.id).all() if agent else []
    prop_ids = [p.id for p in props]
    inquiries = db.query(Inquiry).filter(Inquiry.property_id.in_(prop_ids)).order_by(Inquiry.created_at.desc()).all() if prop_ids else []
    return templates.TemplateResponse("dashboard/inquiries.html", {
        "request": request, "user": user, "inquiries": inquiries, "active": "inquiries",
    })


@router.get("/api/neighborhoods")
def get_neighborhoods(district_id: str, db: Session = Depends(get_db)):
    neighborhoods = db.query(Neighborhood).filter(Neighborhood.district_id == district_id).all()
    from fastapi.responses import JSONResponse
    return JSONResponse([{"id": n.id, "name": n.name} for n in neighborhoods])
