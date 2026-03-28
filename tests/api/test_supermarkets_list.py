from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.api.deps import get_shop_owner_service, require_authenticated
from app.domain.enums.roles import Role
from app.main import app


@dataclass
class _UserStub:
    user_id: str
    role: Role


class _ShopOwnerServiceStub:
    def list_supermarkets(
        self,
        page: int,
        limit: int,
        *,
        name: str | None = None,
        user_id: int | None = None,
        shop_id: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ):
        assert isinstance(page, int)
        assert isinstance(limit, int)
        # Portal list is scoped by login email (JWT sub); query filters are ignored.
        if email is not None:
            assert email == "portal-1"
            assert name is None and user_id is None and shop_id is None and phone is None
        else:
            # Validate filter wiring from router -> service (superadmin).
            if name is not None:
                assert name == "super"
            if user_id is not None:
                assert user_id == 101
            if shop_id is not None:
                assert shop_id == "SHOP001"
            if phone is not None:
                assert phone == "9999999999"
        return {
            "data": [
                {
                    "photo": "https://example.com/image.jpg",
                    "shop_name": "Super Market 1",
                    "user_id": 101,
                    "phone": "9999999999",
                    "location": "Main Street",
                    "geo_coordinates": {"type": "Point", "coordinates": [76.1, 10.1]},
                    "latitude": 10.1,
                    "longitude": 76.1,
                }
            ],
            "meta": {
                "currentPage": page,
                "limit": limit,
                "total": 1,
                "totalPages": 1,
            },
        }

    def get_supermarket_detail(self, user_id: int, role: Role):
        if user_id == 404:
            from app.api.exceptions.http_errors import ApiError

            raise ApiError(code="RESOURCE_NOT_FOUND", message="Supermarket not found", status_code=404)
        return {
            "shop_owner": {
                "shop_id": "SHOP001",
                "user_id": user_id,
                "shop_name": "Super Market 1",
                "phone": "9999999999",
                "email": "shop@example.com",
                "photo": "https://example.com/shop.jpg",
                "status": "active",
                "payment_status": "pending",
                "is_blocked": False,
                "geo_coordinates": {"type": "Point", "coordinates": [76.1, 10.1]},
                "upi_id": "shop@upi",
                "rating": 4.5,
                "delivery_time": 30,
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            },
            "address": {
                "street_address": "Main Street",
                "city": "Kochi",
                "state": "Kerala",
                "pincode": "682001",
                "latitude": 10.1,
                "longitude": 76.1,
            },
            "subscription": None,
            "promotion": None,
            "delivery_partners": [] if role == Role.PORTAL_USER else [{"delivery_partner_id": "DP001"}],
            "subscription_invoices": [],
            "daily_order_stats": None if role == Role.PORTAL_USER else [{"date": "2026-03-24"}],
        }


def test_supermarkets_requires_authentication():
    client = TestClient(app)
    response = client.get("/supermarkets")
    assert response.status_code == 401


def test_supermarkets_list_success_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)

    response = client.get("/supermarkets?page=1&limit=20")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["currentPage"] == 1
    assert body["meta"]["limit"] == 20
    assert body["meta"]["total"] == 1
    assert body["meta"]["totalPages"] == 1
    first = body["data"][0]
    assert set(first.keys()) == {
        "photo",
        "shop_name",
        "user_id",
        "phone",
        "location",
        "geo_coordinates",
        "latitude",
        "longitude",
    }

    app.dependency_overrides.clear()


def test_supermarkets_list_supports_search_filters():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)

    response = client.get(
        "/supermarkets?page=1&limit=20&name=super&user_id=101&shop_id=SHOP001&phone=9999999999"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["currentPage"] == 1
    assert body["meta"]["total"] == 1

    app.dependency_overrides.clear()


def test_supermarket_detail_not_found():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)

    response = client.get("/supermarkets/404")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    app.dependency_overrides.clear()


def test_supermarket_detail_for_portal_hides_partners_and_stats():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)

    response = client.get("/supermarkets/101")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["shop_owner"]["user_id"] == 101
    assert data["delivery_partners"] == []
    assert data["daily_order_stats"] is None
    app.dependency_overrides.clear()


def test_supermarket_detail_for_superadmin_includes_stats():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)

    response = client.get("/supermarkets/101")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["shop_owner"]["user_id"] == 101
    assert isinstance(data["delivery_partners"], list)
    assert data["daily_order_stats"] is not None
    app.dependency_overrides.clear()


def test_supermarket_detail_forbidden_for_other_roles():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="monitor-1", role=Role.MONITOR_APP
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)

    response = client.get("/supermarkets/101")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    app.dependency_overrides.clear()

