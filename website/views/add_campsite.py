from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user
import traceback

from website.controllers.controllers import *
from website.controllers.images import campsitePhotoUploadSuccessful
from website.extensions import socketio

add_campsite_bp = Blueprint("add_campsite", __name__)


@add_campsite_bp.route("/", methods=["GET", "POST"])
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