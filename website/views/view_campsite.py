from os import path
from re import sub

from flask import render_template, request, flash, redirect, url_for, jsonify, Blueprint
from flask_login import current_user
from flask import jsonify

from .. import db
from ..models.models import CampSite

from website.controllers.controllers import *
from website.controllers.images import handle_campsite_photos, delete_campsite_photo

view_campsite_bp = Blueprint("view_campsite", __name__, url_prefix="campsites/")

@view_campsite_bp.route("<int:id>", methods=["GET", "POST"])
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

@view_campsite_bp.route("<int:id>/delete", methods=['POST', 'DELETE'])
def delete_campsite(id):
    campsite = CampSite.query.get_or_404(id)
    
    # Check if user is the original submitter
    if campsite.submittedBy != current_user.name:
        return jsonify({'error': 'Unauthorized - only the submitter can delete this campsite'}), 403
    
    try:
        db.session.delete(campsite)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@view_campsite_bp.route("<int:id>/photos", methods=["POST"])
@login_required
def upload_campsite_photos(id):
    campsite = CampSite.query.get_or_404(id)
    
    # Check permissions
    if not can_edit_campsite(campsite, current_user):
        flash("You don't have permission to add photos to this campsite", category="error")
        return redirect(url_for('views.show_campsite', id=id))
    
    try:
        if handle_campsite_photos(campsite, request.files):
            flash("Photos uploaded successfully!", category="success")
        else:
            flash("No photos were uploaded", category="error")
            
    except Exception as e:
        flash(str(e), category="error")
    
    return redirect(url_for('view_campsite.show_campsite', id=id))

@view_campsite_bp.route("photo/<int:photo_id>", methods=["DELETE"])
@login_required
def delete_campsite_photo_route(photo_id):
    try:
        photo = CampsitePhoto.query.get_or_404(photo_id)
        campsite = photo.campsite
        
        # Check permissions
        if not can_edit_campsite(campsite, current_user):
            return jsonify({"message": "You don't have permission to delete this photo"}), 403
            
        delete_campsite_photo(photo_id)
        return jsonify({"message": "Photo deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@view_campsite_bp.route("photo/<int:photo_id>/primary", methods=["POST"])
@login_required
def set_primary_photo_route(photo_id):
    try:
        photo = CampsitePhoto.query.get_or_404(photo_id)
        campsite = photo.campsite
        
        # Check permissions
        if not can_edit_campsite(campsite, current_user):
            return jsonify({"message": "You don't have permission to modify this photo"}), 403
        
        # Update primary photo
        CampsitePhoto.query.filter_by(campsite_id=campsite.id).update({"is_primary": False})
        photo.is_primary = True
        db.session.commit()
        
        return jsonify({"message": "Primary photo updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
