# ⚡ Quick Reference - Blazing Fast Commands

## 🚀 One-Command Setup

```powershell
# Automated setup (recommended)
.\scripts\setup_performance.ps1
```

## 🏃 Quick Start

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create database (PostgreSQL must be running)
python scripts/migrate.py create

# 3. Start app (accessible on all network interfaces)
python web_app.py

# 4. Open browser
# Local:   http://localhost:5000
# Network: http://YOUR_LOCAL_IP:5000
```

## 🌐 Network Access

```powershell
# Get your network access information
python scripts/network_info.py

# This displays:
# - Your local IP address
# - All access URLs (localhost, network, mobile)
# - Firewall configuration commands
# - QR code for mobile access (if qrcode installed)
```

## 📊 Performance Monitoring

### Check Cache Stats

```powershell
python -c "from src.services.cache_service import get_cache_service; import json; cache = get_cache_service(); print(json.dumps(cache.get_stats(), indent=2))"
```

### Test Database Connection

```powershell
python -c "from src.database import get_db; next(get_db()); print('✅ Database OK')"
```

### Test Redis Connection

```powershell
redis-cli ping  # Should return PONG
```

### View Database Tables

```powershell
$env:PGPASSWORD="niknotes_pass"
psql -U niknotes_user -d niknotes_db -c "\dt"
```

### View Database Indexes

```powershell
psql -U niknotes_user -d niknotes_db -c "\di"
```

## 🔧 Database Management

### Reset Database

```powershell
python scripts/migrate.py drop   # Drop all tables
python scripts/migrate.py create # Create fresh tables
```

### PostgreSQL Service

```powershell
Get-Service postgresql-x64-16     # Check status
Start-Service postgresql-x64-16   # Start
Stop-Service postgresql-x64-16    # Stop
Restart-Service postgresql-x64-16 # Restart
```

### Redis Service

```powershell
Get-Service Redis     # Check status
Start-Service Redis   # Start
Stop-Service Redis    # Stop
```

## 🧹 Clear Cache

### Clear All Redis Data

```powershell
redis-cli FLUSHDB
```

### Clear Specific Cache

```powershell
python -c "from src.services.cache_service import get_cache_service; cache = get_cache_service(); cache.clear_all()"
```

## 📈 PostgreSQL Monitoring Queries

### Active Connections

```sql
SELECT count(*) FROM pg_stat_activity;
```

### Slow Queries

```sql
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

### Index Usage

```sql
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Cache Hit Ratio (should be >90%)

```sql
SELECT
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit)  as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

### Database Size

```sql
SELECT pg_size_pretty(pg_database_size('niknotes_db'));
```

## 🎯 Performance Targets

| Metric               | Target | Command to Check       |
| -------------------- | ------ | ---------------------- |
| Cache Hit Rate       | >75%   | `redis-cli info stats` |
| DB Cache Hit         | >90%   | SQL query above        |
| AI Response (cached) | <100ms | Watch console logs     |
| Trip Query           | <50ms  | Watch console logs     |
| Active Connections   | <30    | SQL query above        |

## 🐛 Troubleshooting

### PostgreSQL won't start

```powershell
# Check logs
Get-Content "C:\Program Files\PostgreSQL\16\data\log\*.log" | Select-Object -Last 50
```

### Can't connect to database

```powershell
# Test connection
psql -U postgres -c "SELECT version();"

# Check .env file
Get-Content .env | Select-String "DATABASE_URL"
```

### Redis not responding

```powershell
# Check if running
Get-Process redis-server

# Restart
Restart-Service Redis
```

### Cache not working

```powershell
# Check Redis connection
redis-cli ping

# Check Python can connect
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

## 📚 Documentation

- [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) - Complete migration overview
- [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md) - Detailed setup guide
- [DATABASE.md](DATABASE.md) - Database architecture
- [AUTHENTICATION.md](AUTHENTICATION.md) - User authentication & authorization
- [RATE_LIMITING.md](RATE_LIMITING.md) - Rate limiting configuration
- [CSRF_PROTECTION.md](CSRF_PROTECTION.md) - CSRF security
- [CONTAINER_SECURITY.md](CONTAINER_SECURITY.md) - Docker security
- [GEMINI_SETUP.md](GEMINI_SETUP.md) - AI configuration
- [WEATHER_SETUP.md](WEATHER_SETUP.md) - Weather integration guide
- [SMART_QUANTITIES.md](SMART_QUANTITIES.md) - Smart quantity suggestions (v0.8.0)
- [WEB_INTERFACE.md](WEB_INTERFACE.md) - Web app guide
- [README.md](README.md) - Main documentation

## ⚡ Performance Expectations

- **First AI request**: 2-5 seconds (generates + caches)
- **Cached AI request**: **10-50ms** ⚡ (50-500x faster!)
- **Database queries**: **5-20ms** ⚡
- **Max concurrent users**: **100+** 🚀
- **Cache hit rate**: 75-90% after warm-up
- **Memory usage**: ~300MB (PostgreSQL + Redis)

## 🎉 Success Indicators

When you see these in the console, everything is working perfectly:

```output
✅ Redis cache connected
✅ Gemini AI initialized with cache
✅ AI Service initialized (Cache: ON)
✅ Database connected

🚀 Cache HIT: AI suggestions  ← This means BLAZING FAST! ⚡
💾 Cached AI suggestions (TTL: 24h)
```

---

**Quick Help**: Run `.\setup_performance.ps1` to diagnose and fix common issues!
