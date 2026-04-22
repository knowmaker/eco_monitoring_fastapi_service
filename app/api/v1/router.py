from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.device_state import router as device_state_router
from app.api.v1.endpoints.dust_state import router as dust_state_router
from app.api.v1.endpoints.gas_sensors import router as gas_sensors_router
from app.api.v1.endpoints.gas_state import router as gas_state_router
from app.api.v1.endpoints.ivtm_state import router as ivtm_state_router
from app.api.v1.endpoints.meteo_state import router as meteo_state_router
from app.api.v1.endpoints.monitoring_posts import router as monitoring_posts_router
from app.api.v1.endpoints.plc_state import router as plc_state_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(monitoring_posts_router)
api_router.include_router(plc_state_router)
api_router.include_router(device_state_router)
api_router.include_router(gas_state_router)
api_router.include_router(gas_sensors_router)
api_router.include_router(dust_state_router)
api_router.include_router(meteo_state_router)
api_router.include_router(ivtm_state_router)
