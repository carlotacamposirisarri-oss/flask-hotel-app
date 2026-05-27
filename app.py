"""
Flask Hotel Finder Application - Demo Version
Serves curated luxury hotel data without requiring external API credentials.
"""

import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS

from config import current_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock hotel database for all major cities
HOTEL_DATABASE = {
    "paris": [
        {
            "id": "DEMO001",
            "name": "Le Palais Étoilé",
            "location": "Champs-Élysées, Paris",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Michelin Restaurant", "Rooftop Lounge", "Private Spa", "Chauffeur Service", "24h Concierge"],
            "category": "Ultra-luxury",
            "price_range": "$800 - $1,500",
            "description": "An iconic Parisian palace hotel where gilded atrium halls and whispered service define the art of staying well.",
        },
        {
            "id": "DEMO002",
            "name": "Maison de Luxe",
            "location": "Saint-Germain-des-Prés, Paris",
            "rating": 5,
            "review_score": 4.8,
            "image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Designer Suites", "Indoor Pool", "Personal Concierge", "VIP Shopping", "Wine Library"],
            "category": "Ultra-luxury",
            "price_range": "$550 - $950",
            "description": "A Left Bank retreat of understated opulence — each suite a private world of silk, stone and city light.",
        },
        {
            "id": "DEMO003",
            "name": "Le Ritz Paris",
            "location": "Place Vendôme, Paris",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Michelin Chef", "Historical Spa", "Jewelry Store", "Limousine Service", "Private Garden"],
            "category": "Ultra-luxury",
            "price_range": "$900 - $2,000",
            "description": "Place Vendôme's crown jewel — over a century of Proustian grandeur, reinvented for the modern connoisseur.",
        },
    ],
    "dubai": [
        {
            "id": "DEMO004",
            "name": "Skyline Royal Resort",
            "location": "Downtown Dubai",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Infinity Pool", "Private Beach", "Helicopter Tours", "Spa Treatments", "Fine Dining"],
            "category": "Ultra-luxury",
            "price_range": "$700 - $1,300",
            "description": "A vertical sanctuary above the city skyline, where rooftop infinity pools dissolve into the Arabian horizon.",
        },
        {
            "id": "DEMO005",
            "name": "Pearl of Arabia",
            "location": "Palm Jumeirah, Dubai",
            "rating": 5,
            "review_score": 4.8,
            "image_url": "https://images.unsplash.com/photo-1501117716987-c8ec9c0fac61?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Ocean Villas", "Fine Dining", "Water Sports", "Yacht Access", "Private Beach Club"],
            "category": "Ultra-luxury",
            "price_range": "$450 - $900",
            "description": "Stretching over the Palm's shoreline — private beach villas, yacht moorings, and perpetual golden light.",
        },
        {
            "id": "DEMO006",
            "name": "Burj Al Arab",
            "location": "Jumeirah Beach, Dubai",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1567521464027-f127ff144326?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Underwater Restaurant", "Helipad Arrival", "Private Beach", "Gold-Plated Interiors", "In-Room Chef"],
            "category": "Ultra-luxury",
            "price_range": "$1,200 - $3,000",
            "description": "The world's most iconic silhouette on water — every suite a duplex, every arrival a theatre.",
        },
    ],
    "new york": [
        {
            "id": "DEMO007",
            "name": "The Plaza Premier",
            "location": "Fifth Avenue, New York",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Michelin Restaurant", "Spa", "Rooftop Bar", "Personal Shoppers", "Theater"],
            "category": "Ultra-luxury",
            "price_range": "$750 - $2,000",
            "description": "Overlooking the green expanse of Central Park — a Beaux-Arts monument to Manhattan ambition.",
        },
        {
            "id": "DEMO008",
            "name": "The Mark New York",
            "location": "Upper East Side, New York",
            "rating": 5,
            "review_score": 4.8,
            "image_url": "https://images.unsplash.com/photo-1570129477492-45a003537e1f?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Park Views", "Michelin Chef", "Spa Retreat", "Concierge", "Sky Pool"],
            "category": "Ultra-luxury",
            "price_range": "$850 - $1,800",
            "description": "Upper East Side's jewel box hotel — Jean-Georges cuisine, a legendary bar, and effortless New York ease.",
        },
    ],
    "tokyo": [
        {
            "id": "DEMO009",
            "name": "The Peninsula Tokyo",
            "location": "Chiyoda, Tokyo",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Rooftop Garden", "Japanese Spa", "Fine Dining", "Michelin Chef", "Imperial Palace Views"],
            "category": "Ultra-luxury",
            "price_range": "$600 - $1,400",
            "description": "Refined Japanese hospitality at its apex — rooms overlooking imperial gardens, service of uncanny precision.",
        },
        {
            "id": "DEMO010",
            "name": "Aman Tokyo",
            "location": "Otemachi, Tokyo",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Aman Spa", "Indoor Pool", "Zen Garden", "Teppanyaki Chef", "Shinkansen Concierge"],
            "category": "Ultra-luxury",
            "price_range": "$1,100 - $2,500",
            "description": "Thirty-three floors above Otemachi — shoji screens, a 30-metre pool, and Tokyo at your feet.",
        },
    ],
    "london": [
        {
            "id": "DEMO011",
            "name": "Claridge's",
            "location": "Mayfair, London",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Michelin Restaurant", "Art Deco Rooms", "Spa", "Afternoon Tea", "Rooftop Bar"],
            "category": "Ultra-luxury",
            "price_range": "$650 - $1,500",
            "description": "Mayfair's living landmark — where Art Deco geometry, Bollinger, and discreet British service converge.",
        },
        {
            "id": "DEMO012",
            "name": "Savoy London",
            "location": "Strand, London",
            "rating": 5,
            "review_score": 4.8,
            "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Thames Views", "Michelin Chef", "Art Deco Spa", "Grill Room", "Rooftop Terrace"],
            "category": "Ultra-luxury",
            "price_range": "$600 - $1,400",
            "description": "London's original grand hotel — Thames river suites, the American Bar, and a century of theatre-night glamour.",
        },
    ],
    "maldives": [
        {
            "id": "DEMO013",
            "name": "Soneva Fushi",
            "location": "Baa Atoll, Maldives",
            "rating": 5,
            "review_score": 5.0,
            "image_url": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Overwater Villas", "Private Observatory", "Open-Air Cinema", "Spa", "Snorkelling Reef"],
            "category": "Ultra-luxury",
            "price_range": "$2,000 - $6,000",
            "description": "A castaway island of barefoot luxury — thatched water villas, a private reef, and skies unspoilt by light.",
        },
        {
            "id": "DEMO014",
            "name": "Gili Lankanfushi",
            "location": "North Malé Atoll, Maldives",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1540541338537-3ceaa6aa6bea?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Crusoe Residences", "Overwater Spa", "Dive Centre", "Organic Garden", "Personal Mr. Friday"],
            "category": "Ultra-luxury",
            "price_range": "$1,500 - $4,500",
            "description": "The original overwater villa resort — where lagoon-blue infinity dissolves at sunset into coral pink.",
        },
    ],
    "santorini": [
        {
            "id": "DEMO015",
            "name": "Canaves Oia Epitome",
            "location": "Oia, Santorini",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Infinity Pool", "Caldera Views", "Sunset Dining", "Private Plunge Pools", "Helicopter Transfers"],
            "category": "Ultra-luxury",
            "price_range": "$1,200 - $3,500",
            "description": "Carved into Oia's caldera edge — suites of whitewashed stone, private pools and a view that redefines dusk.",
        },
        {
            "id": "DEMO016",
            "name": "Grace Santorini",
            "location": "Imerovigli, Santorini",
            "rating": 5,
            "review_score": 4.8,
            "image_url": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Champagne Terrace", "Spa Cave", "Private Pool Suites", "Yacht Charters", "Wine Cellar"],
            "category": "Ultra-luxury",
            "price_range": "$900 - $2,800",
            "description": "Suspended above the Aegean on the rim of an ancient volcano — where every terrace is a front-row seat to eternity.",
        },
    ],
    "bali": [
        {
            "id": "DEMO017",
            "name": "Amandari",
            "location": "Ubud, Bali",
            "rating": 5,
            "review_score": 4.9,
            "image_url": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Rice Terrace Views", "Aman Spa", "Infinity Pool", "Yoga Pavilion", "Temple Ceremonies"],
            "category": "Ultra-luxury",
            "price_range": "$900 - $2,200",
            "description": "Terraced into Bali's sacred valley — stone pavilions, gamelan at dusk, and a pool that mirrors the rice fields.",
        },
        {
            "id": "DEMO018",
            "name": "COMO Uma Ubud",
            "location": "Ubud, Bali",
            "rating": 5,
            "review_score": 4.8,
            "image_url": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1400&q=85",
            "amenities": ["Jungle Pool", "COMO Shambhala Spa", "Cooking Classes", "Guided Treks", "Meditation Garden"],
            "category": "Ultra-luxury",
            "price_range": "$700 - $1,800",
            "description": "A jungle sanctuary on the Tjampuhan Ridge — clean living, profound stillness, and Balinese ritual at every turn.",
        },
    ],
}


def create_app(config=None):
    """
    Create and configure the Flask application.

    Args:
        config: Configuration object (defaults to current_config)

    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    if config is None:
        config = current_config

    app.config.from_object(config)
    CORS(app)

    # Register routes
    register_routes(app)

    return app


def register_routes(app):
    """Register application routes."""

    @app.route("/")
    def index():
        """Render homepage."""
        return render_template("index.html")

    @app.route("/api/hotels/<city>", methods=["GET"])
    def get_hotels(city):
        """
        Get 5-star luxury hotels for a city.

        Args:
            city: City name (e.g., Paris, Dubai, New York, Tokyo, London)

        Returns:
            JSON list of luxury hotels with details
        """
        if not city or not city.strip():
            return jsonify({"error": "City name is required"}), 400

        city_normalized = city.strip().lower()
        hotels = HOTEL_DATABASE.get(city_normalized)

        if not hotels:
            available_cities = ", ".join(HOTEL_DATABASE.keys())
            return jsonify(
                {
                    "error": f"No luxury hotels found for '{city}'. Try: {available_cities}"
                }
            ), 404

        return jsonify({"city": city, "hotels": hotels}), 200

    @app.route("/api/cities", methods=["GET"])
    def get_cities():
        """Get list of available cities."""
        cities = list(HOTEL_DATABASE.keys())
        return jsonify({"cities": cities}), 200

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "Flask Hotel Finder"}), 200

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors."""
        logger.error(f"Server error: {error}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5001)

