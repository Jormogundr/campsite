from os import getenv

from flask import  render_template, flash, Blueprint
from flask_login import current_user
from werkzeug.security import generate_password_hash

from faker import Faker
import random

from .. import db
from ..models.models import User, CampSite

fill_table_bp = Blueprint("fill_table", __name__, url_prefix="/filltables")

@fill_table_bp.route("", methods=["GET"])
def fillTables(FILL_TABLES=False):
    FILL_TABLES = getenv("FILL_TABLES")

    if not bool(FILL_TABLES):
        return render_template("error.html", user=current_user, msg="Testing flag not true."), 404

    fake = Faker()
    
    # Create users first
    users = []
    for i in range(20):
        # Create user with hashed password
        user = User(
            email=fake.email(),
            name=fake.user_name(),
            password=generate_password_hash("password123", method='sha256'),
        )
        db.session.add(user)
        users.append(user)
    
    db.session.commit()  # Commit users first to get their IDs
    
    # Camping styles and other options
    camping_styles = ['Tent', 'RV', 'Car', 'Cabin']
    
    # Create campsites
    for i in range(100):
        # Generate realistic US coordinates
        latitude = random.uniform(25.0, 49.0)  # Continental US latitude range
        longitude = random.uniform(-124.0, -66.0)  # Continental US longitude range
        
        # Random submitter from our users
        submitter = random.choice(users)
        
        # Create campsite with varied attributes
        campsite = CampSite(
            name=fake.city() + " " + random.choice(['Campground', 'Camp', 'Wilderness Site', 'Recreation Area']),
            latitude=round(latitude, 6),
            longitude=round(longitude, 6),
            potableWater=random.choice([True, False]),
            electrical=random.choice([True, False]),
            description=fake.paragraph(nb_sentences=4),
            backCountry=random.choice([True, False]),
            permitRequired=random.choice([True, False]),
            campingStyle=random.choice(camping_styles),
            firePit=random.choice([True, False]),
            submittedBy=submitter.name,
            rating=round(random.uniform(3.0, 5.0), 1),  # Generate rating between 3.0 and 5.0
            numRatings=random.randint(0, 50)
        )
        
        # Randomly assign some users who have rated this campsite
        num_raters = random.randint(0, min(campsite.numRatings, len(users)))
        if num_raters > 0:
            campsite.ratedUsers = random.sample([user.id for user in users], num_raters)
        
        db.session.add(campsite)
    
    # Commit all changes
    db.session.commit()
    
    print(f"Created {len(users)} users and 100 campsites")
    flash("Success", category="success")
    return render_template("error.html", msg="Successfully filled tables.", user=current_user)