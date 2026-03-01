// slide-nav.js

(function() {
    const trigger = document.getElementById('navTrigger');
    const overlay = document.getElementById('navOverlay');
    const nav     = document.getElementById('slideNav');
    const close   = document.getElementById('navClose');

    // Safety check
    if (!trigger || !nav || !overlay || !close) {
        console.warn('Sliding nav: one or more elements not found');
        return;
    }

    function openNav() {
        nav.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeNav() {
        nav.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    trigger.addEventListener('click', openNav);
    close.addEventListener('click', closeNav);
    overlay.addEventListener('click', closeNav);

    // Close nav when any link inside it is clicked
    nav.addEventListener('click', function(e) {
        if (e.target.closest('a')) {
            closeNav();
        }
    });

    // ESC key support
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && nav.classList.contains('active')) {
            closeNav();
        }
    });

    console.log('Slide navigation initialized');
})();