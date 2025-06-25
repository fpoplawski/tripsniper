import pytest
from datetime import datetime

from trip_sniper.fetchers.amadeus import AmadeusFlightFetcher
from trip_sniper.models import Offer


class DummyResponse:
    def __init__(self, data, headers=None):
        self.data = data
        self.headers = headers or {}


def make_fetcher(monkeypatch, data, headers=None):
    fetcher = AmadeusFlightFetcher(api_key="k", api_secret="s")

    class DummySearch:
        def __init__(self):
            self.params = None

        def get(self, **kwargs):
            self.params = kwargs
            return DummyResponse(data, headers)

    dummy = DummySearch()
    client = type("C", (), {"shopping": type("S", (), {"flight_offers_search": dummy})()})()
    fetcher._amadeus = client
    return fetcher, dummy


def test_fetch_offers_maps_response(monkeypatch):
    data = [
        {
            "id": "1",
            "price": {"grandTotal": "120.0"},
            "itineraries": [
                {
                    "segments": [
                        {
                            "departure": {"at": "2024-01-01T10:00:00"},
                            "arrival": {"at": "2024-01-01T12:00:00"},
                        }
                    ]
                }
            ],
        }
    ]
    fetcher, dummy = make_fetcher(monkeypatch, data, {"X-RateLimit-Remaining": "1"})
    offers = fetcher.fetch_offers("LON", "2024-01-01", origin="WAW")
    assert dummy.params["originLocationCode"] == "WAW"
    assert isinstance(offers[0], Offer)
    assert offers[0].id == "1"
    assert offers[0].price_per_person == 120.0
    assert offers[0].total_duration == 120
    assert offers[0].location == "LON"
    assert offers[0].date == datetime(2024, 1, 1)


def test_fetch_offers_uses_env_origin(monkeypatch):
    monkeypatch.setenv("ORIGIN_IATA", "XYZ")
    data = []
    fetcher, dummy = make_fetcher(monkeypatch, data, {"X-RateLimit-Remaining": "1"})
    fetcher.fetch_offers("LON", "2024-01-01")
    assert dummy.params["originLocationCode"] == "XYZ"
