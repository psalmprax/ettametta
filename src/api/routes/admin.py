import logging
import os
import re
import shutil
import threading
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, status, UploadFile, File
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from api.utils.database import get_db
from api.utils.user_models import UserDB, UserRole
from api.routes.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from api.utils.audit_service import audit_service

router = APIRouter(prefix="/admin", tags=["Admin Operations"])
logger = logging.getLogger(__name__)

def admin_required(current_user: UserDB = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this operation."
        )
    return current_user

@router.get("/system/env")
async def get_env_keys(current_user: UserDB = Depends(admin_required)):
    """
    Lists the keys present in the current .env file.
    Values are redacted for security.
    """
    env_path = ".env"
    if not os.path.exists(env_path):
        return {"message": ".env file not found", "keys": []}
    
    keys = []
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key = line.split("=")[0]
                keys.append(key)
    
    return {"keys": keys, "count": len(keys)}

@router.post("/system/env/upload")
async def upload_env_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserDB = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """
    Securely uploads and replaces the system .env file.
    Includes granular key-value validation and automatic backup.
    """
    # 1. Basic Validation: Filename and Content type
    if not file.filename.endswith(".env") and file.filename != ".env":
         # We allow files named like "production.env" as input but they will save as ".env"
         pass

    content = await file.read()
    decoded_content = content.decode("utf-8")
    
    # 2. Granular Validation
    lines = decoded_content.splitlines()
    valid_lines = []
    errors = []
    
    # Simple regex for KEY=VALUE pairs, allowing comments and empty lines
    # Keys must be alphanumeric/underscore
    kv_pattern = re.compile(r"^[A-Z0-9_]+=[^#]*")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            valid_lines.append(line)
            continue
            
        if kv_pattern.match(line):
            valid_lines.append(line)
        else:
            errors.append(f"Line {i+1}: Invalid format. Expected KEY=VALUE. Got: '{line[:30]}...'")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Validation failed in .env file", "errors": errors}
        )

    # 3. Defensive Backup
    env_path = ".env"
    if os.path.exists(env_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f".env.bak_{timestamp}"
        shutil.copy(env_path, backup_path)
        logger.info(f"📦 Admin: Created environment backup at {backup_path}")

    # 4. Persistence
    with open(env_path, "w") as f:
        f.write("\n".join(valid_lines))
    
    # 5. Hot-swap (Current Process Only)
    if load_dotenv:
        load_dotenv(env_path, override=True)
        logger.info("⚡ Admin: Environment hot-swapped for current API process.")
    
    # 6. Audit Logging
    await audit_service.log(
        action="ADMIN_ENV_UPLOAD",
        user_id=current_user.id,
        resource_type="SYSTEM",
        resource_id="ENV_FILE",
        details={"filename": file.filename, "backup_created": True},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db,
    )

    return {
        "message": "System environment (.env) updated and hot-swapped.",
        "backup_created": True,
        "note": "A full system restart is recommended to synchronize Workers and other microservices."
    }

@router.post("/system/restart")
async def restart_system(
    request: Request,
    current_user: UserDB = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers a controlled shutdown of the API process. 
    Requires 'restart: always' in docker-compose.yml to effect a reboot.
    """
    await audit_service.log(
        action="ADMIN_SYSTEM_RESTART",
        user_id=current_user.id,
        resource_type="SYSTEM",
        resource_id="API_NODE",
        details={"initiated_by": current_user.username},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db,
    )

    def kill_process():
        time.sleep(2)
        logger.warning("🛑 Admin Protocol: Terminating process for lifecycle reboot...")
        os._exit(0)

    threading.Thread(target=kill_process, daemon=True).start()

    return {
        "message": "System restart initiated. The API will be offline momentarily.",
        "estimated_downtime": "5-15 seconds"
    }
