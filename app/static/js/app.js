// Caramel Interactive Client Helper
document.addEventListener('DOMContentLoaded', () => {
  // Horizontal scroll buttons helper
  window.scrollCarousel = function(carouselId, direction) {
    const el = document.getElementById(carouselId);
    if (el) {
      const scrollAmount = direction * 280;
      el.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  // Dynamic Star Rating selector in Review Modal / Forms
  window.selectStarRating = function(value) {
    const input = document.getElementById('selectedRatingInput');
    if (input) input.value = value;
    
    for (let i = 1; i <= 5; i++) {
      const star = document.getElementById(`star-btn-${i}`);
      if (star) {
        if (i <= value) {
          star.classList.add('text-amber-400');
          star.classList.remove('text-stone-300');
        } else {
          star.classList.remove('text-amber-400');
          star.classList.add('text-stone-300');
        }
      }
    }
  };
});
