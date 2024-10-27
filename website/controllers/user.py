from abc import ABC, abstractmethod
from functools import wraps
from flask import abort
from flask_login import current_user, login_required
from enum import Enum
from typing import Optional

class UserRole(Enum):
    USER_ROLE_GUEST = 0
    USER_ROLE_REGISTERED_FREE = 1
    USER_ROLE_REGISTERED_PREMIUM = 2
    USER_ROLE_MODERATOR = 3
    USER_ROLE_ADMIN = 4

class AbstractOperations(ABC):
    @abstractmethod
    def create_list(self, name: str):
        pass
    
    @abstractmethod
    def view_list(self, list_id: int):
        pass
    
    @abstractmethod
    def delete_list(self, list_id: int):
        pass
    

class ConcreteOperations(AbstractOperations):
    # Implementation remains the same as your original code
    pass

class FlaskUserProxy(AbstractOperations):
    def __init__(self):
        self._real_operations = ConcreteOperations()
    
    def _get_user_role(self) -> UserRole:
        if not current_user.is_authenticated:
            return UserRole.GUEST
        return UserRole(getattr(current_user, 'role', UserRole.REGISTERED_FREE.value))
    
    def _check_authorization(self, required_role: UserRole) -> bool:
        user_role = self._get_user_role()
        return user_role.value >= required_role.value
    
    def _check_ownership(self, resource_id: int, resource_type: str) -> bool:
        if not current_user.is_authenticated:
            return False
            
        if resource_type == 'list':
            return self._check_list_ownership(resource_id)
        elif resource_type == 'campsite':
            return self._check_campsite_ownership(resource_id)
        return False
    
    def _check_list_ownership(self, list_id: int) -> bool:
        from website.models.models import CampSiteList
        camp_list = CampSiteList.query.get(list_id)
        return camp_list and camp_list.user_id == current_user.id
    
    @login_required
    def create_list(self, name: str):
        if not self._check_authorization(UserRole.REGISTERED_FREE):
            abort(403, "Insufficient permissions to create lists")
        return self._real_operations.create_list(name)
    
    def view_list(self, list_id: int):
        # Allow public viewing
        return self._real_operations.view_list(list_id)
    
    @login_required
    def delete_list(self, list_id: int):
        # Check if user is owner or admin
        if not (self._check_ownership(list_id, 'list') or 
                self._check_authorization(UserRole.ADMIN)):
            abort(403, "Must be the owner or an admin to delete this list")
        return self._real_operations.delete_list(list_id)
    
    # Add similar implementations for other methods...

# Updated decorator that works with Flask-Login
def requires_role(role: UserRole):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            proxy = FlaskUserProxy()
            if not proxy._check_authorization(role):
                abort(403, f"Required role: {role.name}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Example usage in Flask routes:
"""
from flask import Blueprint, request

bp = Blueprint('lists', __name__)

@bp.route('/lists', methods=['POST'])
@requires_role(UserRole.REGISTERED_FREE)
def create_list():
    proxy = FlaskUserProxy()
    name = request.json.get('name')
    return proxy.create_list(name)

@bp.route('/lists/<int:list_id>', methods=['DELETE'])
@requires_role(UserRole.REGISTERED_FREE)
def delete_list(list_id):
    proxy = FlaskUserProxy()
    return proxy.delete_list(list_id)
"""