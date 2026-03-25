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
    def delete_supermarket(self, user_id: int, role: Role):
        assert user_id == 321
        assert role == Role.SUPERADMIN
        return {"deleted": True, "user_id": user_id}

    def list_supermarkets(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def get_supermarket_detail(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def create_supermarket(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def update_supermarket(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


def test_supermarkets_delete_requires_authentication():
    client = TestClient(app)
    response = client.delete("/supermarkets/321")
    assert response.status_code == 401


def test_supermarkets_delete_forbidden_for_portal_user():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="portal-1", role=Role.PORTAL_USER
    )
    client = TestClient(app)
    response = client.delete("/supermarkets/321")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    app.dependency_overrides.clear()


def test_supermarkets_delete_forbidden_for_monitor_app():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="monitor-1", role=Role.MONITOR_APP
    )
    client = TestClient(app)
    response = client.delete("/supermarkets/321")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    app.dependency_overrides.clear()


def test_supermarkets_delete_success_superadmin_wiring():
    app.dependency_overrides[require_authenticated] = lambda: _UserStub(
        user_id="admin-1", role=Role.SUPERADMIN
    )
    app.dependency_overrides[get_shop_owner_service] = lambda: _ShopOwnerServiceStub()
    client = TestClient(app)
    response = client.delete("/supermarkets/321")
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True
    assert response.json()["data"]["user_id"] == 321
    app.dependency_overrides.clear()

