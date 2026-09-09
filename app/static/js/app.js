// Caramel Interactive Client Helper
document.addEventListener('DOMContentLoaded', () => {
  // Restore saved view mode (Mobile frame vs Expanded Desktop)
  const savedMode = localStorage.getItem('caramel_view_mode') || 'mobile';
  if (savedMode === 'desktop') {
    document.body.classList.add('view-desktop');
  }

  // Horizontal scroll buttons helper
  window.scrollCarousel = function(carouselId, direction) {
    const el = document.getElementById(carouselId);
    if (el) {
      const scrollAmount = direction * 280;
      el.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  // Toggle View Mode (Mobile Frame vs Expanded Layout)
  window.toggleViewMode = function() {
    document.body.classList.toggle('view-desktop');
    const isDesktop = document.body.classList.contains('view-desktop');
    localStorage.setItem('caramel_view_mode', isDesktop ? 'desktop' : 'mobile');
    const label = document.getElementById('viewModeLabel');
    if (label) {
      label.textContent = isDesktop ? 'Vista Móvil (Figma)' : 'Vista Expandida';
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
          star.classList.remove('text-stone-600');
        } else {
          star.classList.remove('text-amber-400');
          star.classList.add('text-stone-600');
        }
      }
    }
  };
});
