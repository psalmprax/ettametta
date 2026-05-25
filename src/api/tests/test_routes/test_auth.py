"""
Authentication Endpoint Tests
============================
Integration tests for authentication routes
"""

from fastapi.testclient import TestClient
from fastapi import status


class TestRegistration:
    """Test user registration endpoints."""
    
    def test_register_new_user(self, client: TestClient):
        """Test registering a new user."""
        response = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Password123!"
        })
        
        assert response.status_code == status.HTTP_200_OK
        res_json = response.json()
        assert "data" in res_json
        data = res_json["data"]
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "role" in data
    
    def test_register_first_user_is_admin(self, client: TestClient):
        """Test that the first registered user becomes admin."""
        response = client.post("/api/v1/auth/register", json={
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "Password123!"
        })
        
        assert response.status_code == status.HTTP_200_OK
        res_json = response.json()
        assert "data" in res_json
        data = res_json["data"]
        assert data["role"] == "admin"
    
    def test_register_duplicate_email(self, client: TestClient):
        """Test registering with an existing email fails."""
        # First registration
        client.post("/api/v1/auth/register", json={
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "Password123!"
        })
        
        # Second registration with same email
        response = client.post("/api/v1/auth/register", json={
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "Password123!"
        })
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Email already registered" in response.json()["error"]["message"]
    
    def test_register_duplicate_username(self, client: TestClient):
        """Test registering with an existing username fails."""
        # First registration
        client.post("/api/v1/auth/register", json={
            "username": "samename",
            "email": "user1@example.com",
            "password": "Password123!"
        })
        
        # Second registration with same username
        response = client.post("/api/v1/auth/register", json={
            "username": "samename",
            "email": "user2@example.com",
            "password": "Password123!"
        })
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Username already taken" in response.json()["error"]["message"]
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registering with an invalid email format."""
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "not-an-email",
            "password": "Password123!"
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_fields(self, client: TestClient):
        """Test registering with missing required fields."""
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser"
            # missing email and password
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test login endpoints."""
    
    def test_login_valid_credentials(self, client: TestClient):
        """Test login with valid credentials."""
        # Register user first
        client.post("/api/v1/auth/register", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "Password123!"
        })
        
        # Login
        response = client.post("/api/v1/auth/login", data={
            "username": "logintest",
            "password": "Password123!"
        })
        
        assert response.status_code == status.HTTP_200_OK
        res_json = response.json()
        assert "data" in res_json
        data = res_json["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_username(self, client: TestClient):
        """Test login with non-existent username."""
        response = client.post("/api/v1/auth/login", data={
            "username": "nonexistent",
            "password": "Password123!"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_invalid_password(self, client: TestClient):
        """Test login with wrong password."""
        # Register user
        client.post("/api/v1/auth/register", json={
            "username": "wrongpass",
            "email": "wrongpass@example.com",
            "password": "Password123!"
        })
        
        # Login with wrong password
        response = client.post("/api/v1/auth/login", data={
            "username": "wrongpass",
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_missing_credentials(self, client: TestClient):
        """Test login with missing credentials."""
        response = client.post("/api/v1/auth/login", data={})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTokenRefresh:
    """Test token refresh endpoints."""
    
    def test_get_current_user_valid_token(self, client: TestClient):
        """Test getting current user with valid token."""
        # Register and login
        client.post("/api/v1/auth/register", json={
            "username": "currentuser",
            "email": "current@example.com",
            "password": "Password123!"
        })
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": "currentuser",
            "password": "Password123!"
        })
        
        token = login_response.json()["data"]["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        res_json = response.json()
        assert "data" in res_json
        data = res_json["data"]
        assert data["username"] == "currentuser"
    
    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
