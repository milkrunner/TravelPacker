# NikNotes - AI-Powered Trip Packing Assistant ⚡

Never forget what to pack again! NikNotes is your intelligent travel companion that helps you remember everything you need for your trips.

**🚀 BLAZING FAST**: PostgreSQL + Redis caching for lightning-fast AI suggestions (10-50ms response times!)

## Features

### 🎒 Smart Packing Lists

Keep track of all the items you need to bring on your trip with organized, customizable packing lists.

### 🤖 AI-Powered Suggestions (with Caching!)

Get intelligent recommendations for what to pack based on:

- Your destination
- Trip duration
- Weather conditions
- Activities planned
- Travel type

**Powered by Google Gemini** with **Redis caching** for instant responses:

- **First request**: AI generates suggestions (~2-5 seconds)
- **Subsequent requests**: Cached response (**10-50ms**) ⚡
- **Cache duration**: 24 hours
- **50-500x faster** than uncached requests!

See [GEMINI_SETUP.md](GEMINI_SETUP.md) for AI configuration and [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md) for database optimization.

### 👥 Personalized for Every Traveler

Customize your packing lists based on:

- **Who's traveling**: Solo, couple, family, group
- **Travel style**: Business, leisure, adventure, backpacking
- **Special needs**: Kids, pets, medical requirements
- **Transportation method**: Flight, road trip, train, cruise

### 💾 Enterprise-Grade Database

**PostgreSQL with performance optimizations**:

- Connection pooling (20 base + 40 overflow connections)
- Database indexes on frequently queried columns
- Parallel query execution for complex queries
- SSD optimizations for disk I/O
- Supports **100+ concurrent users**

### ✨ Key Benefits

- ⚡ **Lightning fast**: 10-50ms AI responses with Redis caching
- 🚀 **Scalable**: PostgreSQL connection pooling for 100+ users
- 🧠 **Smart**: Google Gemini AI for personalized suggestions
- 🎯 **Organized**: Category-based packing lists with progress tracking
- 💪 **Reliable**: Database persistence with automatic migrations
- 🔄 **Efficient**: Cached AI suggestions reduce API costs

## Performance Metrics

| Metric                    | Value          |
| ------------------------- | -------------- |
| AI Suggestions (cached)   | **10-50ms** ⚡ |
| AI Suggestions (uncached) | 2-5 seconds    |
| Trip Queries              | **5-20ms**     |
| Max Concurrent Users      | **100+**       |
| Cache Hit Rate            | 75-90%         |
| Database Connections      | 60 (pooled)    |

## Getting Started

### Quick Setup

**🐳 Docker (Recommended for Production):**

```bash
# Set your Gemini API key in .env file or environment
export GEMINI_API_KEY=your_api_key_here

# Start all services (PostgreSQL + Redis + Web App)
docker compose up -d

# Open: http://localhost:5000
```

**Note:** PostgreSQL performance settings are configured in `docker-compose.yml` at container startup. No manual configuration needed!

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker instructions.

**⚡ Automated Setup Scripts:**

**Windows (PowerShell):**

```powershell
.\setup_performance.ps1
```

**Linux/Debian/Ubuntu (Bash):**

```bash
chmod +x setup_performance.sh
./setup_performance.sh
```

These scripts will automatically install PostgreSQL, Redis, create the database, and configure everything! ⚡

For manual setup or troubleshooting, see [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md).

### Using the App

1. Create a new trip
2. Specify your travel details (destination, dates, travelers)
3. Let AI suggest items for your packing list
4. Customize and add your own items
5. Check off items as you pack
6. Export as PDF for printing or sharing

## Feature Documentation

- **[Trip Templates](TEMPLATES.md)** - Save and reuse trip configurations
- **[PDF Export](PDF_EXPORT.md)** - Export packing lists as PDF documents
- **[Dark Mode](DARK_MODE.md)** - Toggle between light and dark themes
- **[Weather Integration](WEATHER_SETUP.md)** - Weather-aware packing suggestions
- **[Smart Quantities](SMART_QUANTITIES.md)** - Intelligent quantity calculations

## Use Cases

- **Family Vacations**: Get suggestions for kids' items, entertainment, and family essentials
- **Business Trips**: Pack efficiently with work-specific recommendations
- **Adventure Travel**: Don't forget specialized gear for hiking, camping, or extreme sports
- **International Travel**: Remember important documents, adapters, and local essentials

---

Made with ❤️ for stress-free travel planning
