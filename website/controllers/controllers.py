from flask_login import login_required

from werkzeug.security import generate_password_hash
from ..models.models import *
from .. import db

def fill_tables(emails, passwords, user_names, activities, locations, ages, names, coords, potableWaters, electricals, descriptions, backCountrys, permitsRequired, campingStyles, firePits, submissions, ratings, numRatings):
    # Add users
    for email, password, user_name, activity, location, age in zip(emails, passwords, user_names, activities, locations, ages):
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

    # Add campsites
    for name, coord, hasPotable, hasElectrical, description, isBackcountry, isPermitReq, campingStyle, firePit, submittedBy, rating, numRating in zip(names, coords, potableWaters, electricals, descriptions, backCountrys, permitsRequired, campingStyles, firePits, submissions, ratings, numRatings):
        latitude, longitude = coord
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

    return "Table data generated"