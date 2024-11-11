from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask import jsonify

from .. import db
from ..models.models import User, CampSiteList, ListPermissionType

from website.controllers.controllers import *
from website.controllers.notifications import collaboration_notifier

campsite_lists_bp = Blueprint("campsite_lists", __name__, url_prefix="/campsite-lists/")

@campsite_lists_bp.route("<int:list_id>/rename", methods=["POST"])
@login_required
def rename_campsite_list(list_id):
    data = request.get_json()
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'error': 'No name provided'}), 400
        
    campsite_list = CampSiteList.query.get_or_404(list_id)
    
    # Check if user owns this list
    if campsite_list.owner_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    campsite_list.name = new_name
    db.session.commit()
    
    return jsonify({'success': True})
    

@campsite_lists_bp.route("<int:list_id>/collaborate", methods=["POST"])
@login_required
def collab_campsite_list(list_id):
    data = request.get_json()
    email = data.get('email', '').strip()
    
    validation_result = validate_collab_request(email, list_id)
    if validation_result:
        # Invalid if not None
        return validation_result
    
    try:
        campsite_list = CampSiteList.query.get_or_404(list_id)
        other_user = User.query.filter_by(email=email).first()
        
        campsite_list.add_collaborator(other_user, ListPermissionType.PERMISSION_WRITE)
        
        # Verify the permission was set correctly
        permission = campsite_list.get_user_permission(other_user)
        can_edit = permission in (ListPermissionType.PERMISSION_WRITE, ListPermissionType.PERMISSION_ADMIN)
        
        if not can_edit:
            return jsonify({
                'error': 'Failed to set user permissions',
                'details': 'The system could not grant write access to the user.'
            }), 500
        
        # Send email to the other user
        collaboration_notifier.notify_new_collaborator(
            owner=current_user,
            collaborator=other_user,
            campsite_list=campsite_list
        )
            
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Successfully shared list with {email}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'details': str(e)
        }), 500

@campsite_lists_bp.route("<int:list_id>", methods=["DELETE"])
@login_required
def delete_campsite_list(list_id):
    campsite_list = CampSiteList.query.get_or_404(list_id)
    
    # Check if user owns this list
    if campsite_list.owner_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    for campsite in campsite_list.campsites:
        campsite.campsite_list = None
        campsite.campsite_list_id = None
    
    # Then delete the list
    db.session.delete(campsite_list)
    db.session.commit()
    
    return jsonify({'success': True})

@campsite_lists_bp.route("<int:id>")
def view_campsiteList(id):
    """
    
    Return an HTML page with the information necessary to display a specific campsite list details.

    Args:
        id (int): The model campsite list id

    Returns:
        str: HTML page with relevant information
    """

    campSiteList = get_campsite_list_campsites(id)
    if not campSiteList:
        return render_template("error.html", msg="The campsite list does not exist."), 404
    
    campsites = campSiteList.campsites
    
    return render_template(
        "campsite_list.html",
        user=current_user,
        campsitelist=campSiteList,
        campsites = campsites,
        list_id=id,
        list_name=campSiteList.name
    )

@campsite_lists_bp.route("/remove-collaborator/<int:list_id>/<int:user_id>", methods=["POST"])
@login_required
def remove_collaborator(list_id, user_id):
    """Remove a collaborator from a campsite list"""
    campsite_list = CampSiteList.query.get_or_404(list_id)
    
    # Check if current user is the owner
    if campsite_list.owner_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    user_to_remove = User.query.get_or_404(user_id)
    
    try:
        campsite_list.remove_collaborator(user_to_remove)
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@campsite_lists_bp.route("/my-lists/", methods=["GET"])
def show_lists(): 
    
    return render_template(
        "mylists.html",
        user=current_user,
    )

@campsite_lists_bp.route("modify-list", methods=["GET", "POST"])
def modify_list(): 
    return render_template(
        "modify_list.html"
    )
