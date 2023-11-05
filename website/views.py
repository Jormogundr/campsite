from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import CampSite
from . import db
import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST': 

        # TODO: Visibility should be set on list creation, not campsite creation
        isPrivate = True if request.form.get('visibility') == 'on' else False
        hasPotable = True if request.form.get('potable') == 'on' else False
        hasElectrical = True if request.form.get('electrical') == 'on' else False

        # validate user campsite submission
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
        
        if latitude > 90 or latitude < -90:
            flash('Invalid latitude', category='error')
        if longitude > 180 or longitude < -180:
            flash('Invalid longitude', category='error')
        else:
            # save entries to model
            new_campsite = CampSite(latitude=latitude, longitude=longitude, potableWater=hasPotable, electrical=hasElectrical)
            db.session.add(new_campsite)
            db.session.commit()
            flash('Campsite added!', category='success')
            return redirect(url_for('views.home'))
            
    return render_template("home.html", user=current_user)


