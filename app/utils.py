"""
Authentication routes for user registration, login, logout, and profile management.
"""

from typing import Dict, Any

def update_user_info(user: Any, data: Dict[str, Any]) -> None:
    """
    Update the user object with the provided data.

    Args:
        user (Any): The user object to update.
        data (Dict[str, Any]): The data to update the user object with. Keys should include
                               'username', 'email', 'phone', and/or 'password'.
    
    """
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "phone" in data:
        user.phone = data["phone"]
    if "password" in data:
        user.set_password(data["password"])
