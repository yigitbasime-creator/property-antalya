from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.models import Property, District, PropertyStatus, PropertyType, ListingType
from app.utils.auth import get_current_user
from app.i18n import get_lang, get_t, FLAGS, SUPPORTED_LANGS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def lang_ctx(request: Request) -> dict:
    lang = get_lang(request)
    return {"lang": lang, "t": get_t(lang), "flags": FLAGS, "supported_langs": SUPPORTED_LANGS}


@router.get("/", response_class=HTMLResponse)
def homepage(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    featured = (
        db.query(Property)
        .filter(Property.status == PropertyStatus.ACTIVE)
        .order_by(Property.view_count.desc())
        .limit(6)
        .all()
    )
    districts = db.query(District).order_by(District.name).all()
    stats = {
        "properties": db.query(Property).filter(Property.status == PropertyStatus.ACTIVE).count(),
        "districts": db.query(District).count(),
    }
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "featured": featured,
        "districts": districts,
        "stats": stats,
        **lang_ctx(request),
    })


@router.get("/properties", response_class=HTMLResponse)
def property_list(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    q: str = Query(None),
    type: str = Query(None),
    listing_type: str = Query(None),
    district_id: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    bedrooms: int = Query(None),
    page: int = Query(1),
):
    per_page = 12
    filters = [Property.status == PropertyStatus.ACTIVE]

    if q:
        filters.append(or_(
            Property.title_en.ilike(f"%{q}%"),
            Property.title_tr.ilike(f"%{q}%"),
            Property.title_de.ilike(f"%{q}%"),
            Property.description_en.ilike(f"%{q}%"),
        ))
    if type:
        try:
            filters.append(Property.type == PropertyType(type))
        except ValueError:
            pass
    if listing_type:
        try:
            filters.append(Property.listing_type == ListingType(listing_type))
        except ValueError:
            pass
    if district_id:
        filters.append(Property.district_id == district_id)
    if min_price:
        filters.append(Property.price >= min_price)
    if max_price:
        filters.append(Property.price <= max_price)
    if bedrooms:
        filters.append(Property.bedrooms >= bedrooms)

    total = db.query(Property).filter(and_(*filters)).count()
    properties = (
        db.query(Property)
        .filter(and_(*filters))
        .order_by(Property.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    districts = db.query(District).order_by(District.name).all()
    total_pages = (total + per_page - 1) // per_page

    template = "properties/list.html"
    if request.headers.get("HX-Request"):
        template = "partials/property_cards.html"

    return templates.TemplateResponse(template, {
        "request": request,
        "user": user,
        "properties": properties,
        "districts": districts,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "q": q or "",
        "type": type or "",
        "listing_type": listing_type or "",
        "district_id": district_id or "",
        "min_price": min_price or "",
        "max_price": max_price or "",
        "bedrooms": bedrooms or "",
        "property_types": [t.value for t in PropertyType],
        "listing_types": [t.value for t in ListingType],
        **lang_ctx(request),
    })


@router.get("/properties/{slug}", response_class=HTMLResponse)
def property_detail(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.slug == slug).first()
    if not prop:
        return templates.TemplateResponse("404.html", {"request": request, "user": user}, status_code=404)

    prop.view_count = (prop.view_count or 0) + 1
    db.commit()

    similar = (
        db.query(Property)
        .filter(
            Property.status == PropertyStatus.ACTIVE,
            Property.district_id == prop.district_id,
            Property.id != prop.id,
        )
        .limit(3)
        .all()
    )
    return templates.TemplateResponse("properties/detail.html", {
        "request": request,
        "user": user,
        "prop": prop,
        "similar": similar,
        **lang_ctx(request),
    })
