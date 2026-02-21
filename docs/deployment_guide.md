# ViralForge: E2E Configuration Guide

This guide provides step-by-step instructions for obtaining the necessary credentials to enable full end-to-end (E2E) functionality, including OCI Object Storage archival and automated social media publishing.

---

## ☁️ 1. OCI Customer Secret Keys (S3 Compatibility)

These keys are required for the **Storage Lifecycle Manager** to move video files from local storage to the OCI Cloud.

1.  **Log in** to your [Oracle Cloud Console](https://cloud.oracle.com).
2.  In the top-right corner, click on your **Profile Icon** and select your **User Name** (e.g., your email).
3.  On the left sidebar, under **Resources**, scroll down and click on **Customer Secret Keys**.
4.  Click the **Generate Secret Key** button.
5.  **Name the key**: "ViralForge-Storage".
6.  **Copy the Secret Key**: A pop-up will show the secret key. **Copy it immediately** as it will never be shown again.
7.  **Copy the Access Key**: Once generated, you will see an `Access Key` (a long string of characters) in the list. Copy this as well.

### Implementation:
Add these to your `.env` file:
```bash
STORAGE_ACCESS_KEY="your_access_key"
STORAGE_SECRET_KEY="your_secret_key"
```

---

## 🎥 2. YouTube Data API (Google Cloud)

Required for automated publishing and trend discovery.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com).
2.  **Create a Project**: Click the project dropdown and select "New Project". Name it "ViralForge".
3.  **Enable API**: Search for "YouTube Data API v3" and click **Enable**.
4.  **OAuth Consent Screen**:
    *   Navigate to **APIs & Services** -> **OAuth consent screen**.
    *   Select **External** and then **Create**.
    *   Fill in "ViralForge" as the app name and your email.
    *   **Add Scopes**: Add `.../auth/youtube.upload` and `.../auth/youtube.readonly`.
    *   **Add Test Users**: Add your own YouTube account email as a test user.
5.  **Create Credentials**:
    *   Go to **APIs & Services** -> **Credentials**.
    *   Click **Create Credentials** -> **OAuth client ID**.
    *   **Application type**: Web application.
    *   **Authorized redirect URIs**: 
        *   `http://localhost:8000/api/v1/auth/callback/google`
        *   `http://130.61.26.105.sslip.io:8000/api/v1/auth/callback/google` 
        > [!TIP]
        > Google does not allow raw IPs. Using `.sslip.io` at the end of your IP works as a free domain.
6.  **Copy Client ID & Secret**.

### Implementation:
Add these to your `.env` file:
```bash
GOOGLE_CLIENT_ID="your_client_id"
GOOGLE_CLIENT_SECRET="your_client_secret"
```

---

## 📱 3. TikTok for Developers

Required for TikTok archival and publishing.

1.  Go to [TikTok for Developers](https://developers.tiktok.com/).
2.  **Create an App**: Click "Manage Apps" and "Create a New App".
3.  **Scopes**: Request `video.upload` and `user.info.basic`.
4.  **Copy Client Key & Secret**.

---

## 🔄 4. How to get the Refresh Tokens

Once you have the Client IDs and Secrets in your `.env`, you can generate the "Refresh Tokens" (the permanent keys) using the ViralForge Dashboard:

1.  **Restart the services** (`docker-compose up -d`) to load the new `.env` settings.
2.  Open the **ViralForge Dashboard** -> **Settings**.
3.  Click the **Connect YouTube** or **Connect TikTok** button.
4.  Complete the login flow in the browser.
5.  ViralForge will automatically exchange the code for a **Refresh Token** and save it to the database for autonomous use.

---

## 🛡️ 6. Bypassing YouTube "Sign in to confirm you're not a bot"

Cloud IPs (like Oracle Cloud) are often flagged by scrapers. To bypass this, we use authenticated session cookies.

1.  **Install Extension**: Install **"Get cookies.txt LOCALLY"** in your browser.
2.  **Export Cookies**:
    *   Log in to YouTube.
    *   Click the extension and export as **Netscape** format.
3.  **Upload to OCI**:
    *   Create a folder: `mkdir -p cookies` in your project root.
    *   Save the file as `cookies/youtube_cookies.txt`.
4.  **Security**: The `cookies/` folder is blocked in `.gitignore` and excluded from Jenkins `rsync` to ensure your session data never leaves your OCI instance.
