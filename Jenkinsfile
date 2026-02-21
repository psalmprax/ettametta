/*
 * ViralForge Jenkins CI/CD Pipeline
 * ===================================
 * SETUP: Before running this pipeline, configure the following
 * credentials in Jenkins → Manage Jenkins → Credentials → Global:
 *
 *  ID                        Type                  Description
 *  ─────────────────────────────────────────────────────────────────────
 *  GITHUB_CREDENTIALS        Username/Password     GitHub username + Personal Access Token
 *  OCI_SSH_KEY               SSH Private Key       The .pem key used to SSH into your OCI instance
 *  DOCKER_HUB_CREDENTIALS    Username/Password     Docker Hub username + password/access token
 *  GROQ_API_KEY              Secret text           Your Groq API key
 *  OPENAI_API_KEY            Secret text           Optional: OpenAI API key
 *  ELEVENLABS_API_KEY        Secret text           Optional: ElevenLabs API key
 *  PEXELS_API_KEY            Secret text           Your Pexels API key for stock footage
 *  TELEGRAM_BOT_TOKEN        Secret text           Your Telegram bot token
 *  TELEGRAM_ADMIN_ID         Secret text           Your Telegram User ID (numeric)
 *  POSTGRES_PASSWORD         Secret text           PostgreSQL password
 *  REDIS_PASSWORD            Secret text           Redis password
 *  JWT_SECRET_KEY            Secret text           Random secret for JWT signing
 *
 * HOW TO ADD A CREDENTIAL IN JENKINS:
 *  1. Go to: Jenkins → Manage Jenkins → Credentials → System → Global credentials
 *  2. Click "Add Credentials"
 *  3. Choose the Type (Secret text / Username+Password / SSH Private Key)
 *  4. Set the ID exactly as shown in the table above
 *  5. Save
 *
 * PIPELINE VARIABLES (edit these to match your setup):
 */

pipeline {
    agent any
    
    parameters {
        string(name: 'PRODUCTION_DOMAIN', defaultValue: 'http://130.61.26.105', description: 'Public URL of your ViralForge instance')
        choice(name: 'VOICE_ENGINE', choices: ['fish_speech', 'elevenlabs'], description: 'Primary voice synthesis engine')
        choice(name: 'MONETIZATION_MODE', choices: ['selective', 'all'], description: 'Monetization strategy')
    }

    environment {
        PROJECT_NAME          = "viral_forge"
        DOCKER_COMPOSE_FILE   = "docker-compose.yml"
        
        // Deployment directory on the SAME server
        DEPLOY_DIR            = "/home/ubuntu/viralforge"
        PUBLIC_IP             = "130.61.26.105"
        HEALTH_CHECK_URL      = "http://172.17.0.1:3000/api/health"
        
        // Ensure tools in /usr/bin are found
        PATH                  = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${env.PATH}"

        // Injected from Jenkins credentials store
        // Injected mapping
        GROQ_API_KEY          = credentials('GROQ_API_KEY')
        OPENAI_API_KEY        = credentials('OPENAI_API_KEY')
        ELEVENLABS_API_KEY    = credentials('ELEVENLABS_API_KEY')
        PEXELS_API_KEY        = credentials('PEXELS_API_KEY')
        TELEGRAM_BOT_TOKEN    = credentials('TELEGRAM_BOT_TOKEN')
        POSTGRES_PASSWORD     = credentials('POSTGRES_PASSWORD')
        REDIS_PASSWORD        = credentials('REDIS_PASSWORD')
        JWT_SECRET_KEY        = credentials('JWT_SECRET_KEY')
        TELEGRAM_ADMIN_ID     = credentials('TELEGRAM_ADMIN_ID')
        
        // OAuth & Social
        GOOGLE_CLIENT_ID       = credentials('GOOGLE_CLIENT_ID')
        GOOGLE_CLIENT_SECRET   = credentials('GOOGLE_CLIENT_SECRET')
        TIKTOK_CLIENT_KEY      = credentials('TIKTOK_CLIENT_KEY')
        TIKTOK_CLIENT_SECRET   = credentials('TIKTOK_CLIENT_SECRET')
        YOUTUBE_API_KEY        = credentials('YOUTUBE_API_KEY')
        TIKTOK_API_KEY         = credentials('TIKTOK_API_KEY')
        
        // OCI Storage
        OCI_STORAGE_ACCESS_KEY = credentials('STORAGE_ACCESS_KEY')
        OCI_STORAGE_SECRET_KEY = credentials('STORAGE_SECRET_KEY')
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout') {
            steps {
                // Fetching source code
                git(
                    branch: 'master',
                    url: "https://github.com/psalmprax/viral_forge.git",
                    credentialsId: 'GITHUB_CREDENTIALS'
                )
                echo "Checked out branch: ${env.GIT_BRANCH} @ ${env.GIT_COMMIT?.take(7)}"
            }
        }



        stage('Deploy & Build Locally') {
            steps {
                script {
                    // 1. Prepare Deployment Directory (Local)
                    sh "mkdir -p ${DEPLOY_DIR}"
                    
                    // 2. Sync Files Locally (Workspace -> Deploy Dir)
                    // Using rsync locally to exclude git/venv/etc
                    sh """
                        rsync -avz --delete \\
                            --exclude '.git' \\
                            --exclude 'venv' \\
                            --exclude '__pycache__' \\
                            --exclude '.env' \\
                            --exclude 'cookies' \\
                            --exclude 'terraform' \\
                            . ${DEPLOY_DIR}
                    """

                    // 3. Write .env file Locally
                    script {
                        def envContent = """
GROQ_API_KEY=${GROQ_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}
ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
PEXELS_API_KEY=${PEXELS_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_ADMIN_ID=${TELEGRAM_ADMIN_ID}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
# Networking
PRODUCTION_DOMAIN=${params.PRODUCTION_DOMAIN}
# AI Control
VOICE_ENGINE=${params.VOICE_ENGINE}
MONETIZATION_MODE=${params.MONETIZATION_MODE}
# OAuth
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
TIKTOK_CLIENT_KEY=${TIKTOK_CLIENT_KEY}
TIKTOK_CLIENT_SECRET=${TIKTOK_CLIENT_SECRET}
YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
TIKTOK_API_KEY=${TIKTOK_API_KEY}
# Storage
STORAGE_PROVIDER=OCI
STORAGE_ENDPOINT=https://frraceg1idjv.compat.objectstorage.eu-frankfurt-1.oraclecloud.com
STORAGE_BUCKET=viral-forge-assets
STORAGE_ACCESS_KEY=${OCI_STORAGE_ACCESS_KEY}
STORAGE_SECRET_KEY=${OCI_STORAGE_SECRET_KEY}
STORAGE_REGION=eu-frankfurt-1
"""
                        sh "umask 077 && echo '${envContent}' > ${DEPLOY_DIR}/.env"
                    }

                    // 4. Build and Launch
                    script {
                        try {
                            withCredentials([usernamePassword(
                                credentialsId: 'DOCKER_HUB_CREDENTIALS',
                                usernameVariable: 'DOCKER_USER',
                                passwordVariable: 'DOCKER_PASS'
                            )]) {
                                sh "echo '$DOCKER_PASS' | docker login -u '$DOCKER_USER' --password-stdin"
                            }
                        } catch (Exception e) {
                            echo "⚠️ Docker Hub credentials not found or login failed. Skipping login (this is fine if base images are public)."
                        }

                        sh """
                            cd ${DEPLOY_DIR}
                            
                            # Build & Up
                            docker-compose build --no-cache
                            docker-compose up -d --remove-orphans
                            docker system prune -f
                        """
                    }
                }
            }
        }

        stage('Health Check') {
            steps {
                sh "sleep 15 && curl -sf ${HEALTH_CHECK_URL} && echo 'API healthy' || exit 1"
            }
        }
    }

    post {
        success {
            echo "✅ ViralForge deployed successfully — build #${BUILD_NUMBER}"
        }
        failure {
            echo "❌ Deployment failed at stage: ${env.STAGE_NAME}. Check logs above."
        }
        always {
            sh 'docker logout || true'
            cleanWs()
        }
    }
}
