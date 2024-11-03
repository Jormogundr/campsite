import { MarkerLoader } from './marker_loader.js';

export class MarkerProxy {
    constructor(icons) {
        this.markerLoader = new MarkerLoader(icons);
        this.cache = new Map(); // Map campsite id -> marker
        this.visibleMarkers = new Set(); // currently visible marker ids
        this.markerData = new Map(); // Map campsite id -> marker data
    }

    setMarkerData(lats, lons, names, ids, inSelectedList) {
        this.markerData.clear();
        for (let i = 0; i < ids.length; i++) {
            this.markerData.set(ids[i], {
                id: ids[i],
                lat: lats[i],
                lon: lons[i],
                name: names[i],
                inSelectedList: inSelectedList[i]
            });
        }
    }

    updateVisibleMarkers(bounds, map) {
        // Track which markers should be visible and which should be removed
        const markersToShow = new Set();
        const markersToRemove = new Set(this.visibleMarkers);

        // Find markers within current bounds
        for (const [id, data] of this.markerData.entries()) {
            if (bounds.contains([data.lat, data.lon])) {
                markersToShow.add(id);
                markersToRemove.delete(id);
            }
        }

        // Remove out-of-bounds markers from map
        for (const id of markersToRemove) {
            const marker = this.cache.get(id);
            if (marker) {
                marker.remove();
                this.visibleMarkers.delete(id);
            }
        }

        // Add new in-bounds markers to map
        for (const id of markersToShow) {
            if (!this.visibleMarkers.has(id)) {
                const data = this.markerData.get(id);
                let marker = this.cache.get(id);
                
                // Create marker if not cached
                if (!marker) {
                    marker = this.markerLoader.createMarker(data);
                    this.cache.set(id, marker);
                }
                
                marker.addTo(map);
                this.visibleMarkers.add(id);
            }
        }
    }

    // Method to update a single marker's selected status
    updateMarkerStatus(id, inSelectedList) {
    const data = this.markerData.get(id);
    if (data) {
        data.inSelectedList = inSelectedList;
        const marker = this.cache.get(id);
        if (marker) {
            // Update icon
            const icon = inSelectedList ? this.markerLoader.highlightedIcon : this.markerLoader.defaultIcon;
            marker.setIcon(icon);
            
            // Update class - check if element exists first
            const element = marker.getElement();
            if (element) {
                element.classList.toggle('highlighted-marker', inSelectedList);
                element.classList.toggle('default-marker', !inSelectedList);
            }
            
            // Update popup
            const newMarker = this.markerLoader.createMarker(data);
            marker.setPopupContent(newMarker.getPopup().getContent());
        }
    }
}

    clearCache() {
        // Remove all markers from map
        for (const marker of this.cache.values()) {
            marker.remove();
        }
        this.cache.clear();
        this.visibleMarkers.clear();
    }
}
