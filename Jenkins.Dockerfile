FROM jenkins/jenkins:lts

USER root

# Install rsync and docker CLI
RUN apt-get update && \
    apt-get install -y rsync docker.io && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add jenkins user to docker group (optional, we run as root in compose for simplicity with socket)
# RUN usermod -aG docker jenkins

USER jenkins
