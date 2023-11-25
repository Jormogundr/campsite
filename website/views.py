from os import getcwd, getenv, path
from re import findall, sub

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import reverse_geocode

from .models import CampSite, User
from . import db

load_dotenv()

# load env vars defined in .env
CAMPSITE_PHOTO_UPLOAD_PATH = getenv("CAMPSITE_PHOTO_UPLOAD_PATH")
ALLOWED_EXTENSIONS = getenv("ALLOWED_EXTENSIONS")

views = Blueprint("views", __name__)


@views.route("/", methods=["GET", "POST"])
def home():
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
        return render_template("error.html", user=current_user, msg="We were unable to populate the map.")


@views.route("/profile/<int:id>", methods=["GET", "POST"])
def profile(id):
    user = User.query.get(id)
    
    if not user:
        return render_template("error.html", user=current_user, msg="No such user found.")

    profile_photo_path =  str(user.id) + ".jpg"

    # provide default photo path for profile if user has not uploaded
    placeholderFlag = path.exists("website/static/images/profiles/" + profile_photo_path)
    print(profile_photo_path, placeholderFlag)

    
    return render_template("profile.html", user=user, placeholderFlag=placeholderFlag, photoPath=profile_photo_path)


@views.route("/add-campsite", methods=["GET", "POST"])
def addsite():
    # handle campsite form submissions
    if request.method == "POST":
        # TODO: Visibility should be set on list creation, not campsite creation
        name = request.form.get("name")
        description = request.form.get("description")
        campingStyle = request.form.get("campingStyle")

        # handle checkbox form items
        hasPotable = True if request.form.get("potable") == "on" else False
        hasElectrical = True if request.form.get("electrical") == "on" else False
        isBackcountry = True if request.form.get("backcountry") == "on" else False
        isPermitReq = True if request.form.get("permitReq") == "on" else False
        firePit = True if request.form.get("firePit") == "on" else False
        submittedBy = current_user.id
        
        # initialize list for collecting and displaying errors
        errors = []

        # handle name validation, since name is used for file uploads
        invalid_chars = findall(r"[^A-Za-z0-9 ]+", name)
        if len(invalid_chars) != 0:
            error_msg = "Invalid characters in name: {}".format(invalid_chars)
            errors.append(error_msg)

        # validate user campsite submission
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))

        if latitude > 90 or latitude < -90:
            error_msg = "Invalid latitude."
            errors.append(error_msg)
        if longitude > 180 or longitude < -180:
            error_msg = "Invalid longitude."
            errors.append(error_msg)

        # handle response to invalid form entries
        if len(errors) != 0:
            for error in errors:
                flash(error, category="error")
            return redirect(url_for("views.addsite"))

        # commit validated input to db
        try:
            # save entries to model
            new_campsite = CampSite(
                name=name,
                latitude=latitude,
                longitude=longitude,
                potableWater=hasPotable,
                electrical=hasElectrical,
                description=description,
                backCountry=isBackcountry,
                permitRequired=isPermitReq,
                campingStyle=campingStyle,
                firePit=firePit,
                submittedBy=submittedBy,
                rating = 5.0,
                numRatings = 0
            )
            db.session.add(new_campsite)
            db.session.commit()
            flash("Campsite added.", category="success")

            # handle photo uploads just before returning since this writes to server
            if len(invalid_chars) == 0:
                campsitePhotoUploadSuccessful()

            return redirect(url_for("views.addsite"))
        except:  # TODO: we should catch specific exceptions https://docs.sqlalchemy.org/en/20/errors.html
            flash("An error occurred when commiting this form to a database entry.", category="error")

    return render_template("add_site.html", user=current_user)


@views.route("/campsites/<int:id>", methods=["GET", "POST"])
def show_campsite(id):
    campsite = CampSite.query.get(id)

    # handle routing for campsites that don't exist
    if not campsite:
        return render_template("error.html", user=current_user, msg="The campsite does not exist."), 404
    
    # use same method used to save file in getting file
    campsite_photo_path = sub('[^A-Za-z0-9]+', '', campsite.name ) + '.jpg'

    # use reverse geocoding to get location information based on lat/lon
    coordinates = (campsite.latitude, campsite.longitude),
    locale = reverse_geocode.search(coordinates)[0]

    # provide default photo path for campsite if user has not uploaded
    placeholderFlag = path.exists("website/static/images/campsites/" + campsite_photo_path)

    # handle campsite ratings
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash("Only registered users can submit a campsite rating", category="error")
            return render_template("campsite.html", user=current_user, campsite=campsite, photo_path=campsite_photo_path, locale=locale, placeholder=placeholderFlag)
        
        rating = request.form.get("rating")

        # validation
        if not rating:
            flash("Error getting rating.", category="error")
            return render_template("campsite.html", user=current_user, campsite=campsite, photo_path=campsite_photo_path, locale=locale, placeholder=placeholderFlag)
        
        # check if user has already rated this site
        users_that_have_rated = campsite.ratedUsers

        # if user rated list is initialized
        if users_that_have_rated:
            # check if user has already rated
            if current_user.id in users_that_have_rated:
                flash("You've already rated this campsite.", category="error")
                return render_template("campsite.html", user=current_user, campsite=campsite, photo_path=campsite_photo_path, locale=locale, placeholder=placeholderFlag)
        else:
            users_that_have_rated = [current_user.id]
        
        # calculate new campsite average rating
        avg_rating = campsite.rating
        num_ratings = campsite.numRatings

        # no rating yet
        if num_ratings is None or num_ratings == 0:
            avg_rating = rating
            num_ratings = 1
        # average the rating
        else:
            num_ratings += 1
            avg_rating = (avg_rating + rating)/(num_ratings)
        
        # commit average rating to db
        try:
            # save entries to model
            # round rating to nearest whole number
            campsite.rating = round(float(avg_rating), 2)
            campsite.numRatings = int(num_ratings)
            campsite.ratedUsers = users_that_have_rated
            db.session.commit()
            flash("Rating submitted", category="success")
        except:  # TODO: we should catch specific exceptions https://docs.sqlalchemy.org/en/20/errors.html
            flash("An error occurred when handling this.", category="error")

    submitted_by = User.query.get(campsite.submittedBy)
    return render_template("campsite.html", user=current_user, campsite=campsite, photo_path=campsite_photo_path, locale=locale, placeholder=placeholderFlag, submitted_by=submitted_by)


# Checks that the request contains a valid photo upload, then saves the file to the CAMPSITE_PHOTO_UPLOAD_PATH path (set in .env). Only jpgs will be saved. Returns a boolean flag for the validity of the upload pipe (true if input validated and in jpg form)
def campsitePhotoUploadSuccessful() -> bool:
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
    file = sub('[^A-Za-z0-9]+', '', file) + ".jpg"

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


# helper functions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@views.errorhandler(413)
def error413(e):
    return render_template("error.html", user=current_user), 413
