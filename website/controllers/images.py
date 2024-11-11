from os import path, getcwd, path, remove
from re import sub
from PIL import Image
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import request, flash

from website.models.models import db, CampsitePhoto
from website.config import Config
class PhotoManager:
    def __init__(self, campsite_upload_path, user_upload_path, allowed_extensions={'png', 'jpg', 'jpeg', 'gif'}):
        self.campsite_upload_path = campsite_upload_path
        self.user_upload_path = user_upload_path
        self.allowed_extensions = allowed_extensions
        
    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def process_photo(self, file, filename):
        """Process and save a photo, returning the filename if successful"""
        if not file or file.filename == '':
            raise ValueError("No file selected")
            
        if not self.allowed_file(file.filename):
            raise ValueError(f"Allowed file types are: {', '.join(self.allowed_extensions)}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = secure_filename(f"{sub('[^A-Za-z0-9]+', '', filename)}_{timestamp}")
        filename = f"{base_name}.jpg"
        filepath = path.join(self.campsite_upload_path, filename)
        
        # Convert to JPG and save
        image = Image.open(file)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Resize if too large while maintaining aspect ratio
        max_size = (1920, 1080)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        image.save(filepath, 'JPEG', quality=85)
        return filename
    
    def delete_photo(self, filename):
        """Delete a photo file"""
        filepath = path.join(self.campsite_upload_path, filename)
        if path.exists(filepath):
            remove(filepath)

photo_manager = PhotoManager(Config.CAMPSITE_PHOTO_UPLOAD_PATH, Config.PROFILE_PHOTO_UPLOAD_PATH)

def handle_campsite_photos(campsite, files, existing_photos=None):
    """Handle multiple photo uploads and updates for a campsite"""
    photos_to_add = []
    
    try:
        # Handle new photo uploads
        for key in files.keys():
            if key.startswith('photo_'):
                file = files[key]
                if file and file.filename:
                    filename = photo_manager.process_photo(file, campsite.name)
                    is_primary = len(photos_to_add) == 0 and not existing_photos
                    
                    photo = CampsitePhoto(
                        campsite_id=campsite.id,
                        filename=filename,
                        is_primary=is_primary
                    )
                    photos_to_add.append(photo)
        
        # Add new photos to database
        if photos_to_add:
            db.session.add_all(photos_to_add)
            db.session.commit()
            
        return True
        
    except Exception as e:
        db.session.rollback()
        # Clean up any saved files if database operation failed
        for photo in photos_to_add:
            photo_manager.delete_photo(photo.filename)
        raise e

def delete_campsite_photo(photo_id):
    """Delete a campsite photo"""
    photo = CampsitePhoto.query.get_or_404(photo_id)
    
    if photo.is_primary:
        # If deleting primary photo, make the next oldest photo primary
        next_photo = CampsitePhoto.query.filter(
            CampsitePhoto.campsite_id == photo.campsite_id,
            CampsitePhoto.id != photo.id
        ).order_by(CampsitePhoto.upload_date.asc()).first()
        
        if next_photo:
            next_photo.is_primary = True
    
    filename = photo.filename
    db.session.delete(photo)
    db.session.commit()
    
    photo_manager.delete_photo(filename)

def handle_profile_photos(user, file, existing_photos=None):
    """Handle single photo uploads and updates for user"""
    # TODO: Implement
    # photo_to_add = None

    # if file and file.filename:
    #     filename = photo_manager.process_photo(file, user.id)

    return
    
def campsitePhotoUploadSuccessful():
    # Retrieve file from request
    photo = request.files["photo"]

    # Check user upload
    validity = False
    if not photo:
        return validity

    if photo.filename == "":
        flash("No file selected.", category="error")
        return validity

    if not photo_manager.allowed_file(photo.filename):
        flash("Allowed file types are" + photo_manager.allowed_extensions, category="error")
        return validity

    # Name file after the submitted campsite name
    file = request.form.get("name")

    # Strip special chars from file
    file = sub("[^A-Za-z0-9]+", "", file) + ".jpg"

    filename = secure_filename(file)
    filepath = path.join(getcwd(), photo_manager.campsite_upload_path, filename)

    # Check if file already exists on server
    if path.isfile(filepath):
        flash(
            "Your uploaded file already exists on the server (is your campsite entry a duplicate?)",
            category="error",
        )
        return validity

    validity = True

    # Handle png uploads: convert to jpg then save
    if photo.filename.split(".")[-1] != ".jpg":
        from PIL import Image

        im = Image.open(photo)
        rgb_im = im.convert("RGB")
        rgb_im.save(filepath)
        return validity

    # Save the file
    photo.save(filepath)
    return validity