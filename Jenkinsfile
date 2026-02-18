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

def OCI_HOST        = "130.61.26.105"           // Your OCI instance public IP
def OCI_USER        = "ubuntu"                   // SSH user on OCI
def GITHUB_REPO     = "YOUR_USERNAME/viral_forge" // e.g. psalmprax/viral_forge
def DOCKER_IMAGE    = "YOUR_DOCKERHUB_USER/viralforge" // e.g. psalmprax/viralforge
def DEPLOY_DIR      = "/home/ubuntu/viralforge"  // Deployment path on OCI server

pipeline {
    agent any

    environment {
        PROJECT_NAME          = "viral_forge"
        DOCKER_COMPOSE_FILE   = "docker-compose.yml"
        HEALTH_CHECK_URL      = "http://localhost:8000/health"

        // Injected from Jenkins credentials store (never hardcode these)
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
                    url: "https://github.com/${GITHUB_REPO}.git",
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

        stage('Build Docker Images') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'DOCKER_HUB_CREDENTIALS',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker-compose build --no-cache
                        docker tag ${PROJECT_NAME}_api ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker tag ${PROJECT_NAME}_api ${DOCKER_IMAGE}:latest
                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }

        stage('Deploy to OCI') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'OCI_SSH_KEY',
                    keyFileVariable: 'SSH_KEY_FILE'
                )]) {
                    sh """
                        # Copy latest docker-compose to server
                        scp -i \$SSH_KEY_FILE -o StrictHostKeyChecking=no \\
                            ${DOCKER_COMPOSE_FILE} ${OCI_USER}@${OCI_HOST}:${DEPLOY_DIR}/

                        # Write .env on server (from Jenkins secrets — never stored in git)
                        ssh -i \$SSH_KEY_FILE -o StrictHostKeyChecking=no ${OCI_USER}@${OCI_HOST} \\
                        "cat > ${DEPLOY_DIR}/.env << 'ENVEOF'
GROQ_API_KEY=${GROQ_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENVEOF"

                        # Pull latest images and restart services
                        ssh -i \$SSH_KEY_FILE -o StrictHostKeyChecking=no ${OCI_USER}@${OCI_HOST} \\
                        "cd ${DEPLOY_DIR} && \\
                         docker-compose pull && \\
                         docker-compose up -d --remove-orphans && \\
                         docker system prune -f"
                    """
                }
            }
        }

        stage('Health Check') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'OCI_SSH_KEY',
                    keyFileVariable: 'SSH_KEY_FILE'
                )]) {
                    sh """
                        sleep 15
                        ssh -i \$SSH_KEY_FILE -o StrictHostKeyChecking=no ${OCI_USER}@${OCI_HOST} \\
                        "curl -sf ${HEALTH_CHECK_URL} && echo 'API healthy' || exit 1"
                    """
                }
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
