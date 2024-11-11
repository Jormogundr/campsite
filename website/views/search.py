from flask import Blueprint, render_template, request
from flask_login import  current_user

from .. import db
from ..models.models import User, CampSite

from website.controllers.controllers import *

search_bp = Blueprint("search", __name__, url_prefix="/search/")

@search_bp.route('', methods=['GET', 'POST'])
def search():
    # Get all unique camping styles for the dropdown
    camping_styles = db.session.query(CampSite.campingStyle).distinct().all()
    camping_styles = [style[0] for style in camping_styles if style[0]]
    
    results = []
    
    if request.method == 'POST':
        search_type = request.form.get('searchType', 'campsite')
        name = request.form.get('name', '').strip()
        
        if search_type == 'user':
            # User search
            query = User.query
            
            if name:
                query = query.filter(User.name.ilike(f'%{name}%'))
                
            # Add user-specific filters
            location = request.form.get('location', '').strip()
            activities = request.form.get('activities', '').strip()
            
            if location:
                query = query.filter(User.location.ilike(f'%{location}%'))
            if activities:
                query = query.filter(User.activities.ilike(f'%{activities}%'))
                
        else:
            # Campsite search
            query = CampSite.query
            
            if name:
                query = query.filter(CampSite.name.ilike(f'%{name}%'))
                
            # Add campsite-specific filters
            potable_water = request.form.get('potableWater')
            electrical = request.form.get('electrical')
            fire_pit = request.form.get('firePit')
            back_country = request.form.get('backCountry')
            permit_required = request.form.get('permitRequired')
            camping_style = request.form.get('campingStyle')
            min_rating = request.form.get('minRating')
            
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
    
    return render_template('search.html',
                         results=results,
                         camping_styles=camping_styles,
                         user=current_user)