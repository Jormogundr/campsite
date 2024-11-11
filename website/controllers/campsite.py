from ..models.models import *
from .. import db
import reverse_geocode


def get_all_campsites():
    campsites = CampSite.query.all()
    campsite_lats = [getattr(c, "latitude") for c in campsites]
    campsite_lons = [getattr(c, "longitude") for c in campsites]
    campsite_ids = [getattr(c, "id") for c in campsites]
    campsite_names = [getattr(c, "name") for c in campsites]
    return campsite_lats, campsite_lons, campsite_ids, campsite_names

def can_edit_campsite(campsite, user):
    if not user.is_authenticated:
        return False
        
    # If campsite is not in a list, only the original submitter can edit
    if not campsite.campsite_list:
        return user.name == campsite.submittedBy
        
    # Check if user is the list owner
    if campsite.campsite_list.owner_id == user.id:
        return True
        
    # Check if user has WRITE or ADMIN permission on the list
    permission = campsite.campsite_list.get_user_permission(user)
    return permission in [ListPermissionType.PERMISSION_WRITE, ListPermissionType.PERMISSION_ADMIN]

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

def get_user_campsite_lists(owner_id):
    campsites = CampSiteList.query.filter_by(owner_id=owner_id).all()
    return campsites

def get_campsite_list_by_id(id):
    campsites = CampSiteList.query.filter_by(id=id).all()