from enum import Enum
from .. import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class ListVisibilityType(Enum):
    LIST_VISIBILITY_NONE = 0
    LIST_VISIBILITY_PRIVATE = 1
    LIST_VISIBILITY_PROTECTED = 2
    LIST_VISIBILITY_PUBLIC = 3

class UserRole(Enum):
    USER_ROLE_GUEST = 0
    USER_ROLE_REGISTERED_FREE = 1
    USER_ROLE_REGISTERED_FREE_PREMIUM = 2
    USER_ROLE_MODERATOR = 3
    USER_ROLE_ADMIN = 4

class ListPermissionType(Enum):
    PERMISSION_READ = 1
    PERMISSION_WRITE = 2
    PERMISSION_ADMIN = 3

    @property
    def display_name(self):
        return {
            ListPermissionType.PERMISSION_READ: "View",
            ListPermissionType.PERMISSION_WRITE: "Edit",
            ListPermissionType.PERMISSION_ADMIN: "Admin"
        }[self]

# Association table for shared list permissions
list_permissions = db.Table('list_permissions',
    db.Column('list_id', db.Integer, db.ForeignKey('campsite_lists.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('permission_type', db.Enum(ListPermissionType), nullable=False)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    
    # Owner relationship
    owned_campsite_lists = db.relationship("CampSiteList", back_populates="owner")
    
    # Shared lists relationship
    shared_campsite_lists = db.relationship('CampSiteList',
        secondary=list_permissions,
        backref=db.backref('shared_with', lazy='dynamic'),
        lazy='dynamic'
    )
    
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
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    owner = db.relationship("User", back_populates="owned_campsite_lists")
    campsites = db.relationship("CampSite", back_populates="campsite_list")

    visibility = db.Column(db.Enum(ListVisibilityType))
    name = db.Column(db.String(150))

    def add_collaborator(self, user, permission_type):
        """Add a user as a collaborator with specified permissions"""
        stmt = list_permissions.insert().values(
            list_id=self.id,
            user_id=user.id,
            permission_type=permission_type
        )
        db.session.execute(stmt)
        db.session.commit()

    def remove_collaborator(self, user):
        """Remove a user's collaboration permissions"""
        stmt = list_permissions.delete().where(
            db.and_(
                list_permissions.c.list_id == self.id,
                list_permissions.c.user_id == user.id
            )
        )
        db.session.execute(stmt)
        db.session.commit()

    def get_user_permission(self, user):
        """Get a user's permission level for this list"""
        if user.id == self.owner_id:
            return ListPermissionType.PERMISSION_ADMIN
        
        stmt = db.select(list_permissions.c.permission_type).where(
            db.and_(
                list_permissions.c.list_id == self.id,
                list_permissions.c.user_id == user.id
            )
        )
        result = db.session.execute(stmt).scalar()
        return result

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
    rating = db.Column(db.Float)
    numRatings = db.Column(db.Integer)
    ratedUsers = db.Column(db.PickleType)