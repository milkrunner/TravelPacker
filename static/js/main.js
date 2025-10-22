// Main JavaScript for NikNotes

// Dark Mode Toggle
(function initDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;
    
    // Check for saved user preference, default to light mode
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
    }
    
    // Toggle dark mode
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            
            // Save preference
            if (body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
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

// Show loading state for forms (but allow submission to continue)
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(event) {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.dataset.noLoading) {
            // Don't disable the button, just change the text
            submitBtn.dataset.originalText = submitBtn.textContent;
            submitBtn.textContent = 'Processing...';
            // Let the form submit naturally
        }
    });
});

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

console.log('🎒 NikNotes loaded successfully!');
