#!/bin/bash
# ============================================================================
# Jenkins Credentials Import Script
# ============================================================================
# Usage: JENKINS_PASSWORD='your-password' ./scripts/import_jenkins_credentials.sh
#
# This script:
# 1. Copies the JCasC YAML file to the OCI server
# 2. Imports credentials into Jenkins using the provided password
# ============================================================================

set -e

# Configuration
SSH_KEY="${SSH_KEY:-$HOME/.oci/samuelolle@yahoo.com-2026-02-17T13_44_42.909Z.pem}"
OCI_HOST="${OCI_HOST:-130.61.26.105}"
JENKINS_USER="admin"
JENKINS_PASSWORD="${JENKINS_PASSWORD:-}"  # Must be set via environment variable

# Local files
YAML_FILE="jenkins_casc_credentials.yaml"

echo "=========================================="
echo "Jenkins Credentials Import Script"
echo "=========================================="

# Check if YAML file exists
if [ ! -f "$YAML_FILE" ]; then
    echo "ERROR: $YAML_FILE not found!"
    exit 1
fi

# Check for password
if [ -z "$JENKINS_PASSWORD" ]; then
    echo "ERROR: JENKINS_PASSWORD environment variable not set"
    echo "Usage: JENKINS_PASSWORD='your-password' ./scripts/import_jenkins_credentials.sh"
    exit 1
fi

# Copy YAML file to OCI server
echo "[1/3] Copying $YAML_FILE to OCI server..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$YAML_FILE" ubuntu@${OCI_HOST}:~/jenkins_casc_credentials.yaml
echo "✅ File copied"

# Import credentials via Docker exec
echo "[2/3] Importing credentials into Jenkins container..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${OCI_HOST} << EOFSCRIPT
set -e

JENKINS_PASSWORD='$JENKINS_PASSWORD'

# Find Jenkins container
JENKINS_CONTAINER=\$(docker ps --format '{{.Names}}' | grep -i jenkins | head -1)
echo "Found Jenkins container: \$JENKINS_CONTAINER"

# Install python dependencies in container if needed
docker exec \$JENKINS_CONTAINER pip3 install -q pyyaml requests 2>/dev/null || true

# Run Python import script inside container
docker exec -i \$JENKINS_CONTAINER python3 << 'PYTHON'
import os
import yaml
import requests
from requests.auth import HTTPBasicAuth

# Load YAML
with open('/home/ubuntu/jenkins_casc_credentials.yaml', 'r') as f:
    data = yaml.safe_load(f)

credentials = data.get('credentials', {}).get('system', {}).get('domainCredentials', [{}])[0].get('credentials', [])

# Jenkins API config
JENKINS_URL = 'http://localhost:8080'
JENKINS_USER = 'admin'
JENKINS_PASSWORD = os.environ.get('JENKINS_PASSWORD', '')

if not JENKINS_PASSWORD:
    print("ERROR: JENKINS_PASSWORD not set")
    exit(1)

# First, get a CSRF crumb
try:
    response = requests.get(f"{JENKINS_URL}/crumbIssuer/api/json", auth=HTTPBasicAuth(JENKINS_USER, JENKINS_PASSWORD))
    if response.status_code == 200:
        crumb = response.json().get('crumbRequestField', 'Jenkins-Crumb')
        crumb_value = response.json().get('crumb')
        print(f"Got CSRF crumb")
    else:
        crumb = None
        crumb_value = None
        print(f"No CSRF crumb (status {response.status_code}), continuing...")
except Exception as e:
    print(f"Warning: Could not get crumb: {e}")
    crumb = None
    crumb_value = None

def create_string_credentials(cred_id, secret, description):
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
  <id>{cred_id}</id>
  <secret>{secret}</secret>
  <description>{description}</description>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>'''
    return xml

def create_username_password_credentials(cred_id, username, password, description):
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
  <id>{cred_id}</id>
  <username>{username}</username>
  <password>{password}</password>
  <description>{description}</description>
</com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>'''
    return xml

auth = HTTPBasicAuth(JENKINS_USER, JENKINS_PASSWORD)
imported = 0
failed = 0
skipped = 0

for cred in credentials:
    cred_id = cred.get('id')
    print(f"Importing {cred_id}...", end=" ")
    
    # Skip placeholder credentials
    if 'string' in cred:
        secret = cred['string'].get('secret', '')
        if secret == '******' or not secret:
            print("⏭️  Skipped (placeholder)")
            skipped += 1
            continue
        description = cred['string'].get('description', '')
        xml = create_string_credentials(cred_id, secret, description)
    elif 'usernamePassword' in cred:
        password = cred['usernamePassword'].get('password', '')
        if password == '******' or not password:
            print("⏭️  Skipped (placeholder)")
            skipped += 1
            continue
        username = cred['usernamePassword'].get('username', '')
        description = cred['usernamePassword'].get('description', '')
        xml = create_username_password_credentials(cred_id, username, password, description)
    else:
        print("⚠️  Unknown type, skipping")
        skipped += 1
        continue
    
    try:
        url = f"{JENKINS_URL}/credentials/createDomainCredentials/domain/_/"
        headers = {'Content-Type': 'application/xml'}
        
        # Add crumb header if available
        if crumb and crumb_value:
            headers[crumb] = crumb_value
        
        response = requests.post(url, auth=auth, data=xml, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            print("✅ OK")
            imported += 1
        else:
            print(f"❌ HTTP {response.status_code}")
            failed += 1
            
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        failed += 1

print(f"\n==========================================")
print(f"Import complete: {imported} ✅, {failed} ❌, {skipped} ⏭️")
print(f"==========================================")
PYTHON

EOFSCRIPT

echo "[3/3] Done!"
echo ""
echo "=========================================="
echo "✅ Jenkins credentials import complete!"
echo "=========================================="
