# Performance Setup Scripts

NikNotes includes automated setup scripts for both Windows and Linux platforms.

## 🚀 Quick Start

### Windows (PowerShell)

```powershell
.\scripts\setup_performance.ps1
```

### Linux/Debian/Ubuntu (Bash)

```bash
chmod +x scripts/setup_performance.sh
./scripts/setup_performance.sh
```

## 📋 What These Scripts Do

Both scripts automatically:

1. ✅ **Check Python environment** - Verify/create virtual environment
2. ✅ **Install dependencies** - Install psycopg2-binary and redis packages
3. ✅ **Check PostgreSQL** - Verify installation or install if missing (Linux)
4. ✅ **Create database** - Set up `niknotes_db` with user `niknotes_user`
5. ✅ **Check Redis** - Verify installation or prompt to install (optional)
6. ✅ **Run migrations** - Create database tables with performance indexes
7. ✅ **Test connections** - Verify database and cache connectivity
8. ✅ **Display statistics** - Show cache stats and database tables

**Note:** PostgreSQL performance parameters are configured manually in `postgresql.conf` for local installations (see PERFORMANCE_SETUP.md). For Docker deployments, all performance settings are handled automatically in `docker-compose.yml`.

## 🔧 Platform Differences

### Windows Script (`setup_performance.ps1`)

- Uses PowerShell cmdlets (`Get-Service`, `Start-Service`)
- Checks Windows services for PostgreSQL and Redis
- Requires manual PostgreSQL installation from installer
- Redis installation is manual (provides download link)
- Compatible with Windows 10/11, Server 2016+

### Linux Script (`setup_performance.sh`)

- Uses systemd commands (`systemctl`)
- Can auto-install PostgreSQL via `apt-get`
- Can auto-install Redis via `apt-get`
- Prompts user before installing Redis (optional)
- Compatible with Debian, Ubuntu, Mint, and derivatives

## 📊 Expected Output

Both scripts provide color-coded output:

- 🟢 **Green** - Success/OK
- 🟡 **Yellow** - Warnings/Info
- 🔴 **Red** - Errors
- 🔵 **Cyan** - Instructions/Headers

Example success output:

```output
🚀 NikNotes Performance Setup
==============================

1️⃣  Checking Python environment...
   ✅ Virtual environment found
   ✅ Python 3.11.9

2️⃣  Installing Python dependencies...
   ✅ Dependencies installed

3️⃣  Checking PostgreSQL...
   ✅ PostgreSQL installed: 16.1
   ✅ Database 'niknotes_db' is accessible

4️⃣  Checking Redis...
   ✅ Redis is running
   ✅ Redis version: 7.0.15

5️⃣  Running database migrations...
   ✅ Database tables created successfully

6️⃣  Testing database connection...
   ✅ Database connection successful

7️⃣  Testing Redis cache...
   ✅ Redis cache connected and enabled ⚡

📊 Setup Summary
================
[Cache statistics and database tables displayed]

✅ Setup Complete!
```

## 🐛 Troubleshooting

### Script Won't Run (Windows)

```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Script Won't Run (Linux)

```bash
# Make executable
chmod +x scripts/setup_performance.sh

# Run with bash explicitly
bash scripts/setup_performance.sh
```

### PostgreSQL Not Found

**Windows:** Install manually from <https://www.postgresql.org/download/windows/>

**Linux:**

```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

### Redis Not Found

**Windows:** Download from <https://github.com/microsoftarchive/redis/releases>

**Linux:**

```bash
sudo apt-get install redis-server
```

### Permission Denied (Linux)

```bash
# Run database setup commands with sudo
sudo ./scripts/setup_performance.sh
```

## 📚 Manual Setup

If you prefer manual setup or need to troubleshoot, see:

- **[PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md)** - Detailed step-by-step guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick command reference

## 🔐 Security Notes

Both scripts use default credentials:

- **Database User:** `niknotes_user`
- **Database Password:** `niknotes_pass`
- **Database Name:** `niknotes_db`

**For production:** Change these in:

1. `.env` file (DATABASE_URL)
2. PostgreSQL database creation commands
3. Redis configuration (if using authentication)

## 🎯 Next Steps After Setup

1. **Start the app:**

   ```bash
   python web_app.py
   ```

2. **Open browser:** <http://localhost:5000>

3. **Create a trip** and watch for cache performance messages:
   - `🚀 Cache HIT: AI suggestions` - ⚡ BLAZING FAST!
   - `💾 Cached AI suggestions (TTL: 24h)` - Cached for next time

4. **Monitor performance:** See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for monitoring commands

## 💡 Tips

- **Windows users:** Run PowerShell as Administrator for best results
- **Linux users:** Script will use `sudo` when needed
- **Redis is optional:** App works without it, but AI suggestions are 50-500x slower
- **First run is slow:** Subsequent AI requests hit the cache and are instant!

---

**Need help?** Check [PERFORMANCE_SETUP.md](PERFORMANCE_SETUP.md) for detailed troubleshooting.
