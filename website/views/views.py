from os import path, getcwd, getenv
from re import sub, match
from typing import Tuple, Dict, Union

from flask import Blueprint, render_template, request, flash, redirect, url_for, make_response, jsonify
from flask_login import login_required, current_user
from flask import jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta
import traceback

from .. import db
from ..models.models import User, CampSite, CampSiteList, ListPermissionType

from website.controllers.controllers import *
from website.extensions import socketio

from website.controllers.notifications import collaboration_notifier

load_dotenv()

# load env vars defined in .env
CAMPSITE_PHOTO_UPLOAD_PATH = getenv("CAMPSITE_PHOTO_UPLOAD_PATH")
ALLOWED_EXTENSIONS = getenv("ALLOWED_EXTENSIONS")

views = Blueprint("views", __name__)

# Root view
@views.route("/")
def home():
    try:
        # Get all campsites for the map
        campsite_lats, campsite_lons, campsite_ids, campsite_names = get_all_campsites()
        
        # Initialize variables for user's campsite lists
        user_lists = None
        list_campsites = set()
        selected_list_name = ""
        
        # If user is authenticated, get their campsite lists
        if current_user.is_authenticated:
            user_lists = CampSiteList.query.filter_by(owner_id=current_user.id).all()
            
            # If a list is selected, get its campsites' IDs
            selected_list_id = request.args.get('list_id')
            if selected_list_id:
                selected_list = CampSiteList.query.get(selected_list_id)
                if selected_list and selected_list.owner_id == current_user.id:
                    list_campsites = {site.id for site in selected_list.campsites}
                    selected_list_name = selected_list.name

        # Create a list of boolean flags for whether each campsite is in the selected list
        in_selected_list = [id in list_campsites for id in campsite_ids]
        
        return render_template(
            "home.html",
            user=current_user,
            lats=campsite_lats,
            lons=campsite_lons,
            ids=campsite_ids,
            names=campsite_names,
            user_lists=user_lists,
            in_selected_list=in_selected_list,
            selected_list_name=selected_list_name
        )
    except AssertionError:
        return render_template(
            "error.html", 
            user=current_user, 
            msg="We were unable to populate the map."
        )

# Campsite views
@views.route("/add-campsite", methods=["GET", "POST"])
def add_campsite():
    lat = "Enter Latitude"
    lon = "Enter Longitude"

    campsiteLists = None
    if not current_user.is_authenticated:
            flash("Only registered users can submit a campsite", category="error")
    else:
        campsiteLists = get_user_campsite_lists(current_user.id)

    if request.method == "POST":
        
        # Commit the form contents to the DB and handle WebSocket event
        try:
            name = request.form.get("name")
            description = request.form.get("description")
            campingStyle = request.form.get("campingStyle")
            hasPotable = request.form.get("potable") == "on"
            hasElectrical = request.form.get("electrical") == "on"
            isBackcountry = request.form.get("backcountry") == "on"
            isPermitReq = request.form.get("permitReq") == "on"
            firePit = request.form.get("firePit") == "on"
            submittedBy = User.query.filter_by(id=current_user.id).first()
            latitude = float(request.form.get("latitude"))
            longitude = float(request.form.get("longitude"))
            campsiteListId = None if request.form.get("campsiteList") == "None" else request.form.get("campsiteList")

            # Commit the campsite first
            new_campsite = commit_campsite(
                name, latitude, longitude, hasPotable, hasElectrical, 
                description, isBackcountry, isPermitReq, campingStyle, 
                firePit, submittedBy, campsiteListId
            )
            flash("Campsite added.", category="success")

            # Emit the WebSocket event
            try:
                print("Attempting to emit WebSocket event...")
                socketio.emit('map_update', {
                    'type': 'new_campsite',
                    'campsite': {
                        'id': new_campsite.id,  
                        'name': name,
                        'latitude': latitude,
                        'longitude': longitude
                    }
                }, broadcast=True)
                print("WebSocket event emitted successfully")
            except Exception as websocket_error:
                print(f"WebSocket error: {str(websocket_error)}")
                print(f"Traceback: {traceback.format_exc()}")

            if campsitePhotoUploadSuccessful():
                return redirect(url_for("views.add_campsite"))

        except Exception as e:
            print(f"Error in add_campsite: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            flash("An error occurred when committing this form to a database entry.", category="error")

    if request.method == "GET":
        lat = request.args.get("lat") if request.args.get("lat") else ""
        lon = request.args.get("lon") if request.args.get("lon") else ""
        if lat and lon:
            return render_template(
                "add_site.html", 
                user=current_user, 
                lat=lat, 
                lon=lon, 
                campsiteLists=campsiteLists
            )

    return render_template(
        "add_site.html", 
        user=current_user, 
        lat=lat, 
        lon=lon, 
        campsiteLists=campsiteLists
    )

@views.route("/campsites/<int:id>", methods=["GET", "POST"])
def show_campsite(id):
    result = get_campsite_details(id)
    if not result:
        return render_template("error.html", user=current_user, msg="The campsite does not exist."), 404
    
    campsite, submitted_by, locale = result
    campsite_photo_path = sub("[^A-Za-z0-9]+", "", campsite.name) + ".jpg"
    placeholderFlag = path.exists("website/static/images/campsites/" + campsite_photo_path)
    
    can_edit = can_edit_campsite(campsite, current_user)

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("You must be logged in to perform this action", category="error")
            return redirect(url_for("auth.login"))

        if "rating" in request.form:
            # Handle rating submission
            rating = float(request.form.get("rating"))
            if not rating:
                flash("Error getting rating.", category="error")
            else:
                success, message = add_campsite_rating(campsite, rating, current_user)
                flash(message, category="success" if success else "error")
                
        elif "edit_campsite" in request.form and can_edit:
            # Handle campsite edits
            try:
                campsite.name = request.form.get("name")
                campsite.description = request.form.get("description")
                campsite.potableWater = bool(request.form.get("potableWater"))
                campsite.electrical = bool(request.form.get("electrical"))
                campsite.firePit = bool(request.form.get("firePit"))
                campsite.backCountry = bool(request.form.get("backCountry"))
                campsite.permitRequired = bool(request.form.get("permitRequired"))
                campsite.campingStyle = request.form.get("campingStyle")
                
                db.session.commit()
                flash("Campsite updated successfully!", category="success")
            except Exception as e:
                db.session.rollback()
                flash("Error updating campsite.", category="error")
        else:
            flash("You don't have permission to edit this campsite.", category="error")

    return render_template(
        "campsite.html",
        user=current_user,
        campsite=campsite,
        photo_path=campsite_photo_path,
        locale=locale,
        placeholder=placeholderFlag,
        submitted_by=submitted_by,
        can_edit=can_edit
    )

# Profile views
@views.route("/profile/<int:id>", methods=["GET", "POST"])
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
            if file and allowed_file(file.filename):
                filename = secure_filename(str(user.id) + ".jpg")
                file.save(path.join("website/static/images/profiles/", filename))
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
    placeholderFlag = path.exists("website/static/images/profiles/" + profile_photo_path)

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

# Add this helper function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
    
# Campsite list views
@views.route("/my-lists/", methods=["GET"])
def show_lists(): 
    
    return render_template(
        "mylists.html",
        user=current_user,
    )

@views.route("/view-lists/", methods=["GET"])
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

@views.route("/remove-collaborator/<int:list_id>/<int:user_id>", methods=["POST"])
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

@views.route("/campsite-lists/<int:list_id>/rename", methods=["POST"])
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

@views.route("/campsite-lists/<int:list_id>/collaborate", methods=["POST"])
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

@views.route("/campsite-lists/<int:list_id>", methods=["DELETE"])
@login_required
def delete_campsite_list(list_id):
    campsite_list = CampSiteList.query.get_or_404(list_id)
    
    # Check if user owns this list
    if campsite_list.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    for campsite in campsite_list.campsites:
        campsite.campsite_list = None
        campsite.campsite_list_id = None
    
    # Then delete the list
    db.session.delete(campsite_list)
    db.session.commit()
    
    return jsonify({'success': True})

@views.route("/campsite-lists/<int:id>")
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

@views.route("/modify-list/", methods=["GET", "POST"])
def modify_list(): 
    return render_template(
        "modify_list.html"
    )

@views.route("/create-list/", methods=["GET", "POST"])
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
        
        # TODO: Check for duplicate entry

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

@views.route('/search/', methods=['GET', 'POST'])
def search_campsites():
    # Get all unique camping styles for the dropdown
    camping_styles = db.session.query(CampSite.campingStyle).distinct().all()
    camping_styles = [style[0] for style in camping_styles if style[0]]  # Remove None values
    
    query = CampSite.query
    
    if request.method == 'POST':
        # Get search parameters
        name = request.form.get('name', '').strip()
        potable_water = request.form.get('potableWater')
        electrical = request.form.get('electrical')
        fire_pit = request.form.get('firePit')
        back_country = request.form.get('backCountry')
        permit_required = request.form.get('permitRequired')
        camping_style = request.form.get('campingStyle')
        min_rating = request.form.get('minRating')
        
        # Apply filters
        if name:
            query = query.filter(CampSite.name.ilike(f'%{name}%'))
        if potable_water == 'true':
            query = query.filter(CampSite.potableWater.is_(True))
        if electrical == 'true':
            query = query.filter(CampSite.electrical.is_(True))
        if fire_pit == 'true':
            query = query.filter(CampSite.firePit.is_(True))
        if back_country == 'true':
            query = query.filter(CampSite.backCountry.is_(True))
        if permit_required == 'true':
            query = query.filter(CampSite.permitRequired.is_(True))
        if camping_style:
            query = query.filter(CampSite.campingStyle == camping_style)
        if min_rating:
            query = query.filter(CampSite.rating >= float(min_rating))
            
        results = query.all()
    else:
        results = []
    
    return render_template('search.html',
                         results=results,
                         camping_styles=camping_styles,
                         user=current_user
                         )
    


@views.route('/set-welcome-banner-cookie', methods=['POST'])
def set_welcome_banner_cookie():
    response = make_response(jsonify({'status': 'success'}))
    
    # Set cookie to expire in 30 days
    expires = datetime.now() + timedelta(days=30)
    
    # Set the cookie
    response.set_cookie(
        'bannerClosed',
        'true',
        expires=expires,
        secure=True,  # Only send cookie over HTTPS
        httponly=False,  
        samesite='Strict'
    )
    
    return response

@views.route('/set-popup-cookie', methods=['POST'])
def set_popup_cookie():
    response = make_response(jsonify({'status': 'success'}))
    
    # Set cookie to expire in 30 days
    expires = datetime.now() + timedelta(days=30)
    
    # Set the cookie
    response.set_cookie(
        'tipClosed',
        'true',
        expires=expires,
        secure=True,  # Only send cookie over HTTPS
        httponly=False,  
        samesite='Strict'
    )
    
    return response



# Keep the helper functions in views.py
def campsitePhotoUploadSuccessful():
    # retrieve file from request
    photo = request.files["photo"]

    # check user upload
    validity = False
    if not photo:
        return validity

    if photo.filename == "":
        flash("No file selected.", category="error")
        return validity

    if not allowed_file(photo.filename):
        flash("Allowed file types are" + ALLOWED_EXTENSIONS, category="error")
        return validity

    # name file after the submitted campsite name
    file = request.form.get("name")

    # strip special chars from file
    file = sub("[^A-Za-z0-9]+", "", file) + ".jpg"

    filename = secure_filename(file)
    filepath = path.join(getcwd(), CAMPSITE_PHOTO_UPLOAD_PATH, filename)

    # check if file already exists on server
    if path.isfile(filepath):
        flash(
            "Your uploaded file already exists on the server (is your campsite entry a duplicate?)",
            category="error",
        )
        return validity

    validity = True

    # handle png uploads: convert to jpg then save
    if photo.filename.split(".")[-1] != ".jpg":
        from PIL import Image

        im = Image.open(photo)
        rgb_im = im.convert("RGB")
        rgb_im.save(filepath)
        return validity

    # save the file
    photo.save(filepath)
    return validity

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@views.errorhandler(413)
def error413(e):
    return render_template("error.html", user=current_user), 413