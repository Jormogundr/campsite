const deletePhoto = async (photoId, event) => {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this photo?')) return;
    
    try {
        const response = await fetch(`/api/campsite/photo/${photoId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            location.reload();
        } else {
            const data = await response.json();
            alert(data.message || 'Error deleting photo');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting photo');
    }
};

const setPrimaryPhoto = async (photoId, event) => {
    event.stopPropagation();
    
    try {
        const response = await fetch(`/api/campsite/photo/${photoId}/primary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            location.reload();
        } else {
            const data = await response.json();
            alert(data.message || 'Error setting primary photo');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error setting primary photo');
    }
};

const updateMainImage = (src, thumbnail) => {
    document.getElementById('gallery-main-image').src = src;
    document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
    thumbnail.classList.add('active');
};

const showPhotoUploadModal = () => {
    document.getElementById('photoUploadModal').style.display = 'flex';
};

const hidePhotoUploadModal = () => {
    document.getElementById('photoUploadModal').style.display = 'none';
};

const previewImage = (input) => {
    const container = input.parentElement;
    const preview = container.querySelector('img');
    const placeholder = container.querySelector('.upload-placeholder');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
        }
        reader.readAsDataURL(input.files[0]);
        
        // Add new upload slot if this is the last one
        const grid = document.getElementById('photoUploadGrid');
        const items = grid.querySelectorAll('.photo-upload-item');
        if (input.files[0] && items.length < 5 && 
            Array.from(items).pop().querySelector('input').files.length > 0) {
            addPhotoUploadSlot();
        }
    }
};

const addPhotoUploadSlot = () => {
    const grid = document.getElementById('photoUploadGrid');
    const newIndex = grid.children.length + 1;
    const newItem = document.createElement('div');
    newItem.className = 'photo-upload-item';
    newItem.innerHTML = `
        <input type="file" name="photo_${newIndex}" accept="image/*" onchange="previewImage(this)">
        <div class="preview-container">
            <img src="#" alt="Preview" style="display: none;">
            <div class="upload-placeholder">
                <i class="fas fa-plus"></i>
                <span>Add Photo</span>
            </div>
        </div>
    `;
    grid.appendChild(newItem);
};

// Close modal when clicking outside
window.onclick = (event) => {
    const modal = document.getElementById('photoUploadModal');
    if (event.target === modal) {
        hidePhotoUploadModal();
    }
};