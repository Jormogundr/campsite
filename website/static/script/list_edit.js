document.addEventListener('DOMContentLoaded', function() {
    // Get list_id from data attribute
    const listId = document.body.dataset.listId;
    
    // Modal functions
    window.openRenameModal = function() {
        document.getElementById('renameModal').style.display = 'block';
    }

    window.closeRenameModal = function() {
        document.getElementById('renameModal').style.display = 'none';
    }

    window.openDeleteModal = function() {
        document.getElementById('deleteModal').style.display = 'block';
    }

    window.closeDeleteModal = function() {
        document.getElementById('deleteModal').style.display = 'none';
    }

    // Close modals when clicking outside
    window.onclick = function(event) {
        if (event.target.className === 'modal') {
            event.target.style.display = 'none';
        }
    }

    // Rename function
    window.renameList = async function() {
        const newName = document.getElementById('newListName').value;
        try {
            const response = await fetch(`/campsite-lists/${listId}/rename`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newName })
            });

            if (response.ok) {
                window.location.reload();
            } else {
                alert('Failed to rename list');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while renaming the list');
        }
    }

    // Delete function
    window.deleteList = async function() {
        try {
            const response = await fetch(`/campsite-lists/${listId}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                window.location.href = '/view-lists';
            } else {
                alert('Failed to delete list');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while deleting the list');
        }
    }
});