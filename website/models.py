from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    activities = db.Column(db.String(200))
    location = db.Column(db.String(150))
    age = db.Column(db.Integer)


class CampSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    potableWater = db.Column(db.Boolean)
    electrical = db.Column(db.Boolean)
    description = db.Column(db.String(1000))
    backCountry = db.Column(db.Boolean)
    firePit = db.Column(db.Boolean)
    submittedBy = db.Column(db.Integer, db.ForeignKey(User.name))
    permitRequired = db.Column(db.Boolean)
    campingStyle = db.Column(db.String(150))
    rating = db.Column(
        db.Float
    )  # TODO: add & check constraints on this value at table level
    numRatings = db.Column(db.Integer)
    ratedUsers = db.Column(db.PickleType)
