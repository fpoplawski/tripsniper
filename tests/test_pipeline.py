from datetime import datetime, timedelta

import pytest

from trip_sniper.models import Offer
from trip_sniper.pipeline import _combine_offers


def make_offer(**kwargs) -> Offer:
    base = dict(
        id="id",
        price_per_person=100.0,
        avg_price=150.0,
        hotel_rating=5.0,
        stars=4,
        distance_from_beach=0.2,
        direct=True,
        total_duration=120,
        date=datetime(2023, 1, 1),
        location="AAA",
        attraction_score=0.0,
        visible_from=datetime(2023, 1, 1),
    )
    base.update(kwargs)
    return Offer(**base)


def test_only_matching_destination_and_date_are_combined():
    now = datetime(2023, 1, 1)
    flight1 = make_offer(id="F1", location="PAR", date=now)
    flight2 = make_offer(id="F2", location="LON", date=now)

    hotel1 = make_offer(id="H1", location="PAR", date=now)
    hotel2 = make_offer(id="H2", location="PAR", date=now + timedelta(days=1))

    combined = _combine_offers([flight1, flight2], [hotel1, hotel2])

    assert len(combined) == 1
    offer = combined[0]
    assert offer.id == "F1-H1"
    assert offer.location == "PAR"
    assert offer.date == now


def test_visible_from_is_max_of_flight_and_hotel():
    now = datetime(2023, 1, 1)
    flight_visible = now + timedelta(hours=1)
    hotel_visible = now + timedelta(hours=2)
    flight = make_offer(id="F1", location="PAR", date=now, visible_from=flight_visible)
    hotel = make_offer(id="H1", location="PAR", date=now, visible_from=hotel_visible)

    combined = _combine_offers([flight], [hotel])

    assert len(combined) == 1
    assert combined[0].visible_from == hotel_visible
