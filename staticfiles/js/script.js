// Filter tournaments function
function filterTournaments() {
    const searchValue = document.getElementById('searchInput').value.toLowerCase();
    const gameValue = document.getElementById('gameFilter').value.toLowerCase();
    const statusValue = document.getElementById('statusFilter').value;

    const cards = document.querySelectorAll('.tournament-card');
    cards.forEach(card => {
        const name = card.querySelector('.tournament-name').textContent.toLowerCase();
        const game = card.dataset.game || '';
        const status = card.dataset.status || '';

        const matchSearch = name.includes(searchValue);
        const matchGame = !gameValue || game.includes(gameValue);
        const matchStatus = !statusValue || status === statusValue;

        if (matchSearch && matchGame && matchStatus) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

// Smooth scroll for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Add animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.tournament-card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    observer.observe(card);
});
