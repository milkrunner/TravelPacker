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

See [AI Suggestions](docs/features/ai-suggestions.md) for AI configuration and [Performance](docs/architecture/performance.md) for database optimization.

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

### 📋 Trip Templates

**Save and reuse trip configurations**:

- Save frequently-used trips as reusable templates
- Perfect for recurring trips (business, weekends, family vacations)
- One-click trip creation from templates
- Templates include all trip settings and packing items
- Easily manage and update your template library

See [Templates](docs/features/templates.md) for detailed template documentation.

### 📄 PDF Export

**Print or share your packing lists**:

- Export packing lists as professional PDF documents
- Perfect for printing physical checklists
- Share with travel companions via email
- Includes trip details, weather, and complete packing list
- Organized by category with checkboxes for each item
- Offline access without app or internet

See [PDF Export](docs/features/pdf-export.md) for detailed export documentation.

### 🌙 Dark Mode

**Comfortable viewing in any lighting**:

- Toggle between light and dark themes with one click
- Automatic theme persistence across sessions
- Reduces eye strain in low-light environments
- Smooth transitions between themes
- Complete coverage of all UI elements

See [DARK_MODE.md](docs/DARK_MODE.md) for detailed dark mode documentation.

### 📊 Packing History

**Learn from your trips**:

- Review items after each trip: mark what you actually used
- Track usage patterns across trips
- History-based insights for smarter future packing
- See which AI suggestions were most helpful

### ✨ Key Benefits

- ⚡ **Lightning fast**: 10-50ms AI responses with Redis caching
- 🚀 **Scalable**: PostgreSQL connection pooling for 100+ users
- 🧠 **Smart**: Google Gemini AI for personalized suggestions
- 🎯 **Organized**: Category-based packing lists with progress tracking
- 💪 **Reliable**: Database persistence with Alembic migrations for safe schema evolution
- 🔄 **Efficient**: Cached AI suggestions reduce API costs
- 📄 **Exportable**: Professional PDF export for printing and sharing
- 🌙 **Customizable**: Dark mode for comfortable viewing
- 🔒 **Secure**: Enterprise-grade security with authentication & rate limiting

### 🔒 Security Features

**Production-Ready Security**:

- ✅ **CSRF Protection**: Flask-WTF protection on all state-changing operations
- ✅ **Content Security Policy**: Talisman with nonce-based inline script protection
- ✅ **Rate Limiting**: Flask-Limiter prevents brute force and abuse
- ✅ **Input Sanitization**: Bleach XSS protection for user-generated content
- ✅ **Secure Credentials**: Environment variables for all secrets
- ✅ **Container Security**: Non-root user execution in Docker
- ✅ **Database Security**: Localhost-only binding, no exposed ports

#### Rate Limits

- API requests: 50-100/hour
- General browsing: 50/hour, 200/day

See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for complete security details.

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
# 1. Create environment configuration
cp .env.example .env
# Edit .env and set your API keys:
#   - GEMINI_API_KEY (required)
#   - FLASK_SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")
#   - POSTGRES_PASSWORD (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Start all services (PostgreSQL + Redis + Web App)
docker compose up -d

# 3. Open: http://localhost:5000
```

**Note:** PostgreSQL performance settings are configured in `docker-compose.yml` at container startup. No manual configuration needed!

See [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) for detailed Docker instructions.

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

For manual setup or troubleshooting, see [Performance Guide](docs/architecture/performance.md).

### Using the App

1. Create a new trip
2. Specify your travel details (destination, dates, travelers)
3. Let AI suggest items for your packing list
4. Customize and add your own items
5. Check off items as you pack

## 📚 Documentation

Complete documentation is available in the [`docs/`](docs/) folder:

### Getting Started Guides

- **[Quick Start](docs/getting-started/quick-start.md)** - Fast setup guide

### Feature Documentation

- **[AI Suggestions](docs/features/ai-suggestions.md)** - Configure AI recommendations
- **[Smart Packing](docs/features/smart-packing.md)** - Intelligent packing features
- **[Weather Integration](docs/features/weather-integration.md)** - Weather-based suggestions
- **[PDF Export](docs/features/pdf-export.md)** - Export packing lists
- **[Templates](docs/features/templates.md)** - Save and reuse trips
- **[Dark Mode](docs/features/dark-mode.md)** - Theme customization

### Architecture

- **[Database Design](docs/architecture/database-design.md)** - Schema and operations
- **[Performance](docs/architecture/performance.md)** - PostgreSQL & Redis optimization
- **[Web Interface](docs/architecture/web-interface.md)** - Web UI documentation

### Security

- **[Security Overview](docs/security/overview.md)** - Complete security guide
- **[CSRF Protection](docs/security/csrf-protection.md)** - Cross-site request forgery
- **[Content Security Policy](docs/security/csp-protection.md)** - CSP implementation
- **[Content Sanitization](docs/security/content-sanitization.md)** - XSS prevention
- **[Rate Limiting](docs/security/rate-limiting.md)** - API protection

### Operations

- **[Docker Deployment](docs/operations/docker-deployment.md)** - Production deployment
- **[Health Checks](docs/operations/health-checks.md)** - Monitoring guide
- **[Database Migrations](docs/operations/database-migrations.md)** - Alembic migration guide

See [docs/INDEX.md](docs/INDEX.md) for complete documentation index.

## Use Cases

- **Family Vacations**: Get suggestions for kids' items, entertainment, and family essentials
- **Business Trips**: Pack efficiently with work-specific recommendations
- **Adventure Travel**: Don't forget specialized gear for hiking, camping, or extreme sports
- **International Travel**: Remember important documents, adapters, and local essentials

---

Made with ❤️ for stress-free travel planning
