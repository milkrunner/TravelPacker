# NikNotes Performance Setup Script
# Run this script to set up PostgreSQL and Redis for blazing fast performance

Write-Host "🚀 NikNotes Performance Setup" -ForegroundColor Cyan
Write-Host "==============================`n" -ForegroundColor Cyan

# Check Python environment
Write-Host "1️⃣  Checking Python environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "   ✅ Virtual environment found" -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "   ❌ Virtual environment not found. Creating..." -ForegroundColor Red
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
}

# Install Python dependencies
Write-Host "`n2️⃣  Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check PostgreSQL
Write-Host "`n3️⃣  Checking PostgreSQL..." -ForegroundColor Yellow
$pgVersion = & psql --version 2>$null
if ($pgVersion) {
    Write-Host "   ✅ PostgreSQL installed: $pgVersion" -ForegroundColor Green
    
    # Test connection
    # Read password from .env file or use default (not recommended for production)
    if (-not $env:POSTGRES_PASSWORD) {
        Write-Host "   ⚠️  POSTGRES_PASSWORD not set. Using default (change this!)" -ForegroundColor Yellow
        $env:PGPASSWORD = "niknotes_pass"
    } else {
        $env:PGPASSWORD = $env:POSTGRES_PASSWORD
    }
    $testConnection = & psql -U niknotes_user -d niknotes_db -c "SELECT 1;" 2>$null
    if ($testConnection) {
        Write-Host "   ✅ Database 'niknotes_db' is accessible" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Database not set up. Creating..." -ForegroundColor Yellow
        Write-Host "   Please enter PostgreSQL superuser password when prompted." -ForegroundColor Cyan
        
        # Create database and user
        $dbPassword = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "niknotes_pass" }
        Write-Host "   ⚠️  Using password from POSTGRES_PASSWORD env variable" -ForegroundColor Yellow
        $createDbScript = @"
CREATE DATABASE niknotes_db;
CREATE USER niknotes_user WITH ENCRYPTED PASSWORD '$dbPassword';
GRANT ALL PRIVILEGES ON DATABASE niknotes_db TO niknotes_user;
"@
        $createDbScript | & psql -U postgres
        
        # Grant schema permissions
        $grantScript = @"
GRANT ALL ON SCHEMA public TO niknotes_user;
ALTER DATABASE niknotes_db OWNER TO niknotes_user;
"@
        $grantScript | & psql -U postgres -d niknotes_db
        
        Write-Host "   ✅ Database created successfully" -ForegroundColor Green
    }
} else {
    Write-Host "   ❌ PostgreSQL not installed" -ForegroundColor Red
    Write-Host "   Please install PostgreSQL from: https://www.postgresql.org/download/windows/" -ForegroundColor Cyan
    Write-Host "   Then run this script again." -ForegroundColor Cyan
    exit 1
}

# Check Redis
Write-Host "`n4️⃣  Checking Redis..." -ForegroundColor Yellow
$redisStatus = Get-Service -Name Redis -ErrorAction SilentlyContinue
if ($redisStatus) {
    if ($redisStatus.Status -eq "Running") {
        Write-Host "   ✅ Redis is running" -ForegroundColor Green
        
        # Test Redis connection
        $redisPing = & redis-cli ping 2>$null
        if ($redisPing -eq "PONG") {
            Write-Host "   ✅ Redis connection successful" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  Redis is installed but not running. Starting..." -ForegroundColor Yellow
        Start-Service Redis
        Write-Host "   ✅ Redis started" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠️  Redis not installed (optional for caching)" -ForegroundColor Yellow
    Write-Host "   Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Cyan
    Write-Host "   Or continue without caching (slower AI suggestions)" -ForegroundColor Cyan
}

# Run database migrations
Write-Host "`n5️⃣  Running database migrations..." -ForegroundColor Yellow
$migrationResult = & python migrate.py create 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Database tables created successfully" -ForegroundColor Green
} else {
    if ($migrationResult -match "already exists") {
        Write-Host "   ✅ Database tables already exist" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Migration warning: $migrationResult" -ForegroundColor Yellow
    }
}

# Test database connection
Write-Host "`n6️⃣  Testing database connection..." -ForegroundColor Yellow
$dbTest = python -c "from src.database import get_db; next(get_db()); print('OK')" 2>&1
if ($dbTest -match "OK") {
    Write-Host "   ✅ Database connection successful" -ForegroundColor Green
} else {
    Write-Host "   ❌ Database connection failed: $dbTest" -ForegroundColor Red
}

# Test Redis cache
Write-Host "`n7️⃣  Testing Redis cache..." -ForegroundColor Yellow
$cacheTest = python -c "from src.services.cache_service import get_cache_service; cache = get_cache_service(); print('OK' if cache.enabled else 'DISABLED')" 2>&1
if ($cacheTest -match "OK") {
    Write-Host "   ✅ Redis cache connected and enabled ⚡" -ForegroundColor Green
} elseif ($cacheTest -match "DISABLED") {
    Write-Host "   ⚠️  Redis cache disabled (install Redis for faster performance)" -ForegroundColor Yellow
} else {
    Write-Host "   ❌ Cache test error: $cacheTest" -ForegroundColor Red
}

# Display setup summary
Write-Host "`n📊 Setup Summary" -ForegroundColor Cyan
Write-Host "================`n" -ForegroundColor Cyan

# Get cache stats
Write-Host "Cache Statistics:" -ForegroundColor Yellow
$cacheStats = python -c "from src.services.cache_service import get_cache_service; import json; cache = get_cache_service(); print(json.dumps(cache.get_stats(), indent=2))" 2>&1
Write-Host $cacheStats -ForegroundColor White

# Count database tables
Write-Host "`nDatabase Tables:" -ForegroundColor Yellow
if (-not $env:POSTGRES_PASSWORD) {
    $env:PGPASSWORD = "niknotes_pass"
} else {
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD
}
$tables = & psql -U niknotes_user -d niknotes_db -c "\dt" 2>$null
Write-Host $tables -ForegroundColor White

# Display next steps
Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Start the web app: python web_app.py" -ForegroundColor White
Write-Host "   2. Open browser: http://localhost:5000" -ForegroundColor White
Write-Host "   3. Create a trip and test AI suggestions" -ForegroundColor White
Write-Host "   4. Watch console for cache performance (🚀 Cache HIT messages)" -ForegroundColor White
Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "   - Performance guide: PERFORMANCE_SETUP.md" -ForegroundColor White
Write-Host "   - AI configuration: GEMINI_SETUP.md" -ForegroundColor White
Write-Host "   - Database guide: DATABASE.md" -ForegroundColor White
Write-Host "   - Web interface: WEB_INTERFACE.md" -ForegroundColor White
Write-Host ""
