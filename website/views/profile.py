from os import path
from re import match

from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import current_user
from flask import jsonify
from werkzeug.utils import secure_filename

from .. import db
from ..models.models import User, CampSiteList

from website.controllers.controllers import *
from website.controllers.images import photo_manager
from website.controllers.campsite import get_user_campsite_lists

profile_bp = Blueprint("profile", __name__, url_prefix="/profile/")

@profile_bp.route("<int:id>", methods=["GET", "POST"])
def profile(id):
    user = User.query.get(id)
    if not user:
        return render_template("error.html", user=current_user, msg="No such user found.")
    
    if request.method == "POST":
        if current_user.id != id:
            return jsonify({"error": "Unauthorized"}), 403
            
        field = request.form.get("field")
        value = request.form.get("value")
        
        # Handle profile photo upload
        if "photo" in request.files:
            file = request.files["photo"]
            if file and photo_manager.allowed_file(file.filename):
                filename = secure_filename(str(user.id) + ".jpg")
                file.save(path.join(photo_manager.user_upload_path, filename))
                return jsonify({"success": True})
                
        # Handle other field updates
        if field in ["name", "activities", "location", "age"]:
            if field == "age":
                try:
                    value = int(value)
                except ValueError:
                    return jsonify({"error": "Invalid age value"}), 400
            
            setattr(user, field, value)
            db.session.commit()
            return jsonify({"success": True})
            
        return jsonify({"error": "Invalid field"}), 400

    profile_photo_path = str(user.id) + ".jpg"
    placeholderFlag = path.exists(photo_manager.user_upload_path + profile_photo_path)

    collaborated_list_count = db.session.query(CampSiteList)\
        .join(list_permissions)\
        .filter(CampSiteList.owner_id == user.id)\
        .distinct(CampSiteList.id)\
        .count()
    
    return render_template(
        "profile.html",
        user=user,
        placeholderFlag=placeholderFlag,
        photoPath=profile_photo_path,
        is_owner=current_user.is_authenticated and current_user.id == id,
        collaborated_list_count=collaborated_list_count
    )

@profile_bp.route("view-lists", methods=["GET"])
def view_user_campsitLists(): 
    """Returns an HTML page of all campsite lists associated with the logged in user's profile.

    Returns:
        str: HTML page with relevant information
    """
    user_id = current_user.id
    campsiteLists = get_user_campsite_lists(user_id)

    # Map the logged in user lists with their shared users
    lists_collaborators = {}

    for campsite_list in campsiteLists:
        # Get all users this list is shared with, along with their permission types and store as tuple
        shared_users = db.session.query(User, list_permissions.c.permission_type)\
            .join(list_permissions, User.id == list_permissions.c.user_id)\
            .filter(list_permissions.c.list_id == campsite_list.id)\
            .all()
            
        lists_collaborators[campsite_list.id] = shared_users
    
    return render_template(
        "view_lists.html",
        user=current_user,
        campsiteLists=campsiteLists,
        lists_collaborators=lists_collaborators
    )

@profile_bp.route("create-list", methods=["GET", "POST"])
def create_list(): 
    
    # TODO: Move this logic to controllers 
    user_id = current_user.id
    campsites = get_user_campsite_lists(user_id)

    if request.method == "POST":
        name = request.form.get("name")
        visibility = request.form.get("visibility")

        errors = False

        if not name or name == "":
            flash("Must provide a valid name", category="error")
            errors = True
        if not visibility:
            # should not be possible
            flash("Must select a visibility type", category="error")
            errors = True
        
        pattern = r"^[a-zA-Z0-9 _-]+$"

        if not bool(match(pattern, name)):
            flash("Name should include alphanumeric characters only", category="error")
            errors = True
        
        # Check for duplicate entry
        campsite_list_exists = db.session.query(CampSiteList).filter(
            CampSiteList.owner_id == user_id,
            CampSiteList.name == name
        ).first() is not None

        if campsite_list_exists:
            flash("A campsite list with this name already exists", category="error")
            errors = True

        if not errors:
            # Construct CampSiteList entry
            owner = User.query.get(user_id)
            
            from ..models.models import ListVisibilityType

            vis_map = {"private": ListVisibilityType.LIST_VISIBILITY_PRIVATE, "protected": ListVisibilityType.LIST_VISIBILITY_PROTECTED, "public": ListVisibilityType.LIST_VISIBILITY_PUBLIC}
            visibility = vis_map[visibility]

            new_campsite_list = CampSiteList(
                owner_id = user_id,
                owner = owner,
                visibility = visibility,
                name = name
            )

            # TODO: Can this fail?
            db.session.add(new_campsite_list)
            db.session.commit()
            
            flash("Successfully added list!", category="info")
    
    return render_template(
        "create_list.html",
        user=current_user,
        campsites=campsites
    )