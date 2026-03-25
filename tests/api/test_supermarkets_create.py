from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.deps import get_shop_owner_service, require_authenticated
from app.api.v1.schemas.shop_owner import SupermarketCreateRequest
from app.domain.enums.roles import Role
from app.main import app


@dataclass
class _UserStub:
    user_id: str
    role: Role


class _CreateShopOwnerServiceStub:
    def create_supermarket(self, payload: SupermarketCreateRequest, role: Role):
        assert payload.user_id == 501
        assert payload.shop_name == "New Mart"
        assert payload.address.city == "Kochi"
        if payload.subscription is not None:
            # Incomplete subscription payloads should be allowed by the schema
            # and later ignored by the repository/service.
            if payload.subscription.amount is not None:
                assert payload.subscription.amount == Decimal("99.00")
        if payload.promotion is not None:
            assert payload.promotion.is_marketing_enabled is True
        return {
            "shop_owner": {
                "shop_id": "SHOP501",
                "user_id": 501,
                "shop_name": "New Mart",
                "phone": None,
                "email": None,
                "photo": None,
                "status": "active",
                "payment_status": "pending",
                "is_blocked": False,
                "geo_coordinates": None,
                "upi_id": None,
                "rating": None,
                "delivery_time": 30,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
            "address": {
                "street_address": "Main",
                "city": "Kochi",
                "state": "KL",
                "pincode": "682001",
                "latitude": None,
                "longitude": None,
            },
            "subscription": None,
            "promotion": None,
            "delivery_partners": [] if role == Role.PORTAL_USER else [{"delivery_partner_id": "DP1"}],
            "subscription_invoices": [],
            "daily_order_stats": None if role == Role.PORTAL_USER else [{"date": "2026-03-24"}],
        }

    def list_supermarkets(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def get_supermarket_detail(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


def _valid_body() -> dict:
    return {
        "user_id": 501,
        "shop_name": "New Mart",
        "password": "client-hashed-secret",
        "address": {
            "street_address": "Main",
            "city": "Kochi",
            "state": "KL",
            "pincode": "682001",
        },
    }


def test_supermarkets_create_requires_authentication():
    client = TestClient(app)
    response = client.post("/supermarkets", json=_valid_body())
    assert response.status_code == 401


def test_supermarkets_create_forbidden_for_monitor():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="monitor-1", role=Role.MONITOR_APP
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _CreateShopOwnerServiceStub()
    client = TestClient(app)
    response = client.post("/supermarkets", json=_valid_body())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    app.dependency_overrides.clear()


def test_supermarkets_create_success_portal():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _CreateShopOwnerServiceStub()
    client = TestClient(app)
    response = client.post("/supermarkets", json=_valid_body())
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["shop_owner"]["user_id"] == 501
    assert data["shop_owner"]["shop_id"] == "SHOP501"
    assert data["delivery_partners"] == []
    assert data["daily_order_stats"] is None
    app.dependency_overrides.clear()


def test_supermarkets_create_success_superadmin():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _CreateShopOwnerServiceStub()
    client = TestClient(app)
    response = client.post("/supermarkets", json=_valid_body())
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["shop_owner"]["user_id"] == 501
    assert data["daily_order_stats"] is not None
    app.dependency_overrides.clear()


def test_supermarkets_create_wires_nested_subscription_and_promotion():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _CreateShopOwnerServiceStub()
    client = TestClient(app)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)
    body = _valid_body()
    body["subscription"] = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "amount": "99.00",
    }
    body["promotion"] = {"is_marketing_enabled": True}
    response = client.post("/supermarkets", json=body)
    assert response.status_code == 200
    app.dependency_overrides.clear()


def test_supermarkets_create_allows_incomplete_subscription():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _CreateShopOwnerServiceStub()
    client = TestClient(app)
    body = _valid_body()
    body["subscription"] = {}  # missing start/end/amount -> backend should ignore
    response = client.post("/supermarkets", json=body)
    assert response.status_code == 200
    assert response.json()["data"]["subscription"] is None
    app.dependency_overrides.clear()


def test_supermarkets_create_validation_missing_address():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    client = TestClient(app)
    response = client.post(
        "/supermarkets",
        json={"user_id": 1, "shop_name": "X", "password": "p"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    app.dependency_overrides.clear()
