"""
Account management routes — list and unlink social accounts.

Extracted from the original monolithic publish.py.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB, UserRole
from src.api.utils.database import get_db
from src.api.utils.models import SocialAccount
from src.api.utils.api_responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/accounts")
async def list_accounts(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    try:
        stmt = select(SocialAccount)
        if current_user.role != UserRole.ADMIN:
            stmt = stmt.where(SocialAccount.user_id == current_user.id)
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        return success_response(
            data=[
                {
                    "id": a.id,
                    "platform": a.platform,
                    "username": a.username,
                    "updated_at": a.updated_at,
                }
                for a in accounts
            ]
        )
    finally:
        pass


@router.delete("/account/{account_id}")
async def delete_account(
    account_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        stmt = select(SocialAccount).where(SocialAccount.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        if account.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this account"
            )

        await db.delete(account)
        await db.commit()
        return success_response(
            data={"status": "success", "message": "Account unlinked"}
        )
    finally:
        pass
