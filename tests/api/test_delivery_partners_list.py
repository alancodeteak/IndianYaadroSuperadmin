from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.api.deps import get_delivery_partner_service, require_authenticated
from app.domain.enums.roles import Role
from app.main import app


@dataclass
class _UserStub:
    user_id: str
    role: Role


class _DeliveryPartnerServiceStub:
    def list_delivery_partners(
        self,
        page: int,
        limit: int,
        *,
        include_deleted: bool = True,
        name: str | None = None,
        delivery_partner_id: str | None = None,
        shop_id: str | None = None,
        shop_name: str | None = None,
        phone: str | None = None,
        current_status: str | None = None,
        online_status: str | None = None,
    ):
        assert isinstance(page, int)
        assert isinstance(limit, int)
        assert isinstance(include_deleted, bool)
        if name is not None:
            assert name == "john"
        if delivery_partner_id is not None:
            assert delivery_partner_id == "DP001"
        if shop_id is not None:
            assert shop_id == "SHOP001"
        if shop_name is not None:
            assert shop_name == "dmart"
        if phone is not None:
            assert phone == "9999999999"
        if current_status is not None:
            assert current_status == "idle"
        if online_status is not None:
            assert online_status == "online"
        return {
            "data": [
                {
                    "delivery_partner_id": "DP001",
                    "shop_id": "SHOP001",
                    "shop_name": "Super Market 1",
                    "name": "John Doe",
                    "phone": "9999999999",
                    "photo": "delivery_partners/DP001/photo.jpg",
                    "photo_url": "https://example.com/photo.jpg",
                    "is_deleted": False,
                }
            ],
            "meta": {
                "currentPage": page,
                "limit": limit,
                "total": 1,
                "totalPages": 1,
            },
        }


def test_delivery_partners_requires_authentication():
    client = TestClient(app)
    resp = client.get("/delivery-partners?page=1&limit=20")
    assert resp.status_code == 401


def test_delivery_partners_forbidden_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.get("/delivery-partners?page=1&limit=20")
    assert resp.status_code == 403

    app.dependency_overrides = {}


def test_delivery_partners_list_success_for_superadmin():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.get(
        "/delivery-partners?page=1&limit=20&name=john&delivery_partner_id=DP001&shop_id=SHOP001&shop_name=dmart&phone=9999999999&current_status=idle&online_status=online"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["currentPage"] == 1
    assert body["meta"]["limit"] == 20
    assert body["meta"]["total"] == 1
    assert body["meta"]["totalPages"] == 1
    first = body["data"][0]
    assert set(first.keys()) == {
        "delivery_partner_id",
        "shop_id",
        "shop_name",
        "name",
        "phone",
        "photo",
        "photo_url",
        "is_deleted",
    }

    app.dependency_overrides = {}

