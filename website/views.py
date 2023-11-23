from os import getcwd, getenv, path
from json import loads, dumps

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from .models import CampSite, User
from . import db

load_dotenv()

# load env vars defined in .env
CAMPSITE_PHOTO_UPLOAD_PATH = getenv("CAMPSITE_PHOTO_UPLOAD_PATH")
ALLOWED_EXTENSIONS = getenv("ALLOWED_EXTENSIONS")

views = Blueprint("views", __name__)


@views.route("/", methods=["GET", "POST"])
def home():
    # handle campsite form submissions
    if request.method == "POST":
        # TODO: Visibility should be set on list creation, not campsite creation
        name = request.form.get("name")
        description = request.form.get("description")
        hasPotable = True if request.form.get("potable") == "on" else False
        hasElectrical = True if request.form.get("electrical") == "on" else False

        # handle photo uploads
        validCampsitePhotoUpload = campsitePhotoUploadSuccessful()
        if not validCampsitePhotoUpload:
            return redirect(url_for('views.home'))   

        # validate user campsite submission
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))

        if latitude > 90 or latitude < -90:
            flash("Invalid latitude", category="error")
        if longitude > 180 or longitude < -180:
            flash("Invalid longitude", category="error")

        # check for json serializable input
        
        # handle validated input
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

@views.route("/add-campsite", methods=["GET", "POST"])
def addsite():
    return render_template("add_site.html", user=current_user)


@views.route("/campsites/<int:id>", methods=["GET", "POST"])
def show_campsite(id):
    campsite = CampSite.query.get(id)
    # check that user has signed in 
    # if not current_user.is_authenticated:
    #     flash('Please register or sign in to view campsites.', category='error')
    #     return redirect(url_for('views.home'))
    
    return render_template("campsite.html", user=current_user, campsite=campsite)


# Checks that the request contains a valid photo upload, then saves the file to the CAMPSITE_PHOTO_UPLOAD_PATH path (set in .env). Only jpgs will be saved. Returns a boolean flag for the validity of the upload pipe (true if input validated and in jpg form)
def campsitePhotoUploadSuccessful() -> bool:
    # retrieve file from request
    photo = request.files['photo']

    # check user upload
    validity = False
    if not photo:
        return validity
    
    if photo.filename == '':
        flash("No file selected.", category='error')
        return validity
    
    if not allowed_file(photo.filename):
        flash("Allowed file types are" + ALLOWED_EXTENSIONS, category='error')
        return validity
    
    # name file after the submitted campsite name
    campsiteSubdir = request.form.get("name") + ".jpg"
    filename = secure_filename(campsiteSubdir)
    filepath = path.join(getcwd(), CAMPSITE_PHOTO_UPLOAD_PATH, filename)

    # check if file already exists on server
    if path.isfile(filepath):
        flash("Your uploaded file already exists on the server (is your campsite entry a duplicate?)", category='error')
        return validity
    
    validity = True
    
    # handle png uploads: convert to jpg then save
    if photo.filename.split('.')[-1] != '.jpg':
        from PIL import Image
        im = Image.open(photo)
        rgb_im = im.convert('RGB')
        rgb_im.save(filepath)
        return validity
    
    # save the file
    photo.save(filepath)
    return validity
    

# helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.errorhandler(413)
def error413(e):
    return render_template('error.html'), 413