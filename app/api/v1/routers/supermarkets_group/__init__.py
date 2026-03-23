from app.api.v1.routers.supermarkets_group.supermarkets_routes import (
    router as supermarkets_router,
)
from app.api.v1.routers.supermarkets_group.supermarkets_add_routes import (
    router as supermarkets_add_router,
)

__all__ = ["supermarkets_router", "supermarkets_add_router"]
