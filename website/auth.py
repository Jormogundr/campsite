from os import getcwd, getenv, path

from . import db

from dotenv import load_dotenv
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, current_user

from website.models.models import UserRole


load_dotenv()

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successfully!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("views.home"))
            else:
                flash("Incorrect password, try again.", category="error")
        else:
            flash("Email does not exist.", category="error")

    return render_template("login.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        location = (
            request.form.get("location")
            if request.form.get("location")
            else "None provided"
        )
        age = request.form.get("age") if request.form.get("age") else "None provided"
        activities = (
            request.form.get("activities")
            if request.form.get("activities")
            else "None provided"
        )

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists.", category="error")
        elif len(email) < 4:
            flash("Email must be greater than 3 characters.", category="error")
        elif len(name) < 2:
            flash("First name must be greater than 1 character.", category="error")
        elif password1 != password2:
            flash("Passwords don't match.", category="error")
        elif len(password1) < 7:
            flash("Password must be at least 7 characters.", category="error")
        elif age and not age.isnumeric():
            flash("Age must be an integer.", category="error")
        elif location and not any([x.isalpha() for x in location]):
            flash("Location must contain alphabet characters.", category="error")
        elif request.files["profile_picture"] and not profilePhotoUpload():
            flash("There was a problem with your file.", category="error")
        else: # valid input
            new_user = User(
                email=email,
                name=name,
                age=age,
                location=location,
                activities=activities,
                role=UserRole.USER_ROLE_REGISTERED_FREE,
                password=generate_password_hash(password1, method="sha256"),
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("Account created!", category="success")

            return redirect(url_for("views.home"))

    return render_template("sign_up.html", user=current_user)


# Checks that the request contains a valid photo upload, then saves the file to the PROFILE_PHOTO_UPLOAD_PATH path (set in .env). Only jpgs will be saved.
def profilePhotoUpload() -> bool:
    # retrieve file from request
    photo = request.files["profile_picture"]

    validity = False

    # check user upload
    if not photo:
        flash("There was a problem with the file.", category="error")
        return validity

    if photo.filename == "":
        flash("No file selected.", category="error")
        return validity

    if not allowed_file(photo.filename):
        flash("Allowed file types are" + ALLOWED_EXTENSIONS, category="error")
        return validity

    # name file based on databaseuser id (unique)
    filename = secure_filename(str(User.query.count() + 1) + ".jpg")
    filepath = path.join(getcwd(), PROFILE_PHOTO_UPLOAD_PATH, filename)

    validity = True

    # handle png uploads: convert to jpg then save
    if photo.filename.split(".")[-1] != ".jpg":
        from PIL import Image

        # pillow has its own save function, so return after saving
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
