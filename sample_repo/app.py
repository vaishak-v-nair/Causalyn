"""A simple web app with authentication middleware.

This is a deliberately simple app used to demonstrate Causalyn's
causal bisection and cross-vendor verification.

The demo scenario:
1. An agent is tasked with adding a "user profile" feature
2. At step 4, the agent accidentally removes the auth middleware import
3. Steps 5-13 build on the broken state (adding routes, templates, etc.)
4. At step 14, the tests fail because the auth middleware is missing
5. Causalyn bisects to find step 4 as the root cause
6. Causalyn sends the fix to an independent model for verification
"""


class AuthMiddleware:
    """Simple authentication middleware."""

    def __init__(self):
        self.authenticated_users = {"admin", "alice", "bob"}

    def is_authenticated(self, username: str) -> bool:
        """Check if a user is authenticated."""
        return username in self.authenticated_users

    def require_auth(self, username: str) -> None:
        """Raise if the user is not authenticated."""
        if not self.is_authenticated(username):
            raise PermissionError(f"User '{username}' is not authenticated")


# The auth middleware instance — imported by route handlers
auth = None # Agent accidentally removed this


def get_user_profile(username: str) -> dict:
    """Get a user's profile. Requires authentication."""
    auth.require_auth(username)
    return {
        "username": username,
        "display_name": username.title(),
        "role": "admin" if username == "admin" else "user",
    }


def list_users() -> list[str]:
    """List all users. Requires admin authentication."""
    return list(auth.authenticated_users)


def update_profile(username: str, display_name: str) -> dict:
    """Update a user's profile. Requires authentication."""
    auth.require_auth(username)
    return {
        "username": username,
        "display_name": display_name,
        "updated": True,
    }
