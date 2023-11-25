// default lat lon to use when we don't have location data
// currently over center of USA
const default_lat = 39.0940394841749;
const default_lon = -102.02316635857781;
var campsite_map = L.map("map-zoomed");

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

function addMarker(name, lat, lon) {
  var marker = L.marker([lat, lon]).addTo(campsite_map);
  marker.bindPopup(
    `<b>Name:</b> ${name} <br> <b>Latitude:</b> ${lat} <br> <b>Longitude:</b> ${lon}`
  );
  campsite_map.setView([lat, lon], 15);
}

function drawMap(lat, lon) {
  L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
    attribution:
      'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
  }).addTo(campsite_map);
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
