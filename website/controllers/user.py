from abc import ABC, abstractmethod
from functools import wraps
from flask import session, abort, current_app
from enum import Enum
from typing import Optional

# Define user roles
class UserRole(Enum):
    USER_ROLE_GUEST = 0
    USER_ROLE_REGISTERED_FREE = 1
    USER_ROLE_REGISTERED_PREMIUM = 2 # currently unused
    USER_ROLE_MODERATOR = 3
    USER_ROLE_ADMIN = 4

# Abstract interface for operations
class AbstractOperations(ABC):
    
    # CampSiteList abstract methods
    @abstractmethod
    def create_list(self, name: str):
        pass
    
    @abstractmethod
    def view_list(self, list_id: int):
        pass
    
    @abstractmethod
    def delete_list(self, list_id: int):
        pass
    
    # CampSite abstract methods
    @abstractmethod
    def create_campsite(self, name: str):
        pass
    
    @abstractmethod
    def view_campsite(self, campsite_id: int):
        pass
    
    @abstractmethod
    def modify_campsite(self, campsite_id: int):
        pass
    
    @abstractmethod
    def delete_campsite(self, campsite_id: int):
        pass
    
    # User abstract methods
    @abstractmethod
    def delete_profile(self, user_id: int):
        pass
    
    @abstractmethod
    def modify_profile(self, user_id: int):
        pass
    
    @abstractmethod
    def view_profile(self, user_id: int):
        pass
    
    @abstractmethod
    def create_profile(self, user_id: int):
        pass
    
    

# Real operations implementation
class ConcreteOperations(AbstractOperations):
    
    # CampSiteList real operations
    def create_list(self, name: str):
        return f"Created list: {name}"
    
    def view_list(self, list_id: int):
        return f"Viewing list: {list_id}"
    
    def delete_list(self, list_id: int):
        return f"Deleted list: {list_id}"
    
    # CampSite real operations
    def create_campsite(self, name):
        return f"Create campsite: {name}"
    
    def view_campsite(self, campsite_id):
        return f"View campsite: {campsite_id}"
    
    def modify_campsite(self, campsite_id):
        return f"Modify campsite: {campsite_id}"
    
    def delete_campsite(self, campsite_id):
        return f"Delete campsite: {campsite_id}"
    
    # User real operations
    def modify_profile(self, user_id):
        return f"Modify user: {user_id}"
    
    def view_profile(self, user_id):
        return f"View user: {user_id}"
    
    def create_profile(self, user_id):
        return f"Create user: {user_id}"
    


# Proxy that handles authentication and authorization
class OperationsProxy(AbstractOperations):
    def __init__(self):
        self._real_operations = ConcreteOperations()
        
    def _check_authentication(self) -> Optional[dict]:
        return session.get('user')
    
    def _get_user_role(self) -> UserRole:
        user = self._check_authentication()
        if not user:
            return UserRole.GUEST
        # You might want to store the role in the session or fetch it from DB
        return UserRole(user.get('role', UserRole.REGISTERED.value))
    
    def _check_authorization(self, required_role: UserRole) -> bool:
        user_role = self._get_user_role()
        return user_role.value >= required_role.value

    # Handling CampsiteList objects
    def create_list(self, name: str):
        if not self._check_authorization(UserRole.REGISTERED):
            abort(403, "Must be registered to create lists")
        return self._real_operations.create_list(name)
    
    def view_list(self, list_id: int):
        return self._real_operations.view_list(list_id)
    
    def delete_list(self, list_id: int):
        if not self._check_authorization(UserRole.REGISTERED):
            abort(403, "Must be registered to delete lists")
        # Add additional check for list ownership
        return self._real_operations.delete_list(list_id)
    
    # Handling Campsite objects
    def create_campsite(self, name: str):
        if not self._check_authorization(UserRole.REGISTERED):
            abort(403, "Must be registered to create campsites")
        return self._real_operations.create_list(name)
    
    def view_list(self, list_id: int):
        return self._real_operations.view_list(list_id)
    
    def delete_list(self, list_id: int):
        if not self._check_authorization(UserRole.REGISTERED):
            abort(403, "Must be registered to delete lists")
        # Add additional check for list ownership
        return self._real_operations.delete_list(list_id)

    # Handling User objects

# Decorator for route-level authentication
def requires_auth(role: UserRole):
    
    def decorator(f):
        @wraps(f)

        def decorated_function(*args, **kwargs):
            proxy = OperationsProxy()
            if not proxy._check_authorization(role):
                abort(403, f"Required role: {role.name}")
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# Example of ownership checking
class OwnershipProxy():
    def delete_list(self, list_id: int):
        if not self._check_authorization(UserRole.REGISTERED):
            abort(403, "Must be registered to delete lists")
            
        user = self._check_authentication()
        list_owner = self._get_list_owner(list_id)
        
        if user['id'] != list_owner and not self._check_authorization(UserRole.ADMIN):
            abort(403, "Must be the owner or an admin to delete this list")
            
        return self._real_operations.delete_list(list_id)
    
    def _get_list_owner(self, list_id: int) -> int:
        # Implementation to get list owner from database
        pass