// Caramel Interactive Client Helper
document.addEventListener('DOMContentLoaded', () => {
  // Horizontal scroll buttons helper
  window.scrollCarousel = function(carouselId, direction) {
    const el = document.getElementById(carouselId);
    if (el) {
      const scrollAmount = direction * 340;
      el.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  // Click-and-drag horizontal scrolling for carousels
  document.querySelectorAll('#carousel-recommendations, [data-drag-carousel]').forEach((slider) => {
    let isDown = false;
    let isDragging = false;
    let startX = 0;
    let scrollLeft = 0;

    slider.classList.add('cursor-grab', 'select-none');

    slider.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      isDown = true;
      isDragging = false;
      startX = e.pageX - slider.offsetLeft;
      scrollLeft = slider.scrollLeft;
      slider.classList.remove('scroll-smooth', 'cursor-grab');
      slider.classList.add('cursor-grabbing');
    });

    const stopDrag = () => {
      if (!isDown) return;
      isDown = false;
      slider.classList.remove('cursor-grabbing');
      slider.classList.add('scroll-smooth', 'cursor-grab');
    };

    slider.addEventListener('mouseleave', stopDrag);
    slider.addEventListener('mouseup', stopDrag);

    slider.addEventListener('mousemove', (e) => {
      if (!isDown) return;
      const x = e.pageX - slider.offsetLeft;
      const walk = x - startX;
      if (Math.abs(walk) > 6) {
        isDragging = true;
        e.preventDefault();
        slider.scrollLeft = scrollLeft - walk * 1.25;
      }
    });

    // Prevent native image/link ghost dragging while dragging the carousel
    slider.addEventListener('dragstart', (e) => e.preventDefault());

    // Prevent accidental click navigation when releasing after a drag
    slider.addEventListener('click', (e) => {
      if (isDragging) {
        e.preventDefault();
        e.stopPropagation();
        isDragging = false;
      }
    }, true);
  });

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

  // Transición suave entre /login, /register y /docente/registro
  const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('a[data-auth-transition]').forEach((link) => {
    link.addEventListener('click', (e) => {
      if (
        reducedMotion ||
        e.defaultPrevented ||
        e.button !== 0 ||
        e.metaKey ||
        e.ctrlKey ||
        e.shiftKey ||
        e.altKey ||
        link.target === '_blank'
      ) {
        return;
      }
      const href = link.getAttribute('href');
      if (!href || href.startsWith('#')) return;
      e.preventDefault();
      document.documentElement.classList.add('caramel-auth-leaving');
      window.setTimeout(() => {
        window.location.href = href;
      }, 210);
    });
  });

  // Limpiar estado de salida si el usuario vuelve con el botón Atrás (bfcache)
  window.addEventListener('pageshow', () => {
    document.documentElement.classList.remove('caramel-auth-leaving');
  });
});
