# Onion Scraper Frontend Integration

This document explains how to create a separate frontend project that uses the onion scraper as a backend API.

## 🎯 Overview

Your onion scraper project now includes:
- **Fixed CSV data** with clean titles (no more comma/pipe parsing issues)
- **Flask API server** for serving data to frontend applications
- **Sample frontend** demonstrating API usage
- **Comprehensive data endpoints** for all scraper outputs

## 📁 Files Created

### Core Files
- `api_server.py` - Flask API server
- `api_requirements.txt` - Python dependencies for API server
- `frontend_example.html` - Sample frontend dashboard
- `repair_csv.py` - CSV repair utility (already used)
- `clean_csv_titles.py` - Title cleaning utility (already used)

### Data Files (Repaired)
- `crypto_addresses_fast.csv` - Main address data (cleaned)
- `human_trafficking_alerts.csv` - Trafficking alerts
- `scam_alerts.csv` - Scam alerts

## 🚀 Quick Start

### 1. Install API Dependencies

```bash
pip install -r api_requirements.txt
```

### 2. Start the API Server

```bash
python api_server.py
```

The server will start on `http://localhost:5000`

### 3. Open the Frontend

Open `frontend_example.html` in your browser, or serve it with a local server:

```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx serve .

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000/frontend_example.html`

## 📊 API Endpoints

### Core Data Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/addresses` | GET | Get all crypto addresses |
| `/api/addresses/<chain>` | GET | Get addresses by blockchain |
| `/api/trafficking` | GET | Get human trafficking alerts |
| `/api/scams` | GET | Get scam alerts |
| `/api/stats` | GET | Get overall statistics |
| `/api/search` | GET | Search addresses and titles |

### Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/api/health` | GET | Health check |
| `/screenshots/<filename>` | GET | Get screenshot images |

### Query Parameters

#### Addresses Endpoint
- `chain` - Filter by blockchain (BTC, ETH, SOL, etc.)
- `limit` - Number of results (default: all)
- `offset` - Pagination offset (default: 0)

#### Search Endpoint
- `q` - Search query (required)

#### Alerts Endpoints
- `priority` - Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)
- `limit` - Number of results

## 🔧 Frontend Integration Options

### Option 1: Use the Sample Frontend
The `frontend_example.html` provides a complete dashboard with:
- Real-time statistics
- Search functionality
- Chain filtering
- Pagination
- Responsive design

### Option 2: Build Your Own Frontend

#### JavaScript/HTML Approach
```javascript
// Example: Fetch addresses
async function getAddresses() {
    const response = await fetch('http://localhost:5000/api/addresses?limit=100');
    const data = await response.json();
    console.log(data.data); // Array of address objects
}

// Example: Search
async function searchAddresses(query) {
    const response = await fetch(`http://localhost:5000/api/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    return data.data;
}
```

#### React/Vue/Angular Approach
```javascript
// React example
const [addresses, setAddresses] = useState([]);

useEffect(() => {
    fetch('http://localhost:5000/api/addresses')
        .then(res => res.json())
        .then(data => setAddresses(data.data));
}, []);
```

#### Python Frontend (Flask/Django)
```python
import requests

def get_addresses():
    response = requests.get('http://localhost:5000/api/addresses')
    return response.json()['data']
```

## 📈 Data Structure

### Address Object
```json
{
    "url": "http://example.onion",
    "title": "Site Title",
    "chain": "BTC",
    "address": "bc1q...",
    "timestamp": "2025-07-02T06:00:06.494068",
    "screenshot": "screenshots_fast/example.png",
    "categories": ["csam", "human trafficking"],
    "description": "Content-based description",
    "scam": false
}
```

### Statistics Object
```json
{
    "total_addresses": 176,
    "total_trafficking_alerts": 45,
    "total_scam_alerts": 23,
    "chains": {
        "BTC": 120,
        "ETH": 30,
        "SOL": 26
    },
    "categories": {
        "csam": 150,
        "human trafficking": 45,
        "carding": 30
    },
    "priorities": {
        "trafficking": {
            "CRITICAL": 10,
            "HIGH": 20
        },
        "scams": {
            "HIGH": 15,
            "MEDIUM": 8
        }
    }
}
```

## 🎨 Customization Options

### 1. Modify the API Server
Edit `api_server.py` to:
- Add new endpoints
- Modify data filtering
- Add authentication
- Change response format

### 2. Create Different Frontends
- **Analytics Dashboard** - Charts and graphs
- **Search Interface** - Advanced search with filters
- **Alert System** - Real-time notifications
- **Mobile App** - React Native or Flutter
- **Desktop App** - Electron or Tkinter

### 3. Database Integration
Replace CSV files with:
- PostgreSQL for complex queries
- MongoDB for flexible schemas
- Redis for caching
- Elasticsearch for advanced search

## 🔒 Security Considerations

### For Production Use
1. **Add Authentication**
   ```python
   from flask_httpauth import HTTPBasicAuth
   auth = HTTPBasicAuth()
   
   @app.route('/api/addresses')
   @auth.login_required
   def get_addresses():
       # Your code here
   ```

2. **Rate Limiting**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app)
   
   @app.route('/api/addresses')
   @limiter.limit("100 per minute")
   def get_addresses():
       # Your code here
   ```

3. **CORS Configuration**
   ```python
   CORS(app, origins=['https://yourdomain.com'])
   ```

4. **Environment Variables**
   ```python
   import os
   API_KEY = os.environ.get('API_KEY')
   ```

## 🚀 Deployment Options

### Local Development
```bash
python api_server.py
```

### Production Server
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app

# Using Docker
docker build -t onion-scraper-api .
docker run -p 5000:5000 onion-scraper-api
```

### Cloud Deployment
- **Heroku** - Easy deployment with Git
- **AWS Lambda** - Serverless functions
- **Google Cloud Run** - Containerized deployment
- **DigitalOcean** - VPS deployment

## 📝 Example Usage Scenarios

### 1. Law Enforcement Dashboard
- Real-time monitoring of new addresses
- Alert system for high-priority cases
- Export functionality for reports

### 2. Research Platform
- Academic analysis of dark web patterns
- Statistical analysis and trends
- Data visualization and charts

### 3. Compliance Tool
- Address screening for exchanges
- Risk assessment scoring
- Automated reporting

### 4. News/Media Platform
- Public awareness dashboard
- Trend analysis and reporting
- Educational content

## 🔧 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure CORS is enabled in the API server
   - Check browser console for specific errors

2. **API Server Not Starting**
   - Check if port 5000 is available
   - Verify all dependencies are installed
   - Check file permissions

3. **No Data Loading**
   - Verify CSV files exist and are readable
   - Check API server logs for errors
   - Ensure proper file paths

4. **Search Not Working**
   - Verify search query is not empty
   - Check API endpoint is accessible
   - Review browser network tab

### Debug Mode
```bash
# Enable debug mode
export FLASK_ENV=development
python api_server.py
```

## 📞 Support

For issues or questions:
1. Check the API server logs
2. Verify CSV file integrity
3. Test API endpoints directly
4. Review browser console for errors

## 🎉 Next Steps

1. **Start the API server** and test the endpoints
2. **Open the sample frontend** to see the data
3. **Customize the frontend** for your needs
4. **Add authentication** if needed
5. **Deploy to production** when ready

Your onion scraper is now ready to serve data to any frontend application! 🚀 