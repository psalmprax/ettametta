#!/usr/bin/env python3
import paramiko
import sys
import os

# Server details
HOST = '38.54.12.83'
PORT = 22
USERNAME = 'root'
# Use SSH key from ~/Music/
SSH_KEY_PATH = os.path.expanduser('~/Music/id_rsa')

# Create SSH client
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {HOST}...")
    # Load SSH key
    private_key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
    client.connect(HOST, port=PORT, username=USERNAME, pkey=private_key)
    print("Connected!")
    
    # Check if credentials.xml exists
    stdin, stdout, stderr = client.exec_command('ls -la /home/ubuntu/jenkins_home/credentials.xml')
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("credentials.xml exists!")
    else:
        print("credentials.xml not found")
    
    # Read the credentials.xml content
    stdin, stdout, stderr = client.exec_command('cat /home/ubuntu/jenkins_home/credentials.xml')
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        content = stdout.read().decode('utf-8')
        print("\n--- credentials.xml content ---")
        print(content[:5000])  # Print first 5000 chars
    else:
        print("Failed to read credentials.xml")
        print(stderr.read().decode('utf-8'))
    
    # Check if credentials.xml is valid XML
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(content)
        print("\n--- XML is valid ---")
        print(f"Root tag: {root.tag}")
        
        # Count credentials
        credentials = root.findall('.//{http://jenkinsci.org/}credentials')
        print(f"Number of credentials: {len(credentials)}")
    except ET.ParseError as e:
        print(f"\n--- XML Parse Error ---")
        print(str(e))
    
    client.close()
    print("\nDisconnected.")
    
except paramiko.AuthenticationException as e:
    print(f"Authentication failed! Error: {str(e)}")
    sys.exit(1)
except paramiko.SSHException as e:
    print(f"SSH Error: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
