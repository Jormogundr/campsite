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

function addMarkers(lats, lons, names, ids) {
  for (let i = 0; i < lats.length; i++) {
    let lat = lats[i];
    let lon = lons[i];
    let name = names[i];
    let id = ids[i];
    // build clickable link string to redirect users to site details
    let link = "/campsites/" + id;

    const campIcon = L.icon({
      iconUrl: "/static/images/camps_icon.png",
      iconSize: [36, 36],
    });
    var marker = L.marker([lat, lon], { icon: campIcon }).addTo(campsite_map);
    marker.bindPopup(
      `<p align="center" style="font-weight:bold;font-size:x-large;padding-bottom:0;margin-bottom:0">${name}</p>  <br> <b>Latitude:</b> ${lat} <br> <b>Longitude:</b> ${lon} <br> <a href="${link}"><h6 align="center" style="padding-top:0.25em">View Details</h6></a>`
    );
  }
}

function drawMap(lat, lon) {
  campsite_map.setView([lat, lon], 6);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright" style="text-align: center">OpenStreetMap</a> contributors',
  }).addTo(campsite_map);

  // show popup with hint for user
  var popup = L.popup()
    .setLatLng([lat, lon])
    .setContent(
      '<h4 align="center"><b>Tip</b></h4> <h5 align="center">Click anywhere on the map to get the latitude and longitude</h5>'
    )
    .openOn(campsite_map);
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

  // listener for on click event - display the clicked lat/lon
  campsite_map.on("click", function (e) {
    var coord = e.latlng;
    var lat = coord.lat.toFixed(6);
    var lng = coord.lng.toFixed(6);
    let link = "/add-campsite" + `?lat=${lat}&lon=${lng}`;
    var popup = L.popup()
      .setLatLng([lat, lng])
      .setContent(`<b>Lat:</b> ${lat} <br> <b>Lon:</b> ${lng} <a href=${link}><h6 align="center" style="padding-top:0.25em;text-align: center;">Add CampSite</h6></a>`)
      .openOn(campsite_map);
  });
});
