// geolocation callbacks
function successCallback(position) {
    return position
  };
  
function showError(error) {
    switch(error.code) {
      case error.PERMISSION_DENIED:
        x.innerHTML = "User denied the request for Geolocation."
        break;
      case error.POSITION_UNAVAILABLE:
        x.innerHTML = "Location information is unavailable."
        break;
      case error.TIMEOUT:
        x.innerHTML = "The request to get user location timed out."
        break;
      case error.UNKNOWN_ERROR:
        x.innerHTML = "An unknown error occurred."
        break;
    }
    return error
  }
  
  function drawMap(lat, lon) {
    var map = L.map('map').setView([lat, lon], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
  }
  

// on successful document load, draw map
document.addEventListener("DOMContentLoaded", () => {
    navigator.geolocation.getCurrentPosition((position) => {
        drawMap(position.coords.latitude, position.coords.longitude);
      });
});