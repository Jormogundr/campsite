function toggleEditMode() {
    const viewMode = document.getElementById('view-mode');
    const editMode = document.getElementById('edit-mode');
    
    if (viewMode.style.display !== 'none') {
        viewMode.style.display = 'none';
        editMode.style.display = 'block';
    } else {
        viewMode.style.display = 'block';
        editMode.style.display = 'none';
    }
}

async function handleDeletion(event) {
    event.preventDefault();  // Prevent form submission -- just handle deleting

    const campsiteId = event.target.dataset.campsiteId;
    
    if (confirm('Are you sure you want to delete this campsite?')) {
        try {
            const response = await fetch(`/campsites/${campsiteId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ campsiteId: campsiteId })
            });
            
            if (response.ok) {
                alert('Successfully deleted campsite');
                window.location.href = '/'
            } else {
                alert('Failed to delete campsite');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while deleting the campsite');
        }
    }
}