"""
Publish route package — split from the original monolithic publish.py.

Modules:
    oauth        — YouTube, TikTok, Instagram, X, LinkedIn OAuth flows
    publisher    — Core post, retry, package, auto-broadcast, platforms
    scheduler    — Schedule, list, cancel, suggested-times
    analytics    — Comments, metrics sync, jobs, history
    accounts     — List / unlink social accounts
    opencli      — Chrome-session-based publishing via opencli-rs
"""

from fastapi import APIRouter

router = APIRouter(prefix="/publish", tags=["Publishing"])

from . import oauth, publisher, scheduler, analytics, accounts, opencli

router.include_router(oauth.router)
router.include_router(publisher.router)
router.include_router(scheduler.router)
router.include_router(analytics.router)
router.include_router(accounts.router)
router.include_router(opencli.router)
