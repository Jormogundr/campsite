// default lat lon to use when we don't have location data
// currently over center of USA
const default_lat = 39.0940394841749;
const default_lon = -102.02316635857781;
var campsite_map = L.map("map").setView([default_lat, default_lon], 8);

// geolocation callbacks
function successCallback(position) {
  return position;
}

function showError(error) {
  // draw map with a default lat/lon
  drawMap(default_lat, default_lon);

  const x = document.getElementById("map-error-flash");
  switch (error.code) {
    case error.PERMISSION_DENIED:
      console.log("User denied the request for Geolocation.");
      x.innerHTML =
        "For the best experience, please allow location permissions.";
      break;
    case error.POSITION_UNAVAILABLE:
      console.log("Location information is unavailable.");
      x.innerHTML = "CampSite could not locate you.";
      break;
    case error.TIMEOUT:
      console.log("The request to get user location timed out.");
      x.innerHTML = "CampSite could not locate you.";
      break;
    case error.UNKNOWN_ERROR:
      console.log("An unknown error occurred.");
      x.innerHTML = "CampSite could not locate you.";
      break;
  }

  // flash message about location error to user
  x.style.display = "block";
  return error;
}

function addMarkers(lats, lons) {
  for (let i = 0; i < lats.length; i++) {
    let lat = lats[i];
    let lon = lons[i];
    var marker = L.marker([lat, lon]).addTo(campsite_map);
    marker.bindPopup(`Latitude: ${lat} <br> Longitude: ${lon} <br>`)
  }
}

function drawMap(lat, lon) {
  campsite_map.setView([lat, lon], 6);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(campsite_map);
}

// Open the new campsite form
function openForm() {
  document.getElementById("new_campsite_form").style.display = "block";
}

// Close the new campsite form
function closeForm() {
  document.getElementById("new_campsite_form").style.display = "none";
}

// on successful document load, draw map

document.addEventListener("DOMContentLoaded", () => {
  // TODO: handle cases where user blocks location in browser
  // first arg for getCurrentPosition is successful callback, second is error callback
  navigator.geolocation.getCurrentPosition(
    (position) => {
      drawMap(position.coords.latitude, position.coords.longitude);
    },
    (error) => {
      showError(error);
    }
  );
});
