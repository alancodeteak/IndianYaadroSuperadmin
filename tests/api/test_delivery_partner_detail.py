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
    def get_delivery_partner_detail(self, delivery_partner_id: str):
        if delivery_partner_id == "missing":
            from app.api.exceptions.http_errors import ApiError
            from app.api.exceptions.error_codes import ErrorCode

            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return {
            "delivery_partner_id": delivery_partner_id,
            "shop_id": "SHOP001",
            "shop_name": "Super Market 1",
            "first_name": "John",
            "last_name": "Doe",
            "license_no": "LIC001",
            "license_image": "s3://license",
            "govt_id_image": None,
            "join_date": "2026-01-01T00:00:00+00:00",
            "is_blocked": False,
            "current_status": "idle",
            "order_count": 0,
            "age": 25,
            "phone1": "9999999999",
            "phone2": None,
            "email": None,
            "online_status": "offline",
            "rating": None,
            "photo": "delivery_partners/DP001/photo.jpg",
            "photo_url": "https://example.com/photo.jpg",
            "device_token": None,
            "device_id": None,
            "last_login": None,
            "last_order": None,
            "vehicle_detail": None,
            "total_bonus": 0,
            "total_penalty": 0,
            "liquid_cash": "0",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "is_deleted": False,
        }


def test_delivery_partner_detail_requires_authentication():
    client = TestClient(app)
    resp = client.get("/delivery-partners/DP001")
    assert resp.status_code == 401


def test_delivery_partner_detail_forbidden_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.get("/delivery-partners/DP001")
    assert resp.status_code == 403

    app.dependency_overrides = {}


def test_delivery_partner_detail_success_for_superadmin():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.get("/delivery-partners/DP001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"] is None
    assert body["data"]["delivery_partner_id"] == "DP001"
    assert body["data"]["shop_id"] == "SHOP001"
    assert body["data"]["shop_name"] == "Super Market 1"

    app.dependency_overrides = {}


def test_delivery_partner_detail_not_found_is_mapped():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.get("/delivery-partners/missing")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    app.dependency_overrides = {}

