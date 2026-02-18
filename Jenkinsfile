/*
 * ViralForge Jenkins CI/CD Pipeline
 * ===================================
 * SETUP: Before running this pipeline, configure the following
 * credentials in Jenkins → Manage Jenkins → Credentials → Global:
 *
 *  ID                        Type                  Description
 *  ─────────────────────────────────────────────────────────────────────
 *  GITHUB_CREDENTIALS        Username/Password     GitHub username + Personal Access Token
 *                            (or SSH Key)          (Settings → Developer settings → PAT)
 *
 *  OCI_SSH_KEY               SSH Private Key       The .pem key used to SSH into your OCI instance
 *                                                  (the same key in ~/.oci/*.pem)
 *
 *  DOCKER_HUB_CREDENTIALS    Username/Password     Docker Hub username + password/access token
 *                                                  (hub.docker.com → Account Settings → Security)
 *
 *  GROQ_API_KEY              Secret text           Your Groq API key from console.groq.com
 *
 *  TELEGRAM_BOT_TOKEN        Secret text           Your Telegram bot token from @BotFather
 *
 *  POSTGRES_PASSWORD         Secret text           PostgreSQL password for production DB
 *
 *  REDIS_PASSWORD            Secret text           Redis password (if auth enabled)
 *
 *  JWT_SECRET_KEY            Secret text           Random secret for JWT signing
 *                                                  Generate with: openssl rand -hex 32
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

    environment {
        PROJECT_NAME          = "viral_forge"
        DOCKER_COMPOSE_FILE   = "docker-compose.yml"
        
        // Deployment directory on the SAME server
        DEPLOY_DIR            = "/home/ubuntu/viralforge"
        HEALTH_CHECK_URL      = "http://localhost:8000/health"

        // Injected from Jenkins credentials store
        GROQ_API_KEY          = credentials('GROQ_API_KEY')
        TELEGRAM_BOT_TOKEN    = credentials('TELEGRAM_BOT_TOKEN')
        POSTGRES_PASSWORD     = credentials('POSTGRES_PASSWORD')
        REDIS_PASSWORD        = credentials('REDIS_PASSWORD')
        JWT_SECRET_KEY        = credentials('JWT_SECRET_KEY')
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout') {
            steps {
                git(
                    branch: 'master',
                    url: "https://github.com/psalmprax/viral_forge.git",
                    credentialsId: 'GITHUB_CREDENTIALS'
                )
                echo "Checked out branch: ${env.GIT_BRANCH} @ ${env.GIT_COMMIT?.take(7)}"
            }
        }

        stage('Lint & Validate') {
            parallel {
                stage('Python lint') {
                    steps {
                        sh '''
                            python3 -m pip install ruff --quiet
                            ruff check . --select E,W,F --ignore E501 || true
                        '''
                    }
                }
                stage('Terraform validate') {
                    steps {
                        dir('terraform') {
                            sh '''
                                terraform init -backend=false -input=false
                                terraform validate
                            '''
                        }
                    }
                }
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
                            --exclude 'terraform' \\
                            . ${DEPLOY_DIR}
                    """

                    // 3. Write .env file Locally
                    sh """
                        cat > ${DEPLOY_DIR}/.env <<EOF
GROQ_API_KEY=${GROQ_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
EOF
                    """

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
