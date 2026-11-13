// Caramel Interactive Client Helper
document.addEventListener('DOMContentLoaded', () => {
  // Restore saved view mode (Mobile frame vs Expanded Desktop)
  const savedMode = localStorage.getItem('caramel_view_mode') || 'mobile';
  if (savedMode === 'desktop') {
    document.body.classList.add('view-desktop');
    const label = document.getElementById('viewModeLabel');
    if (label) {
      label.textContent = 'Vista Móvil';
    }
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
      label.textContent = isDesktop ? 'Vista Móvil' : 'Vista ampliada';
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

  // ============================================================
  // Live Device Hardware Integration: Clock & Battery Status
  // ============================================================
  function updateSystemClock() {
    const clockEl = document.getElementById('mobile-system-clock');
    if (!clockEl) return;
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    clockEl.textContent = `${hours}:${minutes}`;
  }
  updateSystemClock();
  setInterval(updateSystemClock, 1000);

  function initBatteryMonitor() {
    const batteryLevelBar = document.getElementById('mobile-battery-level');
    const batteryText = document.getElementById('mobile-battery-text');
    const batteryBolt = document.getElementById('mobile-battery-bolt');

    if (!batteryLevelBar) return;

    if ('getBattery' in navigator) {
      navigator.getBattery().then(battery => {
        function updateBatteryStatus() {
          const level = Math.round(battery.level * 100);
          const isCharging = battery.charging;

          // Ancho proporcional dinámico
          batteryLevelBar.style.width = `${Math.max(6, level)}%`;

          // Color y estado de carga
          if (isCharging) {
            batteryLevelBar.style.backgroundColor = '#7FB3A6';
            if (batteryBolt) batteryBolt.classList.remove('hidden');
          } else if (level <= 20) {
            batteryLevelBar.style.backgroundColor = '#f87171'; // Nivel crítico
            if (batteryBolt) batteryBolt.classList.add('hidden');
          } else {
            batteryLevelBar.style.backgroundColor = '#7FB3A6';
            if (batteryBolt) batteryBolt.classList.add('hidden');
          }

          if (batteryText) {
            batteryText.textContent = `${level}%`;
          }
        }

        updateBatteryStatus();
        battery.addEventListener('levelchange', updateBatteryStatus);
        battery.addEventListener('chargingchange', updateBatteryStatus);
      }).catch(() => {
        // Fallback seguro en entornos con políticas de permisos restrictivas
        if (batteryLevelBar) batteryLevelBar.style.width = '100%';
      });
    } else {
      // Fallback para navegadores que no exponen Battery API (ej. Safari iOS)
      if (batteryLevelBar) batteryLevelBar.style.width = '100%';
    }
  }
  initBatteryMonitor();
});
