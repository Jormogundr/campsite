export class MarkerLoader {
    constructor(icons) {
        this.defaultIcon = icons.defaultIcon;
        this.highlightedIcon = icons.highlightedIcon;
    }

    createMarker(data) {
        const icon = data.inSelectedList ? this.highlightedIcon : this.defaultIcon;
        const marker = L.marker([data.lat, data.lon], { icon });
        
        marker.on('add', function(e) {
            // Now we can safely access the DOM element
            const element = marker.getElement();
            if (element) {
                element.classList.add(
                    data.inSelectedList ? 'highlighted-marker' : 'default-marker'
                );
            }
        });
        
        // Create and bind popup
        const popupContent = `
            <p align="center" style="font-weight:bold;font-size:x-large;padding-bottom:0;margin-bottom:0">
                ${data.name}
            </p>  
            <br> 
            <b>Latitude:</b> ${data.lat} 
            <br> 
            <b>Longitude:</b> ${data.lon} 
            <br> 
            <a href="/campsites/${data.id}">
                <h6 align="center" style="padding-top:0.25em">View Details</h6>
            </a>
            ${data.inSelectedList ? '<div class="in-list-badge">In Selected List</div>' : ''}`;
            
        marker.bindPopup(popupContent);
        return marker;
    }
}