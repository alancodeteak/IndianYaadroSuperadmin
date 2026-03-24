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
    def list_supermarkets(self, page: int, limit: int):
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

