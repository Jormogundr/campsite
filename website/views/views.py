from os import path, getcwd, getenv
from re import sub, match

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from flask import jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import traceback

from .. import db
from ..models.models import User, CampSite, CampSiteList

from website.controllers.controllers import *
from website.extensions import socketio

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
        list_campsites = set()  # Use a set for efficient lookups
        selected_list_name = ""
        
        # If user is authenticated, get their campsite lists
        if current_user.is_authenticated:
            user_lists = CampSiteList.query.filter_by(user_id=current_user.id).all()
            
            # If a list is selected, get its campsites' IDs
            selected_list_id = request.args.get('list_id')
            if selected_list_id:
                selected_list = CampSiteList.query.get(selected_list_id)
                if selected_list and selected_list.user_id == current_user.id:
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

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Only registered users can submit a campsite rating", category="error")
        else:
            rating = float(request.form.get("rating"))
            if not rating:
                flash("Error getting rating.", category="error")
            else:
                success, message = add_campsite_rating(campsite, rating, current_user)
                flash(message, category="success" if success else "error")

    return render_template(
        "campsite.html",
        user=current_user,
        campsite=campsite,
        photo_path=campsite_photo_path,
        locale=locale,
        placeholder=placeholderFlag,
        submitted_by=submitted_by,
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
    
    return render_template(
        "profile.html",
        user=user,
        placeholderFlag=placeholderFlag,
        photoPath=profile_photo_path,
        is_owner=current_user.is_authenticated and current_user.id == id
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
    
    return render_template(
        "view_lists.html",
        user=current_user,
        campsiteLists=campsiteLists,
    )

@views.route("/campsite-lists/<int:list_id>/rename", methods=["POST"])
@login_required
def rename_campsite_list(list_id):
    data = request.get_json()
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'error': 'No name provided'}), 400
        
    campsite_list = CampSiteList.query.get_or_404(list_id)
    
    # Check if user owns this list
    if campsite_list.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    campsite_list.name = new_name
    db.session.commit()
    
    return jsonify({'success': True})

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

# TODO: I'm thinking it'd be better to click on a little icon in the view-list view to modify the list
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
        
        pattern = r"^[a-zA-Z0-9]+$"

        if not bool(match(pattern, name)):
            flash("Name should include alphanumeric characters only", category="error")
            errors = True
        
        # TODO: Check for duplicate entry

        if not errors:
            # Construct CampSiteList entry
            user = User.query.get(user_id)
            
            from ..models.models import ListVisibilityType

            vis_map = {"private": ListVisibilityType.LIST_VISIBILITY_PRIVATE, "protected": ListVisibilityType.LIST_VISIBILITY_PROTECTED, "public": ListVisibilityType.LIST_VISIBILITY_PUBLIC}
            visibility = vis_map[visibility]

            new_campsite_list = CampSiteList(
                user_id = user_id,
                user = user,
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
    

@views.route("/filltables", methods=["GET"])
def fillTables(FILL_TABLES=False):
    FILL_TABLES = getenv("FILL_TABLES")

    if not bool(FILL_TABLES):
        return render_template("error.html", user=current_user, msg="Testing flag not true."), 404

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
        "trailer",
        "trailer",
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
            password=generate_password_hash(password, method="scrypt"),
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

    message = fill_tables(emails, passwords, user_names, activities, locations, ages, names, coords, potableWaters, electricals, descriptions, backCountrys, permitsRequired, campingStyles, firePits, submissions, ratings, numRatings)
    flash(message, category="success")
    return render_template("error.html", msg="Successfully filled tables.", user=current_user)

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