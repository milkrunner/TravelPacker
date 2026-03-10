// Main JavaScript for NikNotes

// Dark Mode Toggle
(function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;

    // Check for saved user preference, default to light mode
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        if (darkModeToggle) darkModeToggle.setAttribute('aria-checked', 'true');
    }

    // Toggle dark mode
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            const isDark = body.classList.contains('dark-mode');
            darkModeToggle.setAttribute('aria-checked', String(isDark));
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }
})();

// Mobile Navigation Toggle
(function initNavToggle() {
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            const isOpen = navLinks.classList.toggle('nav-open');
            navToggle.setAttribute('aria-expanded', String(isOpen));
        });

        // Close menu when clicking a link
        navLinks.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('nav-open');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });

        // Close menu on outside click
        document.addEventListener('click', (event) => {
            if (!navToggle.contains(event.target) && !navLinks.contains(event.target)) {
                navLinks.classList.remove('nav-open');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }
})();

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('addItemModal');
    if (modal && event.target === modal) {
        modal.style.display = 'none';
    }
});

// Close modal on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('addItemModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
});

// Show loading state for forms
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.dataset.noLoading) {
            submitBtn.dataset.originalText = submitBtn.textContent;
            submitBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
        }
    });
});

// Loading overlay helper
window.NikNotes = window.NikNotes || {};
window.NikNotes.showLoading = function(message) {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.setAttribute('role', 'alert');
        overlay.setAttribute('aria-live', 'assertive');
        overlay.innerHTML = '<div class="loading-spinner loading-spinner--large"></div><div class="loading-overlay-text"></div>';
        document.body.appendChild(overlay);
    }
    overlay.querySelector('.loading-overlay-text').textContent = message || 'Loading...';
    overlay.classList.add('active');
};
window.NikNotes.hideLoading = function() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
};

// Auto-hide success messages
setTimeout(() => {
    const alerts = document.querySelectorAll('.alert-success');
    alerts.forEach(alert => {
        alert.style.transition = 'opacity 0.5s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
    });
}, 5000);

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Add animation class to cards on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe trip cards
document.querySelectorAll('.trip-card, .packing-item').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
});
