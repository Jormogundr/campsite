// Profile page interactions
document.addEventListener('DOMContentLoaded', function() {
    // Photo upload handling
    const photoInput = document.getElementById('photo-input');
    const photoContainer = document.querySelector('.profile-img-container');
    const profileImg = document.getElementById('profile-img');

    if (photoContainer) {
        photoContainer.addEventListener('click', () => photoInput.click());
    }

    if (photoInput) {
        photoInput.addEventListener('change', async function(e) {
            if (this.files && this.files[0]) {
                const formData = new FormData();
                formData.append('photo', this.files[0]);

                try {
                    const response = await fetch(window.location.href, {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        // Update the image preview
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            profileImg.src = e.target.result;
                        };
                        reader.readAsDataURL(this.files[0]);
                    } else {
                        alert('Failed to upload photo');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('Failed to upload photo');
                }
            }
        });
    }

    // Handle editable fields
    const editableFields = document.querySelectorAll('[contenteditable="true"]');
    
    editableFields.forEach(field => {
        let originalValue;
        
        field.addEventListener('focus', function() {
            originalValue = this.textContent;
        });

        field.addEventListener('blur', async function() {
            if (this.textContent !== originalValue) {
                const fieldName = this.dataset.field;
                const value = this.textContent.trim();

                try {
                    const response = await fetch(window.location.href, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({
                            'field': fieldName,
                            'value': value
                        })
                    });

                    if (!response.ok) {
                        this.textContent = originalValue;
                        alert('Failed to update field');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    this.textContent = originalValue;
                    alert('Failed to update field');
                }
            }
        });

        // Handle Enter key to save changes
        field.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    });
});