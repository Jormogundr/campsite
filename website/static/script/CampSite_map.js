// CampSiteMapSingleton.js
class CampSiteMapSingleton {
    constructor() {
        if (CampSiteMapSingleton.instance) {
            return CampSiteMapSingleton.instance;
        }
        
        this.DEFAULT_LAT = 39.0940394841749;
        this.DEFAULT_LON = -102.02316635857781;
        
        // Initialize map instance
        this.map = null;
        this.markers = [];
        this.initialized = false;
        
        // Create icons
        this.defaultIcon = L.icon({
            iconUrl: "/static/images/camps_icon.png",
            iconSize: [36, 36],
        });
        
        this.highlightedIcon = L.icon({
            iconUrl: "/static/images/camps_icon_selected.png",
            iconSize: [36, 36],
        });
        
        // Store instance
        CampSiteMapSingleton.instance = this;
    }

    initialize(callback = null) {
        if (this.initialized) return;
        
        this.map = L.map("map").setView([this.DEFAULT_LAT, this.DEFAULT_LON], 8);
        
        // Set up click handler
        this.map.on("click", (e) => {
            const coord = e.latlng;
            const lat = coord.lat.toFixed(6);
            const lng = coord.lng.toFixed(6);
            const link = `/add-campsite?lat=${lat}&lon=${lng}`;
            
            L.popup()
                .setLatLng([lat, lng])
                .setContent(
                    `<b>Lat:</b> ${lat} <br> <b>Lon:</b> ${lng} 
                     <a href=${link}><h6 align="center" style="padding-top:0.25em;text-align: center;">
                     Add CampSite</h6></a>`
                )
                .openOn(this.map);
        });

        // Get user location and draw map
        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.drawMap(position.coords.latitude, position.coords.longitude);
                if (callback) callback();
            },
            (error) => {
                this.showError(error);
                if (callback) callback();
            }
        );

        this.initialized = true;
    }

    drawMap(lat, lon) {
        this.map.setView([lat, lon], 6);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright" style="text-align: center">OpenStreetMap</a> contributors',
        }).addTo(this.map);

        // show popup with hint for user
        L.popup()
            .setLatLng([lat, lon])
            .setContent(
                '<h4 align="center"><b>Tip</b></h4> <h5 align="center">Click anywhere on the map to get the latitude and longitude</h5>'
            )
            .openOn(this.map);
    }

    // Populate the map with existing campsites.
    addMarkers(lats, lons, names, ids, inSelectedList) {
        // Clear existing markers if any
        this.markers.forEach(marker => {
            if (marker) {
                marker.remove();
            }
        });
        this.markers = [];

        for (let i = 0; i < lats.length; i++) {
            // Choose icon based on whether campsite is in selected list
            const icon = inSelectedList[i] ? this.highlightedIcon : this.defaultIcon;
            
            const marker = L.marker([lats[i], lons[i]], { icon: icon }).addTo(this.map);
            const link = "/campsites/" + ids[i];
            
            // Add a class to the marker element for potential CSS styling
            marker.getElement().classList.add(inSelectedList[i] ? 'highlighted-marker' : 'default-marker');
            
            let popupContent = `
                <p align="center" style="font-weight:bold;font-size:x-large;padding-bottom:0;margin-bottom:0">
                    ${names[i]}
                </p>  
                <br> 
                <b>Latitude:</b> ${lats[i]} 
                <br> 
                <b>Longitude:</b> ${lons[i]} 
                <br> 
                <a href="${link}">
                    <h6 align="center" style="padding-top:0.25em">View Details</h6>
                </a>`;

            // Add indicator if campsite is in selected list
            if (inSelectedList[i]) {
                popupContent = `
                    <div class="in-list-badge">In Selected List</div>
                    ${popupContent}`;
            }
            
            marker.bindPopup(popupContent);
            this.markers.push(marker);
        }
    }

    showError(error) {
        // draw map with default coordinates
        this.drawMap(this.DEFAULT_LAT, this.DEFAULT_LON);

        const x = document.getElementById("map-error-flash");
        switch (error.code) {
            case error.PERMISSION_DENIED:
                console.log("User denied the request for Geolocation.");
                x.innerHTML = "For the best experience, please allow location permissions.";
                break;
            case error.POSITION_UNAVAILABLE:
            case error.TIMEOUT:
            case error.UNKNOWN_ERROR:
                console.log("Location error:", error.message);
                x.innerHTML = "CampSite could not locate you.";
                break;
        }

        x.style.display = "block";
        return error;
    }
}

// Create and export singleton instance
const CampSiteMapSingletonSingleton = new CampSiteMapSingleton();