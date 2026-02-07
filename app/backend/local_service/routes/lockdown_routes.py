"""Lockdown & Intervention Endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

try:
    from ..lockdown_manager import get_lockdown_manager
except ImportError:
    from lockdown_manager import get_lockdown_manager

router = APIRouter(prefix="/api", tags=["Lockdown"])


class LockdownSettings(BaseModel):
    warning_interval_seconds: int
    negotiation_interval_seconds: int


@router.get("/dev/lockdown_settings")
async def get_lockdown_settings():
    """Get the current configuration for intervention intervals."""
    manager = get_lockdown_manager()
    return manager.get_settings()


@router.post("/dev/lockdown_settings")
async def update_lockdown_settings(settings: LockdownSettings):
    """Update the configuration for intervention intervals."""
    manager = get_lockdown_manager()
    manager.save_settings(settings.model_dump())
    return {"status": "success", "settings": manager.get_settings()}


@router.get("/lockdown/status")
async def get_lockdown_status():
    """Check if the system is currently in lockdown mode."""
    manager = get_lockdown_manager()
    return {"is_locked_down": manager.get_status()}


@router.post("/lockdown/trigger")
async def trigger_lockdown():
    """Trigger the system lockdown (called by monitoring service)."""
    manager = get_lockdown_manager()
    manager.set_lockdown(True)
    return {"status": "success", "message": "Lockdown initiated"}


@router.post("/lockdown/unlock")
async def unlock_lockdown():
    """Unlock the system (e.g., called after lesson completion)."""
    manager = get_lockdown_manager()
    manager.set_lockdown(False)
    return {"status": "success", "message": "Lockdown lifted"}
