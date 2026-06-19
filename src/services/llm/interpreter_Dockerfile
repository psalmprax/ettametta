# Minimal and Hardened Sandbox for Ettametta Interpreter
FROM python:3.10-slim

# Prevent Bytecode and set non-buffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Create a restricted working directory
WORKDIR /sandbox
RUN chown sandbox:sandbox /sandbox

# Restrict file system permissions
# Make most of the container read-only later in docker run, 
# but here we set permissions.
RUN chmod 700 /sandbox

# Install minimal dependencies if needed
# RUN pip install --no-cache-dir numpy pandas

# Switch to non-privileged user
USER sandbox

# Entry point will be the raw python interpreter
ENTRYPOINT ["python", "-u"]
