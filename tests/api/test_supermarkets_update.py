from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.api.deps import get_shop_owner_service, require_authenticated
from app.api.v1.schemas.shop_owner import SupermarketUpdateRequest
from app.domain.enums.roles import Role
from app.main import app


@dataclass
class _UserStub:
    user_id: str
    role: Role


class _ShopOwnerServiceStub:
    def update_supermarket(self, user_id: int, payload: SupermarketUpdateRequest, role: Role):
        assert user_id == 123
        assert role == Role.SUPERADMIN
        dumped = payload.model_dump(exclude_unset=True)
        assert dumped["shop_name"] == "Updated Shop"
        assert dumped["delivery_time"] == 45
        assert dumped["address"]["city"] == "Kochi"
        return {"shop_owner": {"user_id": user_id, "shop_id": "SHOP123"}, "address": {}, "subscription": None, "promotion": None, "delivery_partners": [], "subscription_invoices": [], "daily_order_stats": []}

    def list_supermarkets(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def get_supermarket_detail(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


def test_supermarkets_update_requires_authentication():
    client = TestClient(app)
    response = client.patch("/supermarkets/123", json={"shop_name": "X"})
    assert response.status_code == 401


def test_supermarkets_update_forbidden_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    client = TestClient(app)
    response = client.patch("/supermarkets/123", json={"shop_name": "X"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    app.dependency_overrides.clear()


def test_supermarkets_update_forbidden_for_monitor_app():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="monitor-1", role=Role.MONITOR_APP
    )
    client = TestClient(app)
    response = client.patch("/supermarkets/123", json={"shop_name": "X"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    app.dependency_overrides.clear()


def test_supermarkets_update_success_superadmin_wiring():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)
    response = client.patch(
        "/supermarkets/123",
        json={
            "shop_name": "Updated Shop",
            "delivery_time": 45,
            "address": {"city": "Kochi"},
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["shop_owner"]["user_id"] == 123
    app.dependency_overrides.clear()


def test_supermarkets_update_validation_invalid_delivery_time():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    client = TestClient(app)
    response = client.patch("/supermarkets/123", json={"delivery_time": -1})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    app.dependency_overrides.clear()

