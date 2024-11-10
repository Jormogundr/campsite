import { MarkerProxy } from './marker_proxy.js';
class CampSiteMapSingleton {
    constructor() {
        if (CampSiteMapSingleton.instance) {
            return CampSiteMapSingleton.instance;
        }
        
        this.DEFAULT_LAT = 39.0940394841749;
        this.DEFAULT_LON = -102.02316635857781;
        
        this.map = null;
        this.initialized = false;
        this.hasSeenTip = this.checkPopupCookie();
        
        // Create icons
        this.defaultIcon = L.icon({
            iconUrl: "/static/images/camps_icon.png",
            iconSize: [36, 36],
        });
        
        this.highlightedIcon = L.icon({
            iconUrl: "/static/images/camps_icon_selected.png",
            iconSize: [36, 36],
        });

        // Initialize marker proxy to lazily load campsite markers, and remove when out of bounds
        this.markerProxy = new MarkerProxy({
            defaultIcon: this.defaultIcon,
            highlightedIcon: this.highlightedIcon
        });
        
        CampSiteMapSingleton.instance = this;
    }

    initialize(callback = null) {
        if (this.initialized) return;
        
        this.map = L.map("map").setView([this.DEFAULT_LAT, this.DEFAULT_LON], 8);
        
        // Add OpenStreetMap tile layer
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
        
        // Set up click handler for adding new campsites
        this.map.on("click", (e) => {
            const coord = e.latlng;
            const lat = coord.lat.toFixed(6);
            const lng = coord.lng.toFixed(6);
            const link = `/add-campsite?lat=${lat}&lon=${lng}`;
            
            L.popup()
                .setLatLng([lat, lng])
                .setContent(
                    `<b>Lat:</b> ${lat} <br> <b>Lon:</b> ${lng} 
                     <a href=${link}><h6 align="center">Add CampSite</h6></a>`
                )
                .openOn(this.map);
        });

        // Set up bounds change handler for lazy loading markers
        this.map.on('moveend', () => {
            const bounds = this.map.getBounds();
            this.markerProxy.updateVisibleMarkers(bounds, this.map);
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

    checkPopupCookie() {
        return document.cookie.split(';').some(cookie => 
            cookie.trim().startsWith('tipClosed=true'));
    }

    addMarkers(lats, lons, names, ids, inSelectedList) {
        // Update marker data in proxy
        this.markerProxy.setMarkerData(lats, lons, names, ids, inSelectedList);
        
        // Load initial markers in view
        const bounds = this.map.getBounds();
        this.markerProxy.updateVisibleMarkers(bounds, this.map);
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

    drawMap(lat, lon) {
        this.map.setView([lat, lon], 6);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright" style="text-align: center">OpenStreetMap</a> contributors',
        }).addTo(this.map);

        // show popup with hint for user
        if (!this.hasSeenTip) {
            const self = this;  // Store reference to this
            const popup = L.popup()
                .setLatLng([lat, lon])
                .setContent(`
                    <div class="popup-content">
                        <h4 align="center"><b>Tip</b></h4>
                        <h5 align="center">Click anywhere on the map to get the latitude and longitude</h5>
                        <div align="center">
                            <button id="closeHintBtn" class="close-popup-btn">
                                Don't show again
                            </button>
                        </div>
                    </div>
                `)
                .openOn(this.map);

            // Add event listener after popup is added to DOM
            setTimeout(() => {
                document.getElementById('closeHintBtn').addEventListener('click', () => {
                    self.closeHintPopup();
                });
            }, 0);
        }
    }

    closeHintPopup() {
        // Send request to set cookie
        fetch('/set-popup-cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        this.hasSeenTip = true;
        this.map.closePopup();
    }
}

// Create and export singleton instance
export const campSiteMapSingleton = new CampSiteMapSingleton();