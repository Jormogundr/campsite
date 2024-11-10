document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.remove-collaborator').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to remove this collaborator?')) {
                return;
            }
            
            const listId = this.dataset.listId;
            const userId = this.dataset.userId;
            
            try {
                const response = await fetch(`/remove-collaborator/${listId}/${userId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
                
                if (response.ok) {
                    // Remove the list item from the DOM
                    this.closest('li').remove();
                    
                    // If this was the last collaborator, update the display
                    const ulElement = this.closest('ul');
                    if (ulElement && ulElement.children.length === 0) {
                        const tdElement = ulElement.closest('td');
                        tdElement.innerHTML = '<p>Not shared with anyone</p>';
                        window.location.reload(true);
                    }
                } else {
                    const data = await response.json();
                    alert(data.error || 'Failed to remove collaborator');
                }
            } catch (error) {
                alert('An error occurred while removing the collaborator');
                console.error('Error:', error);
            }
        });
    });
});