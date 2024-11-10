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

    window.openShareModal = function() {
        document.getElementById('shareModal').style.display = 'block';
    }

    window.closeShareModal = function() {
        document.getElementById('shareModal').style.display = 'none';
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

    // Collab function
    window.collabList = async function() {
    const emailInput = document.getElementById('collabList');
    const newEmail = emailInput.value;
    
    try {
        const response = await fetch(`/campsite-lists/${listId}/collaborate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: newEmail })
        });
        
        // Always parse the response data, regardless of status
        const data = await response.json();
        
        if (response.ok) {
            showNotification('List shared successfully!', 'success');
            window.location.reload();
        } else {
            // Use the error message from the server if available
            const errorMessage = data.details || data.error || 'An error occurred while sharing the list';
            showNotification(errorMessage, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('An unexpected error occurred while sharing the list', 'error');
    }
}

    // Helper function to show notifications
    function showNotification(message, type) {
        // First, create a wrapper if it doesn't exist
        let wrapper = document.getElementById('notification-wrapper');
        if (!wrapper) {
            wrapper = document.createElement('div');
            wrapper.id = 'notification-wrapper';
            document.body.appendChild(wrapper);
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Create the content
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add to wrapper
        wrapper.appendChild(notification);
        
        // Log for debugging
        console.log('Notification created:', notification);
        console.log('Notification styles:', window.getComputedStyle(notification));
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Test function - you can call this from the browser console to test
    function testNotification() {
        showNotification('Test notification', 'error');
    }
});