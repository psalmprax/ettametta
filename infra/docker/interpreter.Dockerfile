# Minimal Python Sandbox Container
# ============================================
# Restricted environment for user code execution
# - No network access
# - No file system access outside /tmp
# - Limited memory
# - Read-only except /tmp

FROM python:3.12-slim-bookworm

# Create non-root user
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Only allow specific binaries
RUN mkdir -p /home/sandbox/app

# Switch to non-root
USER sandbox:sandbox
WORKDIR /home/sandbox/app

# Copy a simple runner script
COPY sandbox_entry.py /home/sandbox/app/run.py

# Execution entry
CMD ["python3", "/home/sandbox/app/run.py"]