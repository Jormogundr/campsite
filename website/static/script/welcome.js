document.addEventListener('DOMContentLoaded', function() {
    // Check if banner should be hidden
    const bannerClosed = document.cookie
        .split('; ')
        .find(row => row.startsWith('bannerClosed='));
    
    if (bannerClosed) {
        const banner = document.querySelector('.welcome-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    }

    // Add the animation styles
    const styleSheet = document.createElement("style");
    styleSheet.textContent = `
        @keyframes fadeOut {
            0% { opacity: 1; transform: translateY(0); }
            100% { opacity: 0; transform: translateY(-20px); }
        }
        
        .welcome-banner.closing {
            animation: fadeOut 0.3s ease-out forwards;
        }
    `;
    document.head.appendChild(styleSheet);

    // Function to close banner with animation
    function closeBanner(banner) {
        if (banner) {
            banner.classList.add('closing');
            banner.addEventListener('animationend', function() {
                banner.remove();
            });
        }
    }

    // Function to set the cookie
    async function setBannerCookie() {
        try {
            const response = await fetch('/set-welcome-banner-cookie', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            if (!response.ok) {
                console.error('Failed to set banner cookie');
            }
        } catch (error) {
            console.error('Error setting banner cookie:', error);
        }
    }

    // Regular close button (temporary close)
    const closeButton = document.querySelector('.welcome-close');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            const banner = document.querySelector('.welcome-banner');
            closeBanner(banner);
        });
    }

    // "Do not show again" button (permanent close with cookie)
    const doNotShowButton = document.querySelector('.do-not-show-again');
    if (doNotShowButton) {
        doNotShowButton.addEventListener('click', async function() {
            const banner = document.querySelector('.welcome-banner');
            await setBannerCookie();
            closeBanner(banner);
        });
    }
});