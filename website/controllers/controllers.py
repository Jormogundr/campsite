from flask import flash
from werkzeug.security import generate_password_hash
from ..models.models import CampSite, CampSiteList, User
from .. import db
import reverse_geocode

def get_all_campsites():
    campsites = CampSite.query.all()
    campsite_lats = [getattr(c, "latitude") for c in campsites]
    campsite_lons = [getattr(c, "longitude") for c in campsites]
    campsite_ids = [getattr(c, "id") for c in campsites]
    campsite_names = [getattr(c, "name") for c in campsites]
    return campsite_lats, campsite_lons, campsite_ids, campsite_names

def commit_campsite(name, latitude, longitude, hasPotable, hasElectrical, description, isBackcountry, isPermitReq, campingStyle, firePit, submittedBy, campsiteListId):
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
        campsite_list_id = campsiteListId
    )
    db.session.add(new_campsite)
    db.session.commit()

def get_campsite_details(user_id):
    campsite = CampSite.query.get(user_id)
    if not campsite:
        return None
    
    submitted_by = User.query.filter_by(name=campsite.submittedBy).first()
    coordinates = ((campsite.latitude, campsite.longitude),)
    locale = reverse_geocode.search(coordinates)[0]
    
    return campsite, submitted_by, locale

def get_campsite_list_campsites(user_id):
    campsiteList = CampSiteList.query.get(user_id)
    return campsiteList

def add_campsite_rating(campsite, rating, current_user):
    users_that_have_rated = campsite.ratedUsers or []
    
    if current_user.id in users_that_have_rated:
        return False, "You've already rated this campsite."
    
    users_that_have_rated.append(current_user.id)
    
    avg_rating = float(campsite.rating)
    num_ratings = int(campsite.numRatings)
    
    if num_ratings == 0:
        avg_rating = rating
        num_ratings = 1
    else:
        num_ratings += 1
        expr = (((num_ratings - 1) * avg_rating) + rating) / num_ratings
        avg_rating = float(round(expr, 2))
    
    campsite.rating = round(float(avg_rating), 2)
    campsite.numRatings = int(num_ratings)
    campsite.ratedUsers = users_that_have_rated
    db.session.commit()
    
    return True, "Rating submitted"

def get_user_campsite_lists(user_id):
    campsites = CampSiteList.query.filter_by(user_id=user_id).all()
    return campsites

def get_campsite_list_by_id(id):
    campsites = CampSiteList.query.filter_by(id=id).all()
    return campsites

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