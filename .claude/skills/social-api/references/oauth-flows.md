# OAuth Flow Details by Platform

All flows are defined in `src/api/routes/publish/oauth.py`. Tokens are stored via `TokenManager` in `src/services/optimization/auth.py`.

## YouTube

- **Initiate:** `GET /publish/auth/youtube`
- **Library:** `google_auth_oauthlib.flow.Flow`
- **Scopes:** `youtube.upload`, `yt-analytics.readonly`
- **Callback:** `GET /publish/auth/youtube/callback`
- **Token exchange:** `flow.fetch_token(code=code)`
- **Refresh:** `https://oauth2.googleapis.com/token`
- **Storage:** `token_manager.store_token("youtube", access_token, refresh_token, expires_in)`

## TikTok

- **Initiate:** `GET /publish/auth/tiktok`
- **Redirect:** `https://www.tiktok.com/v2/auth/authorize`
- **Scopes:** `video.upload`, `user.info.basic`
- **Callback:** `GET /publish/auth/tiktok/callback`
- **Token exchange:** `POST https://open.tiktokapis.com/v2/oauth/token/`
- **Refresh:** `POST https://open.tiktokapis.com/v2/oauth/token/` with `grant_type=refresh_token`

## Instagram (Meta)

- **Initiate:** `GET /publish/auth/instagram`
- **Redirect:** `https://api.instagram.com/oauth/authorize`
- **Scopes:** `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`, `pages_manage_posts`
- **Callback:** `GET /publish/auth/instagram/callback`
- **Token exchange:** `POST https://api.instagram.com/oauth/access_token`
- **Refresh:** Meta's `fb_exchange_token` mechanism at `https://graph.facebook.com/v18.0/oauth/access_token`

## Facebook

- **No dedicated endpoint** — uses the Instagram/Meta OAuth flow
- **Publishing:** Uses the same Meta app credentials (`meta_app_id` / `meta_app_secret`)

## X (Twitter)

- **Initiate:** `GET /publish/auth/x`
- **Redirect:** `https://twitter.com/i/oauth2/authorize`
- **Scopes:** `tweet.read`, `tweet.write`, `users.read`, `offline.access`
- **Callback:** `GET /publish/auth/x/callback`
- **Token exchange:** `POST https://api.twitter.com/2/oauth2/token`
- **Refresh:** `POST https://api.twitter.com/2/oauth2/token` with `grant_type=refresh_token`
- **Note:** Uses PKCE (code_verifier + code_challenge)

## LinkedIn

- **Initiate:** `GET /publish/auth/linkedin`
- **Redirect:** `https://www.linkedin.com/oauth/v2/authorization`
- **Scopes:** `r_liteprofile`, `r_emailaddress`, `w_member_social`
- **Callback:** `GET /publish/auth/linkedin/callback`
- **Token exchange:** `POST https://www.linkedin.com/oauth/v2/accessToken`
- **Refresh:** `POST https://www.linkedin.com/oauth/v2/accessToken`
- **Bug:** Callback does not store `refresh_token`

## Snapchat (BROKEN)

- **Initiate:** `GET /publish/auth/snapchat`
- **Redirect:** `https://accounts.snapchat.com/accounts/oauth2/auth`
- **Callback:** `GET /publish/auth/snapchat/callback`
- **Token exchange:** `POST https://accounts.snapchat.com/accounts/oauth2/token`
- **Bug:** `settings.SNAPCHAT_REDIRECT_URI` is not defined — will raise `AttributeError`

## Twitch (BROKEN)

- **Initiate:** `GET /publish/auth/twitch`
- **Redirect:** `https://id.twitch.tv/oauth2/authorize`
- **Scopes:** `channel:manage:videos`, `user:edit:broadcast`
- **Callback:** `GET /publish/auth/twitch/callback`
- **Token exchange:** `POST https://id.twitch.tv/oauth2/token`
- **Bug:** `settings.TWITCH_REDIRECT_URI` is not defined — will raise `AttributeError`

## Token Storage

All tokens are:
1. Encrypted with Fernet (derived from `SECRET_KEY`)
2. Stored in the `SocialAccount` DB table
3. Retrieved via `token_manager.get_auth_headers(platform, user_id)`
4. Auto-refreshed via `token_manager.ensure_valid_token(platform, user_id)` with 5-minute early-expiry buffer
