from os import getcwd, getenv, path
from re import findall, sub

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
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
        return render_template(
            "error.html", user=current_user, msg="We were unable to populate the map."
        )


@views.route("/profile/<int:id>", methods=["GET", "POST"])
def profile(id):
    user = User.query.get(id)

    if not user:
        return render_template(
            "error.html", user=current_user, msg="No such user found."
        )

    profile_photo_path = str(user.id) + ".jpg"

    # provide default photo path for profile if user has not uploaded
    placeholderFlag = path.exists(
        "website/static/images/profiles/" + profile_photo_path
    )

    return render_template(
        "profile.html",
        user=user,
        placeholderFlag=placeholderFlag,
        photoPath=profile_photo_path,
    )


@views.route("/add-campsite", methods=["GET", "POST"])
def addsite():
    lat = "Enter Latitude"
    lon = "Enter Longitude"
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
        submittedBy = User.query.filter_by(id=current_user.id).first()

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
                submittedBy=submittedBy.name,
                rating=5.0,
                numRatings=0,
            )
            db.session.add(new_campsite)
            db.session.commit()
            flash("Campsite added.", category="success")

            # handle photo uploads just before returning since this writes to server
            if len(invalid_chars) == 0:
                campsitePhotoUploadSuccessful()

            return redirect(url_for("views.addsite"))
        except:  # TODO: we should catch specific exceptions https://docs.sqlalchemy.org/en/20/errors.html
            flash(
                "An error occurred when commiting this form to a database entry.",
                category="error",
            )

    # check if client is sending us lat/lon to autofill some form fields
    if request.method == "GET":
        # define vars for form field nested text
        lat = request.args.get("lat") if request.args.get("lat") else ""
        lon = request.args.get("lon") if request.args.get("lon") else ""
        if lat and lon:
            return render_template("add_site.html", user=current_user, lat=lat, lon=lon)

    return render_template("add_site.html", user=current_user, lat=lat, lon=lon)


@views.route("/campsites/<int:id>", methods=["GET", "POST"])
def show_campsite(id):
    # define vars passed to template 
    campsite = CampSite.query.get(id)
    submitted_by = User.query.filter_by(name=campsite.submittedBy).first()

    # handle routing for campsites that don't exist
    if not campsite:
        return (
            render_template(
                "error.html", user=current_user, msg="The campsite does not exist."
            ),
            404,
        )

    # use same method used to save file in getting file
    campsite_photo_path = sub("[^A-Za-z0-9]+", "", campsite.name) + ".jpg"

    # use reverse geocoding to get location information based on lat/lon
    coordinates = ((campsite.latitude, campsite.longitude),)
    locale = reverse_geocode.search(coordinates)[0]

    # provide default photo path for campsite if user has not uploaded
    placeholderFlag = path.exists(
        "website/static/images/campsites/" + campsite_photo_path
    )

    # handle campsite ratings
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash(
                "Only registered users can submit a campsite rating", category="error"
            )
            return render_template(
                "campsite.html",
                user=current_user,
                campsite=campsite,
                photo_path=campsite_photo_path,
                locale=locale,
                placeholder=placeholderFlag,
                submitted_by=submitted_by
            )

        rating = float(request.form.get("rating"))

        # validation
        if not rating:
            flash("Error getting rating.", category="error")
            return render_template(
                "campsite.html",
                user=current_user,
                campsite=campsite,
                photo_path=campsite_photo_path,
                locale=locale,
                placeholder=placeholderFlag,
                submitted_by=submitted_by
            )

        # check if user has already rated this site
        users_that_have_rated = campsite.ratedUsers

        # if user rated list is initialized
        if users_that_have_rated:
            # check if user has already rated
            if current_user.id in users_that_have_rated:
                flash("You've already rated this campsite.", category="error")
                return render_template(
                    "campsite.html",
                    user=current_user,
                    campsite=campsite,
                    photo_path=campsite_photo_path,
                    locale=locale,
                    placeholder=placeholderFlag,
                    submitted_by=submitted_by
                )
        else:
            users_that_have_rated = [current_user.id]

        # calculate new campsite average rating
        avg_rating = float(campsite.rating)
        num_ratings = int(campsite.numRatings)

        # no rating yet
        if num_ratings is None or num_ratings == 0:
            avg_rating = rating
            num_ratings = 1
        # average the rating
        else:
            num_ratings += 1
            expr = (((num_ratings - 1) * avg_rating) + rating)/num_ratings
            avg_rating = float(round(expr,2))

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
    
    
    return render_template(
        "campsite.html",
        user=current_user,
        campsite=campsite,
        photo_path=campsite_photo_path,
        locale=locale,
        placeholder=placeholderFlag,
        submitted_by=submitted_by,
    )


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


# helper functions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@views.errorhandler(413)
def error413(e):
    return render_template("error.html", user=current_user), 413


# for testing and filling tables for demo purposes
@views.route("/filltables", methods=["GET"])
def fillTables(FILL_TABLES=False):
    FILL_TABLES = getenv("FILL_TABLES")

    if not bool(FILL_TABLES):
        return (
            render_template(
                "error.html", user=current_user, msg="Testing flag not true."
            ),
            404,
        )

    # users
    emails = [
        "aygulkamalova@maryland-college.cf",
        "marshalleonid@petitemademoiselle.it",
        "vanyapo@mamas-spice.com",
        "faraonsanek@maryland-college.cf",
        "ysinovskii@gmailos.com",
        "pfann@gmailos.com",
        "gkapitonova@hearourvoicetee.com",
        "superstu@viralchoose.com",
    ]
    passwords = [
        "test123",
        "password123",
        "cleverpassword",
        "nobodyWillGuessIt",
        "donttryit",
        "IhaveTheHighground",
        "secretkey123",
        "bobandalice490",
    ]
    user_names = [
        "Bob",
        "Marshall",
        "Dolly",
        "Alice",
        "Justin",
        "Timmy",
        "George",
        "Roger",
    ]
    activities = [
        "Adventure biking, rock climbing, hiking",
        "Backpacking, remote backcountry camping, cross country skiing",
        "Ice fishing, hunting, trapping, camping",
        "Offroading, quads, hunting, trailrunning",
        "Offroading, hiking, glamping",
        "Stargazing, photography, camping",
        "Trailrunning, rock climbing, mountaineering",
        "Hiking",
    ]
    locations = [
        "August, MT, USA",
        "Munising, MI, USA",
        "Winnipeg, Manitoba, Canada",
        "Pinedale, WY, USA",
        "Boulder, CO, USA",
        "Duncan, Scotland, UK",
        "Monroe, MI, USA",
        "Grand Haven, MI, USA",
    ]
    ages = [19, 29, 33, 49, 18, 21, 66, 25]

    # campsites
    names = [
        "Preservation Point",
        "Washington Creek",
        "Lane Cover",
        "Crescent Beach",
        "Teton Crest",
        "South Fork Sun",
        "Dolly Sods Junction",
        "Swift Creek Camp",
        "Ludington Cedar Grove",
        "Sevenmile",
        "Sterling State Park",
    ]
    coords = [
        (46.556705161540734, -86.69258618820088),
        (47.91698944455214, -89.1530720314743),
        (48.144168879677274, -88.55764850267133),
        (43.65948538181766, -110.89673241961191),
        (47.510580675030546, -112.89408774725564),
        (39.04799459887445, -79.3373273982496),
        (37.801724311230544, -83.57590519995529),
        (44.036926224585116, -86.50518613137923),
        (46.619637105540484, -86.2592106425204),
        (40.28875230929873, -105.81174009688026),
        (41.91109713699435, -83.33585130451023),
    ]
    potableWaters = [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
    ]
    electricals = [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        False,
        False,
    ]
    descriptions = [
        "Very secluded site, located on the sandstone cliffs of Grand Island on Lake Superior. Nearest water access is about a 0.2 mile hike to the west (you cannot reach Lake Superior fromt he site).",
        "A nice spot on the river, just a short walk from the Windigo settlement. Very high chance to see some moose in the river.",
        "Secluded spot on the northern shore of Isle Royale. Amazing spot to catch the sun set over the bay. You'll surely hear some loons once the sun goes down! This is a shared site.",
        "Nice sandy beach with tree cover right next to Lake Michigan. Great spot for a swim!",
        "A spot on top of the world! One of the best sites I've ever spent the night. An absolutley stunning view of the Teton peaks and down into Death Canyone valley.",
        "Lovely spot on the South Fork Sun River. Bring your fishing pole! Just a short walk in from the parking lot, yet feels very secluded as it is off the main trail by a fair bit.The Kenck cabin overlooks the site and is worth a visit.",
        "A site on the hill overlooking the junction of three trails, right next to the Red Creek (there is a stream just to the south that is a closer walk for water). An amazing spot for some star gazing. Don't mind the noises around your tent at night, it's just the deer being nosey.",
        "Just a few miles from the trailhead, a good spot for some comfort camping. The river is wide and deep at spots, with some good pools for swimming. There are several good spots to stay along the river. Only downside is that there is usually quite a lot of people.",
        "Wonderful campground. It's large, but dispersed over an area so that it doesn't feel so busy. Can still be quite crowded in the summer months, but during the fall it's quiet. Good spot to bring your kayak as Lake Hamlin is nearby. The best hike in the lower peninsula is here as well (Lost Lake Trail).",
        "Right next to Lake Superior and not too busy usually. Surrounded by old growth forests for miles around!",
        "Not much to do, beach and water is dirty, and the trails in the area are poorly maintained and right next to a huge coal burning plant! Not to mention there's a lot of people, and the site space is just a big parking lot.",
    ]
    backCountrys = [True, True, True, True, True, True, True, True, False, False, False]
    permitsRequired = [
        False,
        True,
        True,
        False,
        True,
        False,
        False,
        True,
        True,
        True,
        True,
    ]
    campingStyles = [
        "tent",
        "lean-to",
        "bivy",
        "hammock",
        "tent",
        "bushcraft",
        "tent",
        "tent",
        "RV",
        "fifth-wheel",
        "fifth-wheel",
    ]
    firePits = [True, True, False, False, False, True, False, False, True, True, True]
    submissions = [
        "Bob",
        "Marshall",
        "Dolly",
        "Alice",
        "Justin",
        "Timmy",
        "George",
        "Roger",
        "Roger",
        "Dolly",
        "Marshall"
    ]
    ratings = [4.56, 4.21, 4.77, 3.99, 4.71, 4.51, 4.41, 4.19, 4.91, 4.50, 2.91]
    numRatings = [17, 8, 21, 4, 81, 36, 17, 22, 93, 9, 47]
    lats = []
    lons = []
    for coord in coords:
        lat, lon = coord[0], coord[1]
        lats.append(lat)
        lons.append(lon)

    # print("emails", len(emails))
    # print("passwords", len(passwords))
    # print("ages", len(ages))
    # print("activities", len(activities))
    # print("locations", len(locations))
    # print("user_names", len(user_names))

    assert (
        len(emails)
        == len(passwords)
        == len(ages)
        == len(activities)
        == len(locations)
        == len(user_names)
    )

    num_users = len(emails)
    for i in range(0, num_users):
        email = emails[i]
        password = passwords[i]
        age = ages[i]
        activity = activities[i]
        location = locations[i]
        user_name = user_names[i]

        new_user = User(
            email=email,
            name=user_name,
            age=age,
            location=location,
            activities=activity,
            password=generate_password_hash(password, method="sha256"),
        )

        db.session.add(new_user)
        db.session.commit()

    # print("names", len(names))
    # print("coords", len(coords))
    # print("potableWaters", len(potableWaters))
    # print("descriptions", len(descriptions))
    # print("backCountrys", len(backCountrys))
    # print("permitsRequired", len(permitsRequired))
    # print("campingStyles", len(campingStyles))
    # print("firePits", len(firePits))
    # print("submissions", len(submissions))
    # print("ratings", len(ratings))
    # print("numRatings", len(numRatings))
    # print("lats", len(lats))
    # print("lons", len(lons))

    assert (
        len(names)
        == len(coords)
        == len(potableWaters)
        == len(descriptions)
        == len(backCountrys)
        == len(permitsRequired)
        == len(campingStyles)
        == len(firePits)
        == len(submissions)
        == len(ratings)
        == len(numRatings)
        == len(lats)
        == len(lons)
    )

    num_sites = len(names)
    for i in range(0, num_sites):
        name = names[i]
        coord = coords[i]
        hasElectrical = electricals[i]
        hasPotable = potableWaters[i]
        description = descriptions[i]
        isBackcountry = backCountrys[i]
        isPermitReq = permitsRequired[i]
        campingStyle = campingStyles[i]
        firePit = firePits[i]
        submittedBy = submissions[i]
        rating = ratings[i]
        numRating = numRatings[i]
        latitude = lats[i]
        longitude = lons[i]

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
            rating=rating,
            numRatings=numRating,
        )
        db.session.add(new_campsite)
        db.session.commit()

    flash("Table data generated", category="success")
    return render_template(
        "error.html", msg="Succesfully filled tables.", user=current_user
    )
