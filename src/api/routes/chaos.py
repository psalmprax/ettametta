from fastapi import APIRouter, Depends
from src.api.utils.auth import admin_required
from src.services.infrastructure.chaos_utility import base_chaos_service
from src.services.analytics.consistency_sentinel import base_consistency_sentinel

router = APIRouter(prefix="/v1/chaos", tags=["Chaos"])


@router.post("/latency")
async def inject_latency(service: str, delay_ms: int, current_user=Depends(admin_required)):
    """Adds artificial delay to a service."""
    await base_chaos_service.inject_latency(service, delay_ms)
    return {"status": "injected", "service": service, "delay": f"{delay_ms}ms"}


@router.post("/crash")
async def simulate_crash(current_user=Depends(admin_required)):
    """Simulates a worker crash notification."""
    await base_chaos_service.simulate_worker_crash()
    return {"status": "crash_simulated"}


@router.post("/exhaustion")
async def induce_exhaustion(platform: str, current_user=Depends(admin_required)):
    """Fakes a 429/403 for a specific platform API."""
    await base_chaos_service.induce_api_exhaustion(platform)
    return {"status": "exhaustion_active", "platform": platform}


@router.post("/scenario")
async def run_chaos_scenario(name: str, current_user=Depends(admin_required)):
    """Executes an orchestrated Killer Combo scenario (blackout/cascade/storm)."""
    report = await base_chaos_service.run_scenario(name)
    return report


@router.post("/continuous/start")
async def start_continuous_chaos(intensity: str = "medium", duration_minutes: int = 30, current_user=Depends(admin_required)):
    """Starts a background continuous chaos injection loop."""
    result = await base_chaos_service.start_continuous_chaos(
        intensity, duration_minutes
    )
    return result


@router.post("/continuous/stop")
async def stop_continuous_chaos(current_user=Depends(admin_required)):
    """Stops continuous chaos and clears all active faults."""
    result = await base_chaos_service.stop_continuous_chaos()
    return result


@router.post("/clear")
async def clear_all_faults(current_user=Depends(admin_required)):
    """Emergency: removes all active chaos faults from the system."""
    await base_chaos_service.clear_all_faults()
    return {"status": "all_faults_cleared"}


@router.get("/report")
async def get_chaos_report(current_user=Depends(admin_required)):
    """Returns current chaos state, sentinel health, and recovery status."""
    from src.services.infrastructure.recovery_service import base_recovery_service

    return {
        "chaos": base_chaos_service.get_chaos_report(),
        "sentinel": base_consistency_sentinel.get_status(),
        "recovery": base_recovery_service.get_status(),
    }
