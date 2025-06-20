"""Data pipeline for Trip Sniper offers."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Iterable, List, Sequence

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from .fetchers import BookingFetcher, SkyscannerFetcher
from .models import Offer
from .scoring.steal_score import steal_score

__all__ = ["run_pipeline", "OfferRecord"]

logger = logging.getLogger(__name__)

Base = declarative_base()


class OfferRecord(Base):
    """SQLAlchemy ORM model for persisted offers."""

    __tablename__ = "offers"

    id = Column(String, primary_key=True)
    price_per_person = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    hotel_rating = Column(Float, nullable=False)
    stars = Column(Integer, nullable=False)
    distance_from_beach = Column(Float, nullable=False)
    direct = Column(Boolean, nullable=False)
    total_duration = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    attraction_score = Column(Float, nullable=False)
    visible_from = Column(DateTime, nullable=False)
    steal_score = Column(Float, nullable=False)


def _combine_offers(flights: Iterable[Offer], hotels: Iterable[Offer]) -> List[Offer]:
    """Join flight and hotel offers by destination and date."""
    result: List[Offer] = []
    for flight in flights:
        for hotel in hotels:
            if flight.location == hotel.location and flight.date.date() == hotel.date.date():
                visible_from = max(flight.visible_from, hotel.visible_from)
                offer = Offer(
                    id=f"{flight.id}-{hotel.id}",
                    price_per_person=flight.price_per_person + hotel.price_per_person,
                    avg_price=flight.avg_price + hotel.avg_price,
                    hotel_rating=hotel.hotel_rating,
                    stars=hotel.stars,
                    distance_from_beach=hotel.distance_from_beach,
                    direct=flight.direct,
                    total_duration=flight.total_duration,
                    date=flight.date,
                    location=flight.location,
                    attraction_score=max(flight.attraction_score, hotel.attraction_score),
                    visible_from=visible_from,
                )
                result.append(offer)
    return result


def _upsert_offer(session: Session, offer: Offer, score: float) -> None:
    """Insert or update an offer record."""
    existing = session.get(OfferRecord, offer.id)
    if existing is None:
        record = OfferRecord(
            id=offer.id,
            price_per_person=offer.price_per_person,
            avg_price=offer.avg_price,
            hotel_rating=offer.hotel_rating,
            stars=offer.stars,
            distance_from_beach=offer.distance_from_beach,
            direct=offer.direct,
            total_duration=offer.total_duration,
            date=offer.date,
            location=offer.location,
            attraction_score=offer.attraction_score,
            visible_from=offer.visible_from,
            steal_score=score,
        )
        session.add(record)
    else:
        existing.price_per_person = offer.price_per_person
        existing.avg_price = offer.avg_price
        existing.hotel_rating = offer.hotel_rating
        existing.stars = offer.stars
        existing.distance_from_beach = offer.distance_from_beach
        existing.direct = offer.direct
        existing.total_duration = offer.total_duration
        existing.date = offer.date
        existing.location = offer.location
        existing.attraction_score = offer.attraction_score
        existing.visible_from = offer.visible_from
        existing.steal_score = score


def run_pipeline(destinations: Sequence[str], dates: Sequence[str], database_url: str | None = None) -> None:
    """Fetch offers, score them and persist to PostgreSQL."""
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not provided")

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    flight_fetcher = SkyscannerFetcher()
    hotel_fetcher = BookingFetcher()

    with Session(engine) as session:
        for dest in destinations:
            for date in dates:
                flights = flight_fetcher.fetch_offers(dest, date)
                hotels = hotel_fetcher.fetch_offers(dest, date, date)
                combined = _combine_offers(flights, hotels)

                for offer in combined:
                    if offer.visible_from > datetime.utcnow():
                        continue
                    score = steal_score(offer)
                    _upsert_offer(session, offer, score)
        session.commit()

