from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import CampSite, User
from . import db
import json

views = Blueprint("views", __name__)


@views.route("/", methods=["GET", "POST"])
def home():
    # handle campsite form submissions
    if request.method == "POST":
        # TODO: Visibility should be set on list creation, not campsite creation
        name = request.form.get("name")
        description = request.form.get("description")
        isPrivate = True if request.form.get("visibility") == "on" else False
        hasPotable = True if request.form.get("potable") == "on" else False
        hasElectrical = True if request.form.get("electrical") == "on" else False

        # validate user campsite submission
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))

        if latitude > 90 or latitude < -90:
            flash("Invalid latitude", category="error")
        if longitude > 180 or longitude < -180:
            flash("Invalid longitude", category="error")
        else:
            try:
                # save entries to model
                new_campsite = CampSite(
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    potableWater=hasPotable,
                    electrical=hasElectrical,
                    description=description
                )
                db.session.add(new_campsite)
                db.session.commit()
                flash("Campsite added!", category="success")
                return redirect(url_for("views.home"))
            except:  # TODO: we should catch specific exceptions https://docs.sqlalchemy.org/en/20/errors.html
                flash("An error occurred.", category="error")

    # get all campsite markers from database CampSite table for displaying to user
    try:
        # TODO: use cookies to store these? Generating these with every page load seems extraordinarily wasteful
        campsites = CampSite.query.all()
        campsite_lats = [getattr(c, "latitude") for c in campsites]
        campsite_lons = [getattr(c, "longitude") for c in campsites]
        campsite_ids = [getattr(c, "id") for c in campsites]
        campsite_names = [getattr(c, "name") for c in campsites]
        assert (
            len(campsite_lats)
            == len(campsite_lons)
            == len(campsite_ids)
            == len(campsite_names)
        )
        return render_template(
            "home.html",
            user=current_user,
            lats=campsite_lats,
            lons=campsite_lons,
            ids=campsite_ids,
            names=campsite_names,
        )
    except AssertionError:
        return render_template("error.html")


@views.route("/profile", methods=["GET", "POST"])
def profile():
    return render_template("profile.html", user=current_user)


@views.route("/campsites/<int:id>", methods=["GET", "POST"])
def show_campsite(id):
    campsite = CampSite.query.get(id)
    # check that user has signed in 
    # if not current_user.is_authenticated:
    #     flash('Please register or sign in to view campsites.', category='error')
    #     return redirect(url_for('views.home'))
    
    return render_template("campsite.html", user=current_user, campsite=campsite)
