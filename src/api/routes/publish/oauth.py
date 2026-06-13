"""
OAuth routes for social platform authentication.
Supports YouTube, TikTok, Instagram, X, and LinkedIn OAuth flows.

Extracted from the original monolithic publish.py.
"""

import json
import base64
import secrets
import urllib.parse
import datetime
import os
import logging
import asyncio
import httpx

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from src.api.config import settings
from src.api.utils.auth import get_current_user
from src.api.utils.vault import get_secret, get_secret_async
from src.api.utils.user_models import UserDB
from src.api.utils.api_responses import success_response
from src.services.optimization.auth import token_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── YouTube OAuth Scopes ───────────────────────────────────────────────

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


# ─── YouTube OAuth ──────────────────────────────────────────────────────


@router.get("/auth/youtube")
async def auth_youtube(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the YouTube OAuth flow with user_id state isolation.
    """
    client_id = await get_secret_async("google_client_id")
    client_secret = await get_secret_async("google_client_secret")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400, detail="Google OAuth Credentials not configured in Vault."
        )

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_YOUTUBE_REDIRECT_URI

    # Generate a manual code_verifier for PKCE pass-through
    code_verifier = secrets.token_urlsafe(64)
    flow.code_verifier = code_verifier

    state_data = {
        "user_id": current_user.id,
        "csrf": secrets.token_hex(16),
        "code_verifier": code_verifier,
    }
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    authorization_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", state=state
    )
    return success_response(data={"url": authorization_url})


@router.get("/auth/youtube/callback")
async def auth_youtube_callback(
    state: str, code: str | None = None, error: str | None = None
):
    """
    Handles the YouTube OAuth callback with user isolation and robust error logging.
    """
    logger.info(
        f"YouTube Callback received: state_len={len(state)}, code_present={bool(code)}, error={error}"
    )

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth Error from Google: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code from Google")

    try:
        state_padded = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(state_padded.encode()).decode())
        user_id = state_data.get("user_id")
        code_verifier = state_data.get("code_verifier")
        logger.info(
            f"Decoded State: user_id={user_id}, has_verifier={bool(code_verifier)}"
        )
    except Exception as e:
        logger.exception(f"Failed to decode OAuth state: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Allow insecure transport for development/local sslip.io setups if using HTTP
    if settings.PRODUCTION_DOMAIN.startswith("http://"):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        logger.warning("OAUTHLIB_INSECURE_TRANSPORT enabled for HTTP session")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": await get_secret_async("google_client_id"),
                "client_secret": await get_secret_async("google_client_secret"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=YOUTUBE_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_YOUTUBE_REDIRECT_URI
    logger.info(f"Using Redirect URI for token exchange: {flow.redirect_uri}")

    # Restore the code_verifier for PKCE validation
    if code_verifier:
        flow.code_verifier = code_verifier

    try:
        await asyncio.to_thread(flow.fetch_token, code=code)
    except Exception as e:
        logger.exception(f"YouTube Token Exchange Failed: {str(e)}", exc_info=True)
        error_detail = str(e)
        if "redirect_uri_mismatch" in error_detail.lower():
            error_detail = f"Redirect URI Mismatch. Check if {flow.redirect_uri} is registered in Google Cloud Console."

        raise HTTPException(
            status_code=400, detail=f"Token exchange failed: {error_detail}"
        )

    credentials = flow.credentials
    await token_manager.store_token(
        "youtube",
        user_id,
        {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_type": "Bearer",
            "expires_in": credentials.expiry.replace(
                tzinfo=datetime.timezone.utc
            ).timestamp()
            - datetime.datetime.now(datetime.timezone.utc).timestamp()
            if credentials.expiry
            else 3600,
        },
    )

    logger.info(f"Successfully stored YouTube token for user_id={user_id}")

    # Redirect back to the frontend dashboard
    dashboard_url = (
        settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
        or "http://localhost:7202"
    )
    return RedirectResponse(
        url=f"{dashboard_url}/publishing?success=true&platform=youtube"
    )


# ─── TikTok OAuth ───────────────────────────────────────────────────────


@router.get("/auth/tiktok")
async def auth_tiktok(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the TikTok OAuth flow with user_id state isolation.
    """
    client_key = await get_secret_async("tiktok_client_key")
    redirect_uri = settings.TIKTOK_REDIRECT_URI

    if not client_key:
        raise HTTPException(
            status_code=400, detail="TikTok Client Key not configured in Vault."
        )

    scope = "video.upload,user.info.basic"

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    params = {
        "client_key": client_key,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://www.tiktok.com/v2/auth/authorize?{query_string}"
    return success_response(data={"url": auth_url})


@router.get("/auth/tiktok/callback")
async def auth_tiktok_callback(code: str, state: str):
    """
    Handles the TikTok OAuth callback and exchanges code for a real token.
    """
    try:
        state_padded = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(state_padded.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    url = "https://open.tiktokapis.com/v2/oauth/token/"

    data = {
        "client_key": await get_secret_async("tiktok_client_key"),
        "client_secret": await get_secret_async("tiktok_client_secret"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.TIKTOK_REDIRECT_URI,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"TikTok Auth Failed: {token_data.get('error_description', 'Unknown error')}",
                )

            # Fetch the TikTok user's display name via /v2/user/info/ to store as username
            # (reuse the existing client instead of creating a nested one)
            try:
                user_headers = {
                    "Authorization": f"Bearer {token_data['access_token']}"
                }
                user_resp = await client.get(
                    "https://open.tiktokapis.com/v2/user/info/?fields=display_name,open_id",
                    headers=user_headers,
                )
                if user_resp.status_code == 200:
                    user_data = user_resp.json()
                    user_info = user_data.get("data", {}).get("user", {})
                    token_data["username"] = user_info.get("display_name", token_data.get("open_id", "tiktok_user"))
                else:
                    token_data["username"] = token_data.get("open_id", "tiktok_user")
            except Exception:
                token_data["username"] = token_data.get("open_id", "tiktok_user")

            await token_manager.store_token(
                "tiktok",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "username": token_data.get("username"),
                    "open_id": token_data.get("open_id"),
                    "expires_in": token_data.get("expires_in", 3600),
                    "scope": token_data.get("scope"),
                },
            )

            # Redirect back to the frontend dashboard
            dashboard_url = (
                settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
                or "http://localhost:7202"
            )
            return RedirectResponse(
                url=f"{dashboard_url}/publishing?success=true&platform=tiktok"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Token exchange failed: {str(e)}")


# ─── Instagram/Facebook OAuth (via Meta) ──────────────────────────────


@router.get("/auth/instagram")
async def auth_instagram(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the Instagram/Facebook OAuth flow with user_id state isolation.
    """
    app_id = await get_secret_async("meta_app_id")
    redirect_uri = settings.META_REDIRECT_URI

    if not app_id:
        raise HTTPException(
            status_code=400, detail="Meta App ID not configured in Vault."
        )

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    # Instagram scope for video upload
    # Instagram Graph API requires Facebook Login for Business/Creator account access.
    # The Instagram Basic Display API (api.instagram.com/oauth/authorize) does NOT
    # support pages_* or instagram_content_publish scopes — only ig_basic and ig_content_publish.
    # To publish via Instagram Graph API, users must have an Instagram Business Account
    # connected to a Facebook Page, and we use Facebook Login to get the required tokens.
    scope = "instagram_basic,pages_read_engagement,pages_manage_posts,instagram_content_publish"

    params = {
        "client_id": app_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    # Use Facebook Login dialog (supports Instagram + Pages scopes) 
    auth_url = f"https://www.facebook.com/v20.0/dialog/oauth?{query_string}"
    return success_response(data={"url": auth_url})


@router.get("/auth/instagram/callback")
async def auth_instagram_callback(code: str, state: str):
    """Handles the Instagram OAuth callback"""

    try:
        state_padded = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(state_padded.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    app_id = await get_secret_async("meta_app_id")
    app_secret = await get_secret_async("meta_app_secret")
    redirect_uri = settings.META_REDIRECT_URI

    # Exchange Facebook Login code for a long-lived User Access Token
    # (Not the Instagram Basic Display token endpoint)
    url = "https://graph.facebook.com/v20.0/oauth/access_token"
    data = {
        "client_id": app_id,
        "client_secret": app_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                error_detail = token_data.get("error", {}).get(
                    "message", token_data.get("error_message", "Unknown error")
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Instagram/Facebook Auth Failed: {error_detail}",
                )

            # Since we're using Facebook Login, fetch the user's name from Facebook Graph API
            # (graph.instagram.com/me only works with Instagram Basic Display tokens, not FB tokens)
            try:
                me_resp = await client.get(
                    "https://graph.facebook.com/v20.0/me",
                    params={
                        "fields": "name,id",
                        "access_token": token_data["access_token"],
                    },
                )
                if me_resp.status_code == 200:
                    me_data = me_resp.json()
                    token_data["username"] = me_data.get("name", f"ig_user_{me_data.get('id', 'unknown')}")
                else:
                    token_data["username"] = "instagram_user"
            except Exception:
                token_data["username"] = "instagram_user"

            await token_manager.store_token(
                "instagram",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "username": token_data.get("username"),
                    "instagram_user_id": token_data.get("user_id"),
                    "expires_in": token_data.get("expires_in", 3600),
                },
            )

            # Redirect back to the frontend dashboard
            dashboard_url = (
                settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
                or "http://localhost:7202"
            )
            return RedirectResponse(
                url=f"{dashboard_url}/publishing?success=true&platform=instagram"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Token exchange failed: {str(e)}")


# ─── X (Twitter) OAuth ──────────────────────────────────────────────────


@router.get("/auth/x")
async def auth_x(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the X (Twitter) OAuth flow with user_id state isolation.
    """
    client_id = await get_secret_async("twitter_client_id")
    redirect_uri = settings.TWITTER_REDIRECT_URI

    if not client_id:
        raise HTTPException(
            status_code=400, detail="Twitter Client ID not configured in Vault."
        )

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    scope = "tweet.read tweet.write users.read offline.access"

    params = {
        "client_id": client_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://twitter.com/i/oauth2/authorize?{query_string}"
    return success_response(data={"url": auth_url})


@router.get("/auth/x/callback")
async def auth_x_callback(code: str, state: str):
    """Handles the X (Twitter) OAuth callback"""

    try:
        state_padded = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(state_padded.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = await get_secret_async("twitter_client_id")
    client_secret = await get_secret_async("twitter_client_secret")
    redirect_uri = settings.TWITTER_REDIRECT_URI

    url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"X Auth Failed: {token_data.get('error_description', 'Unknown error')}",
                )

            # Fetch the X username via /2/users/me to store as account name
            try:
                user_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                me_resp = await client.get(
                    "https://api.twitter.com/2/users/me",
                    headers=user_headers,
                )
                if me_resp.status_code == 200:
                    me_data = me_resp.json()
                    token_data["username"] = me_data.get("data", {}).get("username", "x_user")
                else:
                    token_data["username"] = "x_user"
            except Exception:
                token_data["username"] = "x_user"

            await token_manager.store_token(
                "x",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "username": token_data.get("username"),
                    "expires_in": token_data.get("expires_in", 3600),
                },
            )

            # Redirect back to the frontend dashboard
            dashboard_url = (
                settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
                or "http://localhost:7202"
            )
            return RedirectResponse(
                url=f"{dashboard_url}/publishing?success=true&platform=x"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Token exchange failed: {str(e)}")


# ─── LinkedIn OAuth ────────────────────────────────────────────────────


@router.get("/auth/linkedin")
async def auth_linkedin(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the LinkedIn OAuth flow with user_id state isolation.
    """
    client_id = await get_secret_async("linkedin_client_id")
    redirect_uri = settings.LINKEDIN_REDIRECT_URI

    if not client_id:
        raise HTTPException(
            status_code=400, detail="LinkedIn Client ID not configured in Vault."
        )

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    scope = "r_liteprofile r_emailaddress w_member_social"

    params = {
        "client_id": client_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{query_string}"
    return success_response(data={"url": auth_url})


@router.get("/auth/linkedin/callback")
async def auth_linkedin_callback(code: str, state: str):
    """Handles the LinkedIn OAuth callback"""

    try:
        state_padded = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(state_padded.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = await get_secret_async("linkedin_client_id")
    client_secret = await get_secret_async("linkedin_client_secret")
    redirect_uri = settings.LINKEDIN_REDIRECT_URI

    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"LinkedIn Auth Failed: {token_data.get('error_description', 'Unknown error')}",
                )

            # Fetch the LinkedIn user's profile info.
            # LinkedIn's /v2/userinfo (OpenID Connect) returns `sub` — the LinkedIn member ID
            # needed for the `urn:li:person:{sub}` URN in upload API calls.
            # Also fetch display name for the accounts list.
            linkedin_sub = None
            try:
                user_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                me_resp = await client.get(
                    "https://api.linkedin.com/v2/userinfo",
                    headers=user_headers,
                )
                if me_resp.status_code == 200:
                    me_data = me_resp.json()
                    linkedin_sub = me_data.get("sub")
                    given = me_data.get("given_name", "")
                    family = me_data.get("family_name", "")
                    display_name = f"{given} {family}".strip()
                    # Store the linkedin sub (member ID) as username — this is what
                    # the upload endpoints need for urn:li:person:{sub}
                    token_data["username"] = linkedin_sub or display_name or "linkedin_user"
                else:
                    token_data["username"] = "linkedin_user"
            except Exception:
                token_data["username"] = "linkedin_user"

            await token_manager.store_token(
                "linkedin",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "username": token_data.get("username"),
                    "expires_in": token_data.get("expires_in", 3600),
                },
            )

            # Redirect back to the frontend dashboard
            dashboard_url = (
                settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
                or "http://localhost:7202"
            )
            return RedirectResponse(
                url=f"{dashboard_url}/publishing?success=true&platform=linkedin"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Token exchange failed: {str(e)}")


# ─── Snapchat OAuth ─────────────────────────────────────────────────


@router.get("/auth/snapchat")
async def auth_snapchat(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the Snapchat OAuth flow for Snap Kit / Snapchat Marketing API.
    """
    client_id = await get_secret_async("snapchat_client_id")
    redirect_uri = settings.SNAPCHAT_REDIRECT_URI

    if not client_id:
        raise HTTPException(
            status_code=400, detail="Snapchat Client ID not configured in Vault."
        )

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    scope = "snapchat-marketing-api"

    params = {
        "client_id": client_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://accounts.snapchat.com/accounts/oauth2/auth?{query_string}"
    return success_response(data={"url": auth_url})


@router.get("/auth/snapchat/callback")
async def auth_snapchat_callback(code: str, state: str):
    """Handles the Snapchat OAuth callback"""

    try:
        state_padded = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(state_padded.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = await get_secret_async("snapchat_client_id")
    client_secret = await get_secret_async("snapchat_client_secret")
    redirect_uri = settings.SNAPCHAT_REDIRECT_URI

    url = "https://accounts.snapchat.com/accounts/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Snapchat Auth Failed: {token_data.get('error_description', 'Unknown error')}",
                )

            await token_manager.store_token(
                "snapchat",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in", 3600),
                    "scope": token_data.get("scope"),
                },
            )

            return success_response(
                data={
                    "status": "success",
                    "message": "Snapchat authenticated successfully",
                    "user_id": user_id,
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Token exchange failed: {str(e)}")


# ─── Twitch OAuth ────────────────────────────────────────────────────


@router.get("/auth/twitch")
async def auth_twitch(current_user: UserDB = Depends(get_current_user)):
    """
    Starts the Twitch OAuth flow for video upload and channel management.
    """
    client_id = await get_secret_async("twitch_client_id")
    redirect_uri = settings.TWITCH_REDIRECT_URI

    if not client_id:
        raise HTTPException(
            status_code=400, detail="Twitch Client ID not configured in Vault."
        )

    state_data = {"user_id": current_user.id, "csrf": secrets.token_urlsafe(16)}
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    scope = "channel:manage:videos user:edit:broadcast"

    params = {
        "client_id": client_id,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }

    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://id.twitch.tv/oauth2/authorize?{query_string}"
    return success_response(data={"url": auth_url})


@router.get("/auth/twitch/callback")
async def auth_twitch_callback(code: str, state: str):
    """Handles the Twitch OAuth callback"""

    try:
        state_padded = state + '=' * (-len(state) % 4)
        state_data = json.loads(base64.urlsafe_b64decode(state_padded.encode()).decode())
        user_id = state_data.get("user_id")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = await get_secret_async("twitch_client_id")
    client_secret = await get_secret_async("twitch_client_secret")
    redirect_uri = settings.TWITCH_REDIRECT_URI

    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            token_data = response.json()

            if response.status_code != 200 or "access_token" not in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Twitch Auth Failed: {token_data.get('message', 'Unknown error')}",
                )

            await token_manager.store_token(
                "twitch",
                user_id,
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in", 3600),
                    "scope": token_data.get("scope"),
                },
            )

            return success_response(
                data={
                    "status": "success",
                    "message": "Twitch authenticated successfully",
                    "user_id": user_id,
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Token exchange failed: {str(e)}")
