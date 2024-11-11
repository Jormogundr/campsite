from re import match
from typing import Tuple, Dict, Union

from flask import jsonify
from flask_login import current_user
from ..models.models import *


def validate_collab_request(email: str, list_id: int) -> Union[Tuple[Dict[str, str], int], None]:
    """Validate the share request parameters."""
    
    # Check email presence
    if not email:
        result =  jsonify({
            'error': 'No email provided',
            'details': 'Please provide an email address.'
        }), 400
        print(f"Validation failed - {result}")
        return result
    
    # Validate email format
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not bool(match(pattern, email)):
        result =  jsonify({
            'error': 'Invalid Email Address format',
            'details': 'The provided email address is not properly formatted.'
        }), 400
        print(f"Validation failed - {result}")
        return result
    
    # Check if list exists
    campsite_list = CampSiteList.query.get(list_id)
    if not campsite_list:
        result = jsonify({
            'error': 'List Not Found',
            'details': 'The specified campsite list does not exist.'
        }), 404
        print(f"Validation failed - {result}")
        return result
    
    if campsite_list.visibility != ListVisibilityType.LIST_VISIBILITY_PUBLIC.value:
        result = jsonify({
            'error': 'Invalid visibility',
            'details': 'You may not collaborate on non-public lists.'
        }), 404
        print(f"Validation failed - {result}")
        return result
        
    
    # Check ownership
    if campsite_list.owner_id != current_user.id:
        result =  jsonify({
            'error': 'Unauthorized',
            'details': 'You do not have permission to share this list.'
        }), 403
        print(f"Validation failed - {result}")
        return result
    
    # Check if target user exists
    other_user = User.query.filter_by(email=email).first()
    if not other_user:
        result =  jsonify({
            'error': 'Unknown Other User',
            'details': 'No user account found with this email address.'
        }), 404
        print(f"Validation failed - {result}")
        return result
        
    # Check if user is trying to share with themselves
    if other_user.id == current_user.id:
        result =  jsonify({
            'error': 'Invalid Share Request',
            'details': 'You cannot share a list with yourself.'
        }), 400
        print(f"Validation failed - {result}")
        return result
    
    # Check if the list is already shared with this user
    existing_permission = campsite_list.get_user_permission(other_user)
    if existing_permission:
        result = jsonify({
            'error': 'Already Shared',
            'details': 'This list is already shared with this user.'
        }), 400
        print(f"Validation failed - {result}")
        return result
    
    print("Validation passed!")
    return None