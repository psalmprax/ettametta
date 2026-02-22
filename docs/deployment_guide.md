# ettametta: E2E Configuration Guide

This guide provides step-by-step instructions for obtaining the necessary credentials to enable full end-to-end (E2E) functionality, including OCI Object Storage archival and automated social media publishing.

---

## ☁️ 1. OCI Customer Secret Keys (S3 Compatibility)

These keys are required for the **Storage Lifecycle Manager** to move video files from local storage to the OCI Cloud.

1.  **Log in** to your [Oracle Cloud Console](https://cloud.oracle.com).
2.  In the top-right corner, click on your **Profile Icon** and select your **User Name** (e.g., your email).
3.  On the left sidebar, under **Resources**, scroll down and click on **Customer Secret Keys**.
4.  Click the **Generate Secret Key** button.
5.  **Name the key**: "ettametta-Storage".
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
2.  **Create a Project**: Click the project dropdown and select "New Project". Name it "ettametta".
3.  **Enable API**: Search for "YouTube Data API v3" and click **Enable**.
4.  **OAuth Consent Screen**:
    *   Navigate to **APIs & Services** -> **OAuth consent screen**.
    *   Select **External** and then **Create**.
    *   Fill in "ettametta" as the app name and your email.
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

## 🦅 5. Telegram Multi-Bot Setup
ettametta supports white-labeling. Users can connect their own private agents.
1.  Message **@BotFather** on Telegram.
2.  Use `/newbot` to create your agent.
3.  **Copy the API Token**.
4.  In the **ettametta Dashboard** -> **Settings** -> **Notifications**, paste your **Bot Token** and **Chat ID**.
5.  Your private agent will initialize automatically.

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
5.  **Signature Solving**: The system automatically includes a JavaScript runtime (`nodejs`) in the Docker build to solve YouTube "n-challenge" signature protection. No manual setup is required beyond exporting cookies.

---

## 🔧 Code Fixes Summary (Feb 2026)

The following issues were identified and fixed during the dummy data audit:

### 1. Go Discovery Scanner - Real YouTube API Integration
**File**: `services/discovery-go/scanner.go`

**Problem**: The scanner was generating fake/mock video URLs like `https://discovery.os/v/123456789` instead of real content.

**Fix**: 
- Integrated YouTube Data API v3 for real video search
- Added proper API key authentication via `YOUTUBE_API_KEY` environment variable
- Returns real metadata: view count, thumbnail URL, title, platform info
- Falls back gracefully when API key is not available

### 2. Persona Image Storage - Real S3 Upload
**File**: `api/routes/persona.py`

**Problem**: Persona creation was storing images to fake Google Storage URLs like `https://storage.googleapis.com/viral-forge-assets/...`

**Fix**:
- Integrated real S3-compatible storage service (`api.utils.storage`)
- Files are now uploaded to configured OCI Object Storage
- Returns actual S3 URLs or local path indicators on failure

### 3. Jenkins Credentials Configuration
**Files**: `jenkins_casc_credentials.yaml`, `scripts/import_jenkins_credentials.sh`

- Created JCasC-compatible credentials YAML
- Script to import credentials via Jenkins Groovy console
- 26 credentials pre-configured in Jenkins

### Required Environment Variables for Real Data

Make sure these are set in your `.env` or Jenkins credentials:

| Variable | Purpose |
|----------|----------|
| `YOUTUBE_API_KEY` | YouTube Data API v3 key for discovery scanner |
| `AWS_ACCESS_KEY_ID` | OCI S3 access key for persona image storage |
| `AWS_SECRET_ACCESS_KEY` | OCI S3 secret key |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name |

---

## 🏗️ 7. Dockerized Jenkins CI/CD

Jenkins is now fully dockerized for portability and ease of maintenance.

### 1. Startup
Run the dedicated Jenkins stack from the project root:
```bash
docker-compose -f jenkins-docker-compose.yml up -d
```
Access Jenkins at `http://<OCI_IP>:8080`.

### 2. Configuration as Code (JCasC)
Credentials and system settings are managed via `jenkins_casc_credentials.yaml`. To import your latest environment variables into Jenkins:
```bash
bash scripts/import_jenkins_credentials.sh
```
This script uses the Jenkins Groovy console to securely and idempotently load your `.env` secrets into the Jenkins credential store.

### 3. Build Node Mapping
The Jenkins container is configured with **Docker-out-of-Docker (DooD)**, meaning it shares the host's `/var/run/docker.sock`. This allows Jenkins to build, stop, and start containers on the OCI host directly.

---

Run `docker-compose up -d` for the main application from `/home/ubuntu/viralforge/`.
