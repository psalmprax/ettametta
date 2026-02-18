---
description: troubleshoot authentication issues and 401 errors
---

# Authentication Troubleshooting Workflow

This workflow guides you through identifying and resolving authentication issues (e.g., 401 Unauthorized errors).

1.  **Stop all containers (optional but recommended for a clean state):**
    ```bash
    docker-compose down
    ```

2.  **Verify Environment Variables:**
    Check your `.env` file to ensure the `SECRET_KEY` and `ALGORITHM` are set and match what's expected by the backend.
    ```bash
    grep "SECRET_KEY" .env
    grep "ALGORITHM" .env
    ```

3.  **Start Services:**
    ```bash
    // turbo
    docker-compose up -d --build
    ```

4.  **Wait for Database:**
    Ensure the `db` service is healthy before proceeding.
    ```bash
    // turbo
    docker-compose exec db pg_isready -U psalmprax
    ```

5.  **Verify Admin User Existence:**
    Check if the `psalmprax` user exists in the database.
    ```bash
    docker-compose exec db psql -U psalmprax -d viral_forge -c "SELECT username, role, is_active FROM users WHERE username = 'psalmprax';"
    ```
    *If the user does not exist, you may need to re-run the `init_db` script or manually create the user.*

6.  **Test Login Endpoint (Get Token):**
    Attempt to get a token using `curl`. Replace `viral_forge_pass` with your actual password if different.
    ```bash
    curl -X POST "http://localhost:8000/auth/token" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         -d "username=psalmprax&password=viral_forge_pass"
    ```
    *Successful response should include an `access_token`.*

7.  **Test Protected Endpoint (Verify Token):**
    Use the token from the previous step to access a protected endpoint. Replace `YOUR_ACCESS_TOKEN` with the actual token.
    ```bash
    curl -X GET "http://localhost:8000/auth/me" \
         -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
    ```
    *Successful response should return user details.*

8.  **Check Frontend Logs:**
    If API tests pass but the dashboard still fails, check the browser console logs for specific error messages (e.g., CORS issues, network errors).

9.  **Check Backend Logs:**
    View the logs for the `api` service to see why requests are being rejected.
    ```bash
    // turbo
    docker-compose logs -f api
    ```
