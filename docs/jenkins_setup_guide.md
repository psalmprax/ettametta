# Jenkins Setup Guide — ViralForge

## Step 1: Install Jenkins on OCI Server

SSH into your OCI server, then run:

```bash
# Install Java (Jenkins requirement)
sudo apt update
sudo apt install -y openjdk-17-jdk

# Add Jenkins repo and install
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y jenkins

# Start Jenkins
sudo systemctl enable --now jenkins

# Get the initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Jenkins will be running at: **http://130.61.26.105:8080**

> Make sure port 8080 is open in your OCI security list (same way you opened 8000).

---

## Step 2: Initial Jenkins Setup (Web UI)

1. Open **http://130.61.26.105:8080** in your browser
2. Paste the admin password from Step 1
3. Click **"Install suggested plugins"** — wait for it to finish
4. Create your admin user (username, password, email)
5. Set Jenkins URL to `http://130.61.26.105:8080` → Save & Finish

---

## Step 3: Install Required Plugins

Go to **Manage Jenkins → Plugins → Available plugins**, search and install:

- ✅ **Pipeline** (usually pre-installed)
- ✅ **Git**
- ✅ **GitHub Integration**
- ✅ **Credentials Binding**
- ✅ **Docker Pipeline**

Click **Install** → restart Jenkins when prompted.

---

## Step 4: Add Credentials

Go to: **Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

Add each one below:

### 1. GitHub Credentials
- **Kind**: Username with password
- **Username**: your GitHub username
- **Password**: your GitHub Personal Access Token
  - Get it: GitHub → Settings → Developer settings → Personal access tokens → Generate new token
  - Scopes needed: `repo`, `workflow`
- **ID**: `GITHUB_CREDENTIALS`

### 2. OCI SSH Key (NOT NEEDED)
> Skipped — Pipeline runs locally on the server.

### 3. Docker Hub Credentials (Optional)
- **Kind**: Username with password
- **Username**: your Docker Hub username
- **Password**: Docker Hub password or access token
- **ID**: `DOCKER_HUB_CREDENTIALS`
> **Note**: This is only used to pull base images (like `python:3.10-slim`) to avoid rate limits. We **do not** push your ViralForge images to the registry anymore; they are built locally on the server.

### 4. Groq API Key
- **Kind**: Secret text
- **Secret**: `gsk_...` (your actual key)
- **ID**: `GROQ_API_KEY`

### 5. Telegram Bot Token
- **Kind**: Secret text
- **Secret**: `8414847617:AAHE2AfRTagmP7-aKmqJuVZzFrqTC9m7Dsw`
- **ID**: `TELEGRAM_BOT_TOKEN`

### 6. PostgreSQL Password
- **Kind**: Secret text
- **Secret**: your postgres password (check your `.env` file)
- **ID**: `POSTGRES_PASSWORD`

### 7. Redis Password
- **Kind**: Secret text
- **Secret**: your redis password (must match what you expect, or generate a new one)
- **ID**: `REDIS_PASSWORD`
> **Important**: The application now enforces this password. Ensure this credential is set in Jenkins.

### 8. JWT Secret Key
- **Kind**: Secret text
- **Secret**: generate one now:
  ```bash
  openssl rand -hex 32
  ```
- **ID**: `JWT_SECRET_KEY`

---

## Step 5: Push ViralForge to GitHub

First, create a GitHub repo (github.com → New repository → name: `viral_forge`).

Then on your local machine:

```bash
cd /home/psalmprax/viral_forge
git remote add origin https://github.com/YOUR_USERNAME/viral_forge.git
git push -u origin master
```

---

## Step 6: Create the Pipeline in Jenkins

1. Go to Jenkins dashboard → **New Item**
2. Name it: `viralforge-deploy`
3. Select **Pipeline** → Click OK
4. Scroll to **Pipeline** section:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/YOUR_USERNAME/viral_forge.git`
   - **Credentials**: select `GITHUB_CREDENTIALS`
   - **Branch**: `*/master`
   - **Script Path**: `Jenkinsfile`
5. Click **Save**

---

## Step 7: Update Jenkinsfile Variables

Open `/home/psalmprax/viral_forge/Jenkinsfile` and update the top 4 lines:

```groovy
def OCI_HOST        = "130.61.26.105"           // ✅ already correct
def OCI_USER        = "ubuntu"                   // ✅ already correct
def GITHUB_REPO     = "YOUR_USERNAME/viral_forge" // ← change this
def DOCKER_IMAGE    = "YOUR_DOCKERHUB_USER/viralforge" // ← change this
def DEPLOY_DIR      = "/home/ubuntu/viralforge"  // ✅ already correct
```

Then commit and push:
```bash
git add Jenkinsfile
git commit -m "ci: set correct GitHub and Docker Hub usernames"
git push
```

---

## Step 8: Run the Pipeline

1. Go to Jenkins → `viralforge-deploy`
2. Click **Build Now**
3. Click the build number → **Console Output** to watch it run

The pipeline will:
1. Pull your code from GitHub
2. Lint Python + validate Terraform
3. Build Docker images and push to Docker Hub
4. SSH into your OCI server and deploy
5. Run a health check on `/health`

---

## Automatic Triggers (Optional)

To trigger builds automatically on every `git push`:

1. In Jenkins pipeline settings → **Build Triggers** → check **GitHub hook trigger for GITScm polling**
2. In GitHub repo → Settings → Webhooks → Add webhook:
   - **Payload URL**: `http://130.61.26.105:8080/github-webhook/`
   - **Content type**: `application/json`
   - **Events**: Just the push event
