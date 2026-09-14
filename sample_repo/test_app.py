"""Tests for the sample app.

These tests verify that authentication works correctly and that
unauthenticated users are blocked.
"""

import pytest
from app import get_user_profile, list_users, update_profile, auth


def test_authenticated_user_can_get_profile():
    """An authenticated user should be able to view their profile."""
    profile = get_user_profile("alice")
    assert profile["username"] == "alice"
    assert profile["display_name"] == "Alice"
    assert profile["role"] == "user"


def test_admin_has_admin_role():
    """The admin user should have the admin role."""
    profile = get_user_profile("admin")
    assert profile["role"] == "admin"


def test_unauthenticated_user_is_blocked():
    """An unauthenticated user should get a PermissionError."""
    with pytest.raises(PermissionError, match="not authenticated"):
        get_user_profile("mallory")


def test_list_users_returns_all():
    """list_users should return all authenticated users."""
    users = list_users()
    assert "admin" in users
    assert "alice" in users
    assert "bob" in users


def test_update_profile_requires_auth():
    """update_profile should require authentication."""
    result = update_profile("alice", "Alice Wonderland")
    assert result["updated"] is True

    with pytest.raises(PermissionError):
        update_profile("mallory", "Evil User")


def test_auth_middleware_exists():
    """The auth middleware should be importable and functional."""
    assert auth is not None
    assert auth.is_authenticated("alice")
    assert not auth.is_authenticated("nobody")
