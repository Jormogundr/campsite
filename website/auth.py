from os import getcwd, getenv, path

from . import db

from dotenv import load_dotenv
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, current_user

from website.models.models import UserRole
from website.config import Config

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
        # Required fields
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        password1 = request.form.get("password1", "")
        password2 = request.form.get("password2", "")

        # Optional fields - use None as default to indicate no value provided
        location = request.form.get("location", "").strip() or None
        age = request.form.get("age", "").strip() or None
        activities = request.form.get("activities", "").strip() or None

        # Validation for required fields
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists.", category="error")
            return render_template("sign_up.html", user=current_user)
        elif len(email) < 4:
            flash("Email must be greater than 3 characters.", category="error")
            return render_template("sign_up.html", user=current_user)
        elif len(name) < 2:
            flash("First name must be greater than 1 character.", category="error")
            return render_template("sign_up.html", user=current_user)
        elif password1 != password2:
            flash("Passwords don't match.", category="error")
            return render_template("sign_up.html", user=current_user)
        elif len(password1) < 7:
            flash("Password must be at least 7 characters.", category="error")
            return render_template("sign_up.html", user=current_user)

        # Validation for optional fields only if they're provided
        if age is not None:
            try:
                age = int(age)
                if age < 1 or age > 120:
                    flash("Please enter a valid age between 1 and 120.", category="error")
                    return render_template("sign_up.html", user=current_user)
            except ValueError:
                flash("Age must be a valid number.", category="error")
                return render_template("sign_up.html", user=current_user)

        if location is not None and not any(c.isalpha() for c in location):
            flash("Location must contain at least one letter.", category="error")
            return render_template("sign_up.html", user=current_user)

        # Handle profile picture upload if provided
        profile_picture_path = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                if not profilePhotoUpload():  # Your existing photo upload function
                    flash("There was a problem uploading your profile picture.", category="error")
                    return render_template("sign_up.html", user=current_user)
                profile_picture_path = file.filename  # Adjust based on your storage logic

        # Create new user
        new_user = User(
            email=email,
            name=name,
            age=age,
            location=location,
            activities=activities,
            photo=profile_picture_path,
            role=UserRole.USER_ROLE_REGISTERED_FREE,
            password=generate_password_hash(password1, method="scrypt"),
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("Account created successfully!", category="success")
            return redirect(url_for("views.home"))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while creating your account. Please try again.", category="error")
            return render_template("sign_up.html", user=current_user)

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
        flash("Allowed file types are" + Config.ALLOWED_EXTENSIONS, category="error")
        return validity

    # name file based on databaseuser id (unique)
    filename = secure_filename(str(User.query.count() + 1) + ".jpg")
    filepath = path.join(getcwd(), Config.PROFILE_PHOTO_UPLOAD_PATH, filename)

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
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
