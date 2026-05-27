/**
 * Maison — Luxury Hotel Finder
 * Frontend: search, API, card rendering, scroll effects
 */

document.addEventListener('DOMContentLoaded', function () {

  // ── DOM refs ────────────────────────────────────────────────────────
  const searchForm          = document.getElementById('searchForm');
  const cityInput           = document.getElementById('cityInput');
  const errorContainer      = document.getElementById('errorContainer');
  const loadingContainer    = document.getElementById('loadingContainer');
  const resultsHeader       = document.getElementById('resultsHeader');
  const hotelsContainer     = document.getElementById('hotelsContainer');
  const cityNameSpan        = document.getElementById('cityName');
  const hotelCountSpan      = document.getElementById('hotelCount');
  const navbar              = document.getElementById('navbar');
  const destinationsSection = document.getElementById('destinationsSection');

  // ── Navbar scroll effect ────────────────────────────────────────────
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 48);
  }, { passive: true });

  // ── Intersection Observer for card fade-up ──────────────────────────
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
  );

  // ── State helpers ───────────────────────────────────────────────────

  function showError(message) {
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
    loadingContainer.style.display = 'none';
    resultsHeader.style.display = 'none';
    hotelsContainer.innerHTML = '';
  }

  function clearError() {
    errorContainer.textContent = '';
    errorContainer.style.display = 'none';
  }

  function showLoading() {
    clearError();
    loadingContainer.style.display = 'flex';
    resultsHeader.style.display = 'none';
    hotelsContainer.innerHTML = '';
    if (destinationsSection) destinationsSection.style.display = 'none';
    setTimeout(() => loadingContainer.scrollIntoView({ behavior: 'smooth', block: 'center' }), 80);
  }

  function showDestinations() {
    if (destinationsSection) destinationsSection.style.display = '';
    loadingContainer.style.display = 'none';
    resultsHeader.style.display = 'none';
    hotelsContainer.innerHTML = '';
  }

  // ── API ─────────────────────────────────────────────────────────────

  async function fetchHotels(city) {
    const response = await fetch(`/api/hotels/${encodeURIComponent(city)}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `Request failed (${response.status})`);
    }
    return response.json();
  }

  // ── Card rendering ──────────────────────────────────────────────────

  function createHotelCard(hotel, index) {
    const card = document.createElement('article');
    card.className = 'hotel-card fade-up';
    card.style.transitionDelay = `${Math.min(index * 60, 300)}ms`;

    const amenitiesHTML = hotel.amenities
      .slice(0, 6)
      .map(a => `
        <li class="amenity-item">
          <i class="fas fa-check"></i>
          ${escapeHtml(a)}
        </li>
      `)
      .join('');

    card.innerHTML = `
      <div class="hotel-image">
        <img src="${escapeHtml(hotel.image_url)}" alt="${escapeHtml(hotel.name)}" loading="lazy" />
        <div class="hotel-meta">
          <div class="rating-badge">
            <span class="rating-stars">★★★★★</span>
            ${escapeHtml(String(hotel.rating))}
          </div>
        </div>
      </div>
      <div class="hotel-content">
        <div class="hotel-header">
          <h3>${escapeHtml(hotel.name)}</h3>
          <p class="hotel-location">
            <i class="fas fa-map-marker-alt"></i>
            ${escapeHtml(hotel.location || 'Location not specified')}
          </p>
        </div>
        <div class="hotel-category">
          <span class="category-chip">
            <i class="fas fa-crown"></i>
            ${escapeHtml(hotel.category)}
          </span>
          <span class="price-chip">
            <i class="fas fa-tag"></i>
            ${escapeHtml(hotel.price_range)}
          </span>
        </div>
        <p class="hotel-description">${escapeHtml(hotel.description)}</p>
        <div>
          <div class="amenities-title">Amenities</div>
          <ul class="amenities-list">${amenitiesHTML}</ul>
        </div>
        <span class="card-cta">
          View Property <i class="fas fa-arrow-right"></i>
        </span>
      </div>
    `;

    revealObserver.observe(card);
    return card;
  }

  function renderHotels(city, hotels) {
    clearError();
    loadingContainer.style.display = 'none';
    resultsHeader.style.display = 'block';
    if (destinationsSection) destinationsSection.style.display = 'none';

    cityNameSpan.textContent = escapeHtml(city);
    hotelCountSpan.textContent = `${hotels.length} ${hotels.length === 1 ? 'Property' : 'Properties'} Found`;

    hotelsContainer.innerHTML = '';
    hotels.forEach((hotel, i) => hotelsContainer.appendChild(createHotelCard(hotel, i)));

    // Scroll to results smoothly
    setTimeout(() => {
      document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 120);
  }

  // ── Security ────────────────────────────────────────────────────────

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  }

  // ── Destination card clicks ─────────────────────────────────────────

  document.querySelectorAll('.dest-card').forEach((card) => {
    card.addEventListener('click', () => {
      const city = card.dataset.city;
      if (!city) return;
      cityInput.value = city.charAt(0).toUpperCase() + city.slice(1);
      searchForm.dispatchEvent(new Event('submit'));
    });
  });

  // ── Form submit ─────────────────────────────────────────────────────

  searchForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    const city = cityInput.value.trim();
    if (!city) { showError('Please enter a destination.'); return; }

    showLoading();

    try {
      const data = await fetchHotels(city);
      renderHotels(data.city, data.hotels);
    } catch (err) {
      // On error, show destinations again so the page doesn't feel broken
      showDestinations();
      clearError();
      errorContainer.textContent = err.message;
      errorContainer.style.display = 'block';
    }
  });

});
