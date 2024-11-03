from enum import Enum

from .. import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class ListVisibilityType(Enum):
    LIST_VISIBILITY_NONE = 0
    LIST_VISIBILITY_PRIVATE = 1
    LIST_VISIBILITY_PROTECTED = 2 # not used currently
    LIST_VISIBILITY_PUBLIC = 3

class UserRole(Enum):
    USER_ROLE_GUEST = 0
    USER_ROLE_REGISTERED_FREE = 1
    USER_ROLE_REGISTERED_FREE_PREMIUM = 2 # not used currently
    USER_ROLE_MODERATOR = 3 # not used currently
    USER_ROLE_ADMIN = 4

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, nullable=False)

    # A user can have multiple lists each with their own visibility
    campsite_lists = db.relationship("CampSiteList", back_populates="user")
    role = db.Column(db.Enum(UserRole))

    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(150), unique=True, nullable=False)
    activities = db.Column(db.String(200))
    location = db.Column(db.String(150))
    age = db.Column(db.Integer)

class CampSiteList(db.Model):
    __tablename__ = 'campsite_lists'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship("User", back_populates="campsite_lists")
    campsites = db.relationship("CampSite", back_populates="campsite_list")

    visibility = db.Column(db.Enum(ListVisibilityType))
    name = db.Column(db.String(150))

    # TODO: description? category?

class CampSite(db.Model):
    __tablename__ = 'campsites'

    id = db.Column(db.Integer, primary_key=True)

    campsite_list_id = db.Column(db.Integer, db.ForeignKey('campsite_lists.id'), nullable=True)
    campsite_list = db.relationship("CampSiteList", back_populates="campsites")

    submittedBy = db.Column(db.String(150), db.ForeignKey(User.name))
    name = db.Column(db.String(150))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    potableWater = db.Column(db.Boolean)
    electrical = db.Column(db.Boolean)
    description = db.Column(db.String(1000))
    backCountry = db.Column(db.Boolean)
    firePit = db.Column(db.Boolean)
    permitRequired = db.Column(db.Boolean)
    campingStyle = db.Column(db.String(150))
    rating = db.Column(
        db.Float
    )  # TODO: add & check constraints on this value at table level
    numRatings = db.Column(db.Integer)
    ratedUsers = db.Column(db.PickleType)
