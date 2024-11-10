from os import path, getcwd, getenv

from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from .. import db
from ..models.models import User, CampSite

from website.controllers.controllers import *
from website.extensions import socketio
from website.controllers.notifications import collaboration_notifier
from website.views.views import views


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