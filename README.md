> **New:** this repository also contains **Vestige Intelligence** — see [`vestige/README.md`](vestige/README.md).

# Luxury Hotel Finder - Flask Web Application

A modern, luxury-themed web application for discovering 5-star hotels worldwide. Built with Flask, integrated with Amadeus Hotel Search API, and featuring a responsive dark-theme UI with premium amenities and pricing information.

## Features

- **🏨 5-Star Hotel Discovery**: Search for ultra-luxury and premium hotels by city
- **🌍 Global Coverage**: Access hotels in major cities worldwide via Amadeus API
- **⭐ Quality Filtering**: Automatic filtering for 5-star rating and 4.8+ review scores
- **🎨 Luxury Design**: Editorial dark-theme aesthetic with beige/cream accents
- **📱 Responsive Layout**: Mobile-friendly interface across all devices
- **🏷️ Amenity Icons**: Visual indicators for WiFi, Pool, Spa, Restaurant, Room Service
- **💳 Price Range Display**: Transparent pricing information for each property
- **🖼️ High-Quality Images**: Unsplash-powered hotel photographs

## Tech Stack

- **Backend**: Flask 2.3.3 with Flask-CORS
- **API Integration**: Amadeus Hotel Search API (OAuth2)
- **Frontend**: HTML5, CSS3 (custom responsive grid), Vanilla JavaScript
- **Icons**: Font Awesome 6.4.0
- **Styling**: CSS Variables for easy theming

## Project Structure

```
flask_hotel_app/
├── app.py                  # Main Flask app and routes
├── config.py               # Configuration management
├── amadeus_client.py       # Amadeus API client
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
├── templates/
│   ├── base.html          # Base template with navbar/footer
│   └── index.html         # Home page with search interface
└── static/
    ├── css/
    │   └── style.css      # Luxury CSS styling
    └── js/
        └── app.js         # Frontend logic and API calls
```

## Installation & Setup

### 1. Clone or Download the Project

```bash
cd flask_hotel_app
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Amadeus API Credentials

1. Visit [Amadeus for Developers](https://developer.amadeus.com)
2. Create a free account (no credit card required)
3. Create a new application to get `Client ID` and `Client Secret`
4. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

5. Edit `.env` and add your credentials:

```
AMADEUS_CLIENT_ID=your_actual_client_id
AMADEUS_CLIENT_SECRET=your_actual_client_secret
FLASK_ENV=development
```

**⚠️ Security Note**: Never commit `.env` to version control. The `.gitignore` file already excludes it.

### 5. Run the Development Server

```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Usage

1. Open `http://localhost:5000` in your browser
2. Enter a city name (e.g., "Paris", "Dubai", "New York")
3. Click "Find Hotels" to search
4. Browse the curated 5-star hotels with images, amenities, and pricing
5. Hover over cards for subtle elevation effects

## API Endpoints

### Public Routes

- `GET /` - Homepage with hotel search interface
- `GET /health` - Health check endpoint

### API Routes

- `GET /api/hotels/<city>` - Search for 5-star hotels in a city
  - **Query Parameters** (optional):
    - `check_in`: Check-in date (YYYY-MM-DD)
    - `check_out`: Check-out date (YYYY-MM-DD)
  - **Response**:
    ```json
    {
      "city": "Paris",
      "hotels": [
        {
          "id": "hotel123",
          "name": "Le Palais Étoilé",
          "location": "Champs-Élysées, Paris",
          "rating": 5,
          "review_score": 4.9,
          "category": "Ultra-luxury",
          "price_range": "$800 - $1,500",
          "amenities": ["WiFi", "Pool", "Spa", "Restaurant"],
          "description": "Iconic Parisian palace hotel...",
          "image_url": "https://..."
        }
      ]
    }
    ```

## Configuration

Edit `config.py` to customize:

- **MIN_STAR_RATING**: Minimum star rating (default: 5)
- **MIN_REVIEW_SCORE**: Minimum review score (default: 4.8)
- **MAX_RESULTS**: Maximum hotels per search (default: 10)
- **REQUEST_TIMEOUT**: API timeout in seconds (default: 10)

## Troubleshooting

### "No luxury hotels found"
- Some cities may have limited 5-star data in Amadeus
- Try popular destinations: Paris, Dubai, New York, Tokyo, London

### "API Rate Limit Exceeded"
- Amadeus free tier has rate limits (~10 requests/minute)
- Wait a minute and try again
- Implement caching for production (see Further Improvements)

### "Invalid Amadeus Credentials"
- Verify your `.env` file has correct credentials
- Check that your Amadeus app is activated in the developer portal
- Ensure you haven't exceeded your API quota

## Further Improvements

1. **Caching**: Implement Redis caching for frequently searched cities
2. **Booking Integration**: Add direct booking links to hotel websites
3. **Map View**: Display hotels on an interactive map
4. **Filters**: Add price range, amenities, and rating filters
5. **User Accounts**: Save favorite hotels and search history
6. **Mobile App**: Build native iOS/Android app
7. **Reviews**: Aggregate and display guest reviews

## Environment Variables

Create a `.env` file in the project root:

```env
# Amadeus API
AMADEUS_CLIENT_ID=your_client_id
AMADEUS_CLIENT_SECRET=your_client_secret

# Flask Config
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
```

## Testing

To test the API locally:

```bash
# Test home page
curl http://localhost:5000/

# Test health check
curl http://localhost:5000/health

# Test hotel search
curl http://localhost:5000/api/hotels/Paris

# With check-in/check-out dates
curl "http://localhost:5000/api/hotels/Dubai?check_in=2026-06-01&check_out=2026-06-03"
```

## Deployment

### Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login
heroku login

# Create app
heroku create your-app-name

# Add buildpack
heroku buildpacks:add heroku/python

# Set environment variables
heroku config:set AMADEUS_CLIENT_ID=your_id
heroku config:set AMADEUS_CLIENT_SECRET=your_secret
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main
```

### PythonAnywhere

1. Create account at [PythonAnywhere](https://www.pythonanywhere.com)
2. Upload project files
3. Create virtual environment
4. Configure WSGI file with Flask app
5. Set environment variables in web app settings
6. Reload web app

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review Amadeus API documentation: https://developers.amadeus.com
3. Open an issue on GitHub

---

**Built with ❤️ for luxury hotel enthusiasts**
