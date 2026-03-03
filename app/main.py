import os
from datetime import date, timedelta

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, engine, get_db
from .models import Client, Maintenance, Referral, Subscription, User
from .services import (
    calculate_bonus_and_points,
    import_agendor_deals,
    send_referral_deal_to_agendor,
    send_to_agendor,
    send_to_autentique,
)

ROOT_PATH = os.getenv("ROOT_PATH", "")
app = FastAPI(title="NexusCore Micro SaaS", root_path=ROOT_PATH)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "troque-esta-chave"))
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=pwd_context.hash("admin123")))
            db.commit()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER)
    return user


@app.get("/")
def index(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciais inválidas"})
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    data = {
        "clients": db.query(Client).count(),
        "active_subscriptions": db.query(Subscription).filter(Subscription.status == "ativa").count(),
        "open_referrals": db.query(Referral).filter(Referral.sale_closed == False).count(),
        "maintenances": db.query(Maintenance).count(),
    }
    return templates.TemplateResponse("dashboard.html", {"request": request, "data": data})


@app.get("/clients")
def clients(request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items = db.query(Client).order_by(Client.id.desc()).all()
    return templates.TemplateResponse("clients.html", {"request": request, "clients": items})


@app.post("/clients")
def create_client(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    db.add(Client(name=name, email=email, phone=phone))
    db.commit()
    return RedirectResponse(url="/clients", status_code=303)


@app.get("/clients/{client_id}/edit")
def edit_client_page(client_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    return templates.TemplateResponse("client_edit.html", {"request": request, "client": client})


@app.post("/clients/{client_id}/edit")
def edit_client(
    client_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    points_balance: int = Form(0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    client.name = name
    client.email = email
    client.phone = phone
    client.points_balance = points_balance
    db.commit()
    return RedirectResponse(url="/clients", status_code=303)


@app.post("/clients/{client_id}/delete")
def delete_client(client_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    client = db.get(Client, client_id)
    if client:
        db.delete(client)
        db.commit()
    return RedirectResponse(url="/clients", status_code=303)


@app.get("/referrals")
def referrals(request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items = db.query(Referral).order_by(Referral.id.desc()).all()
    clients_data = db.query(Client).order_by(Client.name.asc()).all()
    return templates.TemplateResponse("referrals.html", {"request": request, "referrals": items, "clients": clients_data})


@app.post("/referrals")
def create_referral(
    referrer_name: str = Form(...),
    referrer_email: str = Form(...),
    referred_client_id: int = Form(...),
    sale_value: float = Form(...),
    bonus_percentage: float = Form(5),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    db.add(
        Referral(
            referrer_name=referrer_name,
            referrer_email=referrer_email,
            referred_client_id=referred_client_id,
            sale_value=sale_value,
            bonus_percentage=bonus_percentage,
        )
    )
    db.commit()
    return RedirectResponse(url="/referrals", status_code=303)


@app.get("/referrals/{referral_id}/edit")
def edit_referral_page(referral_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    referral = db.get(Referral, referral_id)
    if not referral:
        raise HTTPException(404, "Indicação não encontrada")
    clients_data = db.query(Client).order_by(Client.name.asc()).all()
    return templates.TemplateResponse("referral_edit.html", {"request": request, "referral": referral, "clients": clients_data})


@app.post("/referrals/{referral_id}/edit")
def edit_referral(
    referral_id: int,
    referrer_name: str = Form(...),
    referrer_email: str = Form(...),
    referred_client_id: int = Form(...),
    sale_value: float = Form(...),
    bonus_percentage: float = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    referral = db.get(Referral, referral_id)
    if not referral:
        raise HTTPException(404, "Indicação não encontrada")
    referral.referrer_name = referrer_name
    referral.referrer_email = referrer_email
    referral.referred_client_id = referred_client_id
    referral.sale_value = sale_value
    referral.bonus_percentage = bonus_percentage
    db.commit()
    return RedirectResponse(url="/referrals", status_code=303)


@app.post("/referrals/{referral_id}/delete")
def delete_referral(referral_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    referral = db.get(Referral, referral_id)
    if referral:
        db.delete(referral)
        db.commit()
    return RedirectResponse(url="/referrals", status_code=303)


@app.post("/referrals/{referral_id}/close")
async def close_referral(
    referral_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    referral = db.get(Referral, referral_id)
    if not referral:
        raise HTTPException(404, "Indicação não encontrada")

    referral.sale_closed = True
    referral.bonus_value, referral.points_awarded = calculate_bonus_and_points(True, referral.sale_value, referral.bonus_percentage)

    client = db.get(Client, referral.referred_client_id)
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    client.points_balance += referral.points_awarded

    db.add(
        Subscription(
            client_id=client.id,
            status="ativa",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_fee=max(referral.sale_value / 12, 199.0),
        )
    )

    agendor_token = os.getenv("AGENDOR_TOKEN")
    autentique_token = os.getenv("AUTENTIQUE_TOKEN")
    await send_to_agendor({"name": client.name, "contact": {"email": client.email, "phone": client.phone}}, agendor_token)
    await send_to_autentique({"query": "mutation { noop }"}, autentique_token)

    db.commit()
    return RedirectResponse(url="/referrals", status_code=303)


@app.post("/referrals/{referral_id}/send-deal")
async def send_referral_deal(
    referral_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    referral = db.get(Referral, referral_id)
    if not referral:
        raise HTTPException(404, "Indicação não encontrada")
    client = db.get(Client, referral.referred_client_id)
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    agendor_token = os.getenv("AGENDOR_TOKEN")
    payload = {
        "title": f"Negócio de indicação - {client.name}",
        "description": f"Indicação por {referral.referrer_name}",
        "value": referral.sale_value,
    }
    await send_referral_deal_to_agendor(agendor_token, payload)
    return RedirectResponse(url="/referrals", status_code=303)


@app.get("/subscriptions")
def subscriptions(request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items = db.query(Subscription).order_by(Subscription.id.desc()).all()
    clients_data = db.query(Client).order_by(Client.name.asc()).all()
    return templates.TemplateResponse("subscriptions.html", {"request": request, "subscriptions": items, "clients": clients_data})


@app.post("/subscriptions")
def create_subscription(
    client_id: int = Form(...),
    status_value: str = Form("ativa"),
    start_date_value: date = Form(...),
    end_date_value: date = Form(...),
    monthly_fee: float = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    db.add(
        Subscription(
            client_id=client_id,
            status=status_value,
            start_date=start_date_value,
            end_date=end_date_value,
            monthly_fee=monthly_fee,
        )
    )
    db.commit()
    return RedirectResponse(url="/subscriptions", status_code=303)


@app.get("/subscriptions/{subscription_id}/edit")
def edit_subscription_page(subscription_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(404, "Assinatura não encontrada")
    clients_data = db.query(Client).order_by(Client.name.asc()).all()
    return templates.TemplateResponse(
        "subscription_edit.html",
        {"request": request, "subscription": subscription, "clients": clients_data},
    )


@app.post("/subscriptions/{subscription_id}/edit")
def edit_subscription(
    subscription_id: int,
    client_id: int = Form(...),
    status_value: str = Form(...),
    start_date_value: date = Form(...),
    end_date_value: date = Form(...),
    monthly_fee: float = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(404, "Assinatura não encontrada")
    subscription.client_id = client_id
    subscription.status = status_value
    subscription.start_date = start_date_value
    subscription.end_date = end_date_value
    subscription.monthly_fee = monthly_fee
    db.commit()
    return RedirectResponse(url="/subscriptions", status_code=303)


@app.post("/subscriptions/{subscription_id}/delete")
def delete_subscription(subscription_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    subscription = db.get(Subscription, subscription_id)
    if subscription:
        db.delete(subscription)
        db.commit()
    return RedirectResponse(url="/subscriptions", status_code=303)


@app.get("/maintenances")
def maintenances(request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items = db.query(Maintenance).order_by(Maintenance.date.desc()).all()
    clients_data = db.query(Client).order_by(Client.name.asc()).all()
    return templates.TemplateResponse("maintenances.html", {"request": request, "maintenances": items, "clients": clients_data})


@app.post("/maintenances")
def create_maintenance(
    title: str = Form(...),
    notes: str = Form(""),
    client_id: int = Form(...),
    maintenance_date: date = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    db.add(Maintenance(title=title, notes=notes, client_id=client_id, date=maintenance_date))
    db.commit()
    return RedirectResponse(url="/maintenances", status_code=303)


@app.get("/maintenances/{maintenance_id}/edit")
def edit_maintenance_page(maintenance_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    maintenance = db.get(Maintenance, maintenance_id)
    if not maintenance:
        raise HTTPException(404, "Manutenção não encontrada")
    clients_data = db.query(Client).order_by(Client.name.asc()).all()
    return templates.TemplateResponse(
        "maintenance_edit.html",
        {"request": request, "maintenance": maintenance, "clients": clients_data},
    )


@app.post("/maintenances/{maintenance_id}/edit")
def edit_maintenance(
    maintenance_id: int,
    title: str = Form(...),
    notes: str = Form(""),
    client_id: int = Form(...),
    maintenance_date: date = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    maintenance = db.get(Maintenance, maintenance_id)
    if not maintenance:
        raise HTTPException(404, "Manutenção não encontrada")
    maintenance.title = title
    maintenance.notes = notes
    maintenance.client_id = client_id
    maintenance.date = maintenance_date
    db.commit()
    return RedirectResponse(url="/maintenances", status_code=303)


@app.post("/maintenances/{maintenance_id}/delete")
def delete_maintenance(maintenance_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    maintenance = db.get(Maintenance, maintenance_id)
    if maintenance:
        db.delete(maintenance)
        db.commit()
    return RedirectResponse(url="/maintenances", status_code=303)


@app.get("/integrations")
def integrations(request: Request, _: User = Depends(get_current_user)):
    return templates.TemplateResponse("integrations.html", {"request": request, "deals": [], "error": None})


@app.post("/integrations/import-agendor")
async def integrations_import_agendor(request: Request, _: User = Depends(get_current_user)):
    agendor_token = os.getenv("AGENDOR_TOKEN")
    try:
        deals = await import_agendor_deals(agendor_token)
        return templates.TemplateResponse("integrations.html", {"request": request, "deals": deals[:20], "error": None})
    except Exception:
        return templates.TemplateResponse(
            "integrations.html",
            {"request": request, "deals": [], "error": "Não foi possível importar negócios do Agendor."},
        )
