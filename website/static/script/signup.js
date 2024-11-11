function updateFileName(input) {
    const fileNameDisplay = document.querySelector('.file-name-display');
    const clearButton = document.querySelector('.clear-file');
    
    if (input.files && input.files[0]) {
    const fileName = input.files[0].name;
    fileNameDisplay.textContent = fileName;
    clearButton.classList.add('visible');
    } else {
    fileNameDisplay.textContent = 'No file chosen';
    clearButton.classList.remove('visible');
    }
}

function clearFileInput() {
    const input = document.getElementById('profile_picture');
    input.value = '';
    updateFileName(input);
}