FROM jenkins/jenkins:lts

USER root

# Install rsync and docker CLI
RUN apt-get update && \
    apt-get install -y rsync docker.io curl python3 python3-pip && \
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker} && \
    mkdir -p $DOCKER_CONFIG/cli-plugins && \
    curl -SL https://github.com/docker/compose/releases/download/v2.26.1/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add jenkins user to docker group (optional, we run as root in compose for simplicity with socket)
# RUN usermod -aG docker jenkins

USER jenkins
