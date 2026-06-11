from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Inquiry, Property
from app.utils.slugify import new_id

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/inquiries/{property_id}", response_class=HTMLResponse)
def submit_inquiry(
    property_id: str,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    message: str = Form(...),
):
    inquiry = Inquiry(
        id=new_id(),
        property_id=property_id,
        name=name,
        email=email,
        phone=phone,
        message=message,
    )
    db.add(inquiry)
    db.commit()

    # HTMX returns a success partial
    return templates.TemplateResponse("partials/inquiry_success.html", {"request": request})
