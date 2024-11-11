from flask import Blueprint, render_template, request, make_response
from flask_login import  current_user
from datetime import datetime, timedelta

from ..models.models import CampSiteList

from website.controllers.controllers import *

home_bp = Blueprint("home", __name__, url_prefix="/")

@home_bp.route("/")
def homepage():
    try:
        # Get all campsites for the map
        campsite_lats, campsite_lons, campsite_ids, campsite_names = get_all_campsites()
        
        # Initialize variables for user's campsite lists
        user_lists = None
        list_campsites = set()
        selected_list_name = ""
        
        # If user is authenticated, get their campsite lists
        if current_user.is_authenticated:
            user_lists = CampSiteList.query.filter_by(owner_id=current_user.id).all()
            
            # If a list is selected, get its campsites' IDs
            selected_list_id = request.args.get('list_id')
            if selected_list_id:
                selected_list = CampSiteList.query.get(selected_list_id)
                if selected_list and selected_list.owner_id == current_user.id:
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
    
@home_bp.route('/set-welcome-banner-cookie', methods=['POST'])
def set_welcome_banner_cookie():
    response = make_response(jsonify({'status': 'success'}))
    
    # Set cookie to expire in 30 days
    expires = datetime.now() + timedelta(days=30)
    
    # Set the cookie
    response.set_cookie(
        'bannerClosed',
        'true',
        expires=expires,
        secure=True,  # Only send cookie over HTTPS
        httponly=False,  
        samesite='Strict'
    )
    
    return response

@home_bp.route('/set-popup-cookie', methods=['POST'])
def set_popup_cookie():
    response = make_response(jsonify({'status': 'success'}))
    
    # Set cookie to expire in 30 days
    expires = datetime.now() + timedelta(days=30)
    
    # Set the cookie
    response.set_cookie(
        'tipClosed',
        'true',
        expires=expires,
        secure=True,  # Only send cookie over HTTPS
        httponly=False,  
        samesite='Strict'
    )
    
    return response