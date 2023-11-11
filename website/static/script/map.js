// geolocation callbacks
function successCallback(position) {
  return position;
}

function showError(error) {
  // draw map with a default lat/lon defining the origin, currently over central united states
  let default_lat = 39.0940394841749;
  let default_lon = -102.02316635857781;
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
  x.style.visibility='visible';
  return error;
}

function drawMap(lat, lon) {
  var map = L.map("map").setView([lat, lon], 6);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
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
