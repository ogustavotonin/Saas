from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    points_balance: Mapped[int] = mapped_column(Integer, default=0)

    subscriptions = relationship("Subscription", back_populates="client", cascade="all, delete-orphan")
    maintenances = relationship("Maintenance", back_populates="client", cascade="all, delete-orphan")


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    referrer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    referrer_email: Mapped[str] = mapped_column(String(120), nullable=False)
    referred_client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    sale_value: Mapped[float] = mapped_column(Float, nullable=False)
    sale_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    bonus_percentage: Mapped[float] = mapped_column(Float, default=5.0)
    bonus_value: Mapped[float] = mapped_column(Float, default=0.0)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ativa")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_fee: Mapped[float] = mapped_column(Float, nullable=False)

    client = relationship("Client", back_populates="subscriptions")


class Maintenance(Base):
    __tablename__ = "maintenances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    date: Mapped[date] = mapped_column(Date, nullable=False)

    client = relationship("Client", back_populates="maintenances")
