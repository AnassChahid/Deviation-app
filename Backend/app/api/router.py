from fastapi import APIRouter

from app.api.routes import auth, deviations, deviation_types, health, notifications, qcs, users, vessels


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(deviation_types.router, prefix="/deviation-types", tags=["deviation types"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"])
api_router.include_router(qcs.router, prefix="/qcs", tags=["qcs"])
api_router.include_router(deviations.router, prefix="/deviations", tags=["deviations"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
