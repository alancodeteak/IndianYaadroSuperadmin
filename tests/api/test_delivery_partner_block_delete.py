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
    def set_delivery_partner_blocked(self, delivery_partner_id: str, *, blocked: bool):
        if delivery_partner_id == "missing":
            from app.api.exceptions.http_errors import ApiError
            from app.api.exceptions.error_codes import ErrorCode

            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return {"delivery_partner_id": delivery_partner_id, "is_blocked": blocked}

    def delete_delivery_partner(self, delivery_partner_id: str):
        if delivery_partner_id == "missing":
            from app.api.exceptions.http_errors import ApiError
            from app.api.exceptions.error_codes import ErrorCode

            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return {"delivery_partner_id": delivery_partner_id, "deleted": True}

    def restore_delivery_partner(self, delivery_partner_id: str):
        if delivery_partner_id == "missing":
            from app.api.exceptions.http_errors import ApiError
            from app.api.exceptions.error_codes import ErrorCode

            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return {"delivery_partner_id": delivery_partner_id, "restored": True}


def test_delivery_partner_block_requires_authentication():
    client = TestClient(app)
    resp = client.patch("/delivery-partners/DP001/block", json={"blocked": True})
    assert resp.status_code == 401


def test_delivery_partner_block_forbidden_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.patch("/delivery-partners/DP001/block", json={"blocked": True})
    assert resp.status_code == 403

    app.dependency_overrides = {}


def test_delivery_partner_block_success_for_superadmin():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.patch("/delivery-partners/DP001/block", json={"blocked": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == {"delivery_partner_id": "DP001", "is_blocked": True}
    assert body["meta"] is None

    app.dependency_overrides = {}


def test_delivery_partner_block_not_found_is_mapped():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.patch("/delivery-partners/missing/block", json={"blocked": True})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    app.dependency_overrides = {}


def test_delivery_partner_delete_requires_authentication():
    client = TestClient(app)
    resp = client.delete("/delivery-partners/DP001")
    assert resp.status_code == 401


def test_delivery_partner_delete_forbidden_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.delete("/delivery-partners/DP001")
    assert resp.status_code == 403

    app.dependency_overrides = {}


def test_delivery_partner_delete_success_for_superadmin():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.delete("/delivery-partners/DP001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == {"delivery_partner_id": "DP001", "deleted": True}
    assert body["meta"] is None

    app.dependency_overrides = {}


def test_delivery_partner_delete_not_found_is_mapped():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.delete("/delivery-partners/missing")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    app.dependency_overrides = {}


def test_delivery_partner_restore_requires_authentication():
    client = TestClient(app)
    resp = client.patch("/delivery-partners/DP001/restore")
    assert resp.status_code == 401


def test_delivery_partner_restore_forbidden_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.patch("/delivery-partners/DP001/restore")
    assert resp.status_code == 403

    app.dependency_overrides = {}


def test_delivery_partner_restore_success_for_superadmin():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.patch("/delivery-partners/DP001/restore")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == {"delivery_partner_id": "DP001", "restored": True}
    assert body["meta"] is None

    app.dependency_overrides = {}


def test_delivery_partner_restore_not_found_is_mapped():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_delivery_partner_service] = lambda: _DeliveryPartnerServiceStub()
    client = TestClient(app)

    resp = client.patch("/delivery-partners/missing/restore")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    app.dependency_overrides = {}

