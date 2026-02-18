# ViralForge Deployment & Credential Guide

This guide provides step-by-step instructions for generating the required production credentials for ViralForge.

## 1. Google OAuth Credentials (YouTube Publishing)

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new Project (e.g., "ViralForge-Prod").
3.  Navigate to **APIs & Services > Library**.
4.  Enable the **YouTube Data API v3**.
5.  Navigate to **APIs & Services > OAuth consent screen**.
    *   Select **External** (unless you have a G-Suite org).
    *   Fill in app details.
    *   Add test users (your email) while in testing mode.
6.  Navigate to **APIs & Services > Credentials**.
7.  Click **Create Credentials > OAuth client ID**.
    *   Application type: **Web application**.
    *   Name: "ViralForge API".
    *   **Authorized redirect URIs**:
        *   `https://your-domain.com/publish/auth/youtube/callback`
        *   (If testing locally: `http://localhost:8000/publish/auth/youtube/callback`)
8.  Copy the **Client ID** and **Client Secret**.
9.  Add them to your `.env.production` file:
    ```bash
    GOOGLE_CLIENT_ID="your_client_id"
    GOOGLE_CLIENT_SECRET="your_client_secret"
    ```

## 2. TikTok API Credentials

1.  Register as a developer on the [TikTok for Developers](https://developers.tiktok.com/) portal.
2.  Create a new App.
3.  In "Products", add **Share Kit** and **Login Kit**.
4.  Copy the **Client Key** and **Client Secret**.
5.  In the app settings, set the **Redirect URI**:
    *   `https://your-domain.com/publish/auth/tiktok/callback`
6.  Submit for review (TikTok requires app review for production API access).
7.  Add keys to `.env.production`:
    ```bash
    TIKTOK_CLIENT_KEY="your_client_key"
    TIKTOK_CLIENT_SECRET="your_client_secret"
    ```

## 3. AWS S3 (Video Storage)

1.  Log in to [AWS Console](https://aws.amazon.com/console/).
2.  Go to **S3** and create a new bucket (e.g., `viral-forge-videos-prod`).
    *   Uncheck "Block all public access" if you need public URLs, OR better, use CloudFront.
    *   Enable CORS configuration if uploading directly from frontend (optional).
3.  Go to **IAM** and create a new User (e.g., `viral-forge-bot`).
    *   Attach policy: `AmazonS3FullAccess` (or scope it down to your bucket).
4.  Create **Access Keys** for this user.
5.  Add to `.env.production`:
    ```bash
    AWS_ACCESS_KEY_ID="AKIA..."
    AWS_SECRET_ACCESS_KEY="secret..."
    AWS_REGION="us-east-1"
    AWS_STORAGE_BUCKET_NAME="viral-forge-videos-prod"
    ```

## 4. Final Deployment Steps

1.  Copy the template:
    ```bash
    cp .env.production.template .env.production
    ```
2.  Fill in all values.
3.  Update `PRODUCTION_DOMAIN` in settings to match your actual domain.
4.  Deploy using Docker:
    ```bash
    docker-compose -f docker-compose.yml --env-file .env.production up -d --build
    ```
