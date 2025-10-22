#!/bin/bash
# NikNotes Performance Setup Script for Debian/Ubuntu
# Run this script to set up PostgreSQL and Redis for blazing fast performance

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 NikNotes Performance Setup${NC}"
echo -e "${CYAN}==============================\n${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}⚠️  Please don't run this script as root${NC}"
    echo -e "${YELLOW}   It will use sudo when needed${NC}\n"
fi

# Check Python environment
echo -e "${YELLOW}1️⃣  Checking Python environment...${NC}"
if [ -d "venv" ]; then
    echo -e "   ${GREEN}✅ Virtual environment found${NC}"
    source venv/bin/activate
else
    echo -e "   ${RED}❌ Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "   ${GREEN}✅ Python $PYTHON_VERSION${NC}"

# Install Python dependencies
echo -e "\n${YELLOW}2️⃣  Installing Python dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Check PostgreSQL
echo -e "\n${YELLOW}3️⃣  Checking PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | awk '{print $3}')
    echo -e "   ${GREEN}✅ PostgreSQL installed: $PG_VERSION${NC}"
    
    # Test connection
    # Use password from environment or default (change in production!)
    if [ -z "$POSTGRES_PASSWORD" ]; then
        echo -e "   ${YELLOW}⚠️  POSTGRES_PASSWORD not set. Using default (change this!)${NC}"
        export PGPASSWORD="niknotes_pass"
    else
        export PGPASSWORD="$POSTGRES_PASSWORD"
    fi
    if psql -U niknotes_user -d niknotes_db -h localhost -c "SELECT 1;" &> /dev/null; then
        echo -e "   ${GREEN}✅ Database 'niknotes_db' is accessible${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Database not set up. Creating...${NC}"
        
        # Check if PostgreSQL service is running
        if ! sudo systemctl is-active --quiet postgresql; then
            echo -e "   ${YELLOW}⚠️  PostgreSQL service not running. Starting...${NC}"
            sudo systemctl start postgresql
        fi
        
        # Create database and user
        DB_PASSWORD="${POSTGRES_PASSWORD:-niknotes_pass}"
        echo -e "   ${YELLOW}⚠️  Using password from POSTGRES_PASSWORD env variable or default${NC}"
        echo -e "   ${CYAN}Creating database and user...${NC}"
        sudo -u postgres psql << EOF
CREATE DATABASE niknotes_db;
CREATE USER niknotes_user WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE niknotes_db TO niknotes_user;
\c niknotes_db
GRANT ALL ON SCHEMA public TO niknotes_user;
ALTER DATABASE niknotes_db OWNER TO niknotes_user;
EOF
        
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✅ Database created successfully${NC}"
        else
            echo -e "   ${RED}❌ Database creation failed${NC}"
        fi
    fi
else
    echo -e "   ${RED}❌ PostgreSQL not installed${NC}"
    echo -e "   ${CYAN}Installing PostgreSQL...${NC}"
    
    # Update package list
    sudo apt-get update
    
    # Install PostgreSQL
    sudo apt-get install -y postgresql postgresql-contrib
    
    # Start PostgreSQL service
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    echo -e "   ${GREEN}✅ PostgreSQL installed${NC}"
    
    # Create database and user
    DB_PASSWORD="${POSTGRES_PASSWORD:-niknotes_pass}"
    echo -e "   ${YELLOW}⚠️  Using password from POSTGRES_PASSWORD env variable or default${NC}"
    echo -e "   ${CYAN}Creating database and user...${NC}"
    sudo -u postgres psql << EOF
CREATE DATABASE niknotes_db;
CREATE USER niknotes_user WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE niknotes_db TO niknotes_user;
\c niknotes_db
GRANT ALL ON SCHEMA public TO niknotes_user;
ALTER DATABASE niknotes_db OWNER TO niknotes_user;
EOF
    
    echo -e "   ${GREEN}✅ Database setup complete${NC}"
fi

# Check Redis
echo -e "\n${YELLOW}4️⃣  Checking Redis...${NC}"
if command -v redis-cli &> /dev/null; then
    # Check if Redis is running
    if redis-cli ping &> /dev/null; then
        echo -e "   ${GREEN}✅ Redis is running${NC}"
        REDIS_VERSION=$(redis-cli --version | awk '{print $2}')
        echo -e "   ${GREEN}✅ Redis version: $REDIS_VERSION${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Redis installed but not running. Starting...${NC}"
        sudo systemctl start redis-server
        sudo systemctl enable redis-server
        
        if redis-cli ping &> /dev/null; then
            echo -e "   ${GREEN}✅ Redis started${NC}"
        else
            echo -e "   ${RED}❌ Failed to start Redis${NC}"
        fi
    fi
else
    echo -e "   ${YELLOW}⚠️  Redis not installed (optional for caching)${NC}"
    read -p "   Install Redis for better performance? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "   ${CYAN}Installing Redis...${NC}"
        sudo apt-get update
        sudo apt-get install -y redis-server
        
        # Configure Redis to start on boot
        sudo systemctl enable redis-server
        sudo systemctl start redis-server
        
        if redis-cli ping &> /dev/null; then
            echo -e "   ${GREEN}✅ Redis installed and running${NC}"
        else
            echo -e "   ${RED}❌ Redis installation failed${NC}"
        fi
    else
        echo -e "   ${YELLOW}⚠️  Skipping Redis installation${NC}"
        echo -e "   ${CYAN}App will work without caching (slower AI suggestions)${NC}"
    fi
fi

# Run database migrations
echo -e "\n${YELLOW}5️⃣  Running database migrations...${NC}"
if python migrate.py create 2>&1 | grep -q "already exists\|created successfully"; then
    echo -e "   ${GREEN}✅ Database tables created successfully${NC}"
else
    echo -e "   ${YELLOW}⚠️  Migration completed with warnings${NC}"
fi

# Test database connection
echo -e "\n${YELLOW}6️⃣  Testing database connection...${NC}"
if python -c "from src.database import get_db; next(get_db()); print('OK')" 2>&1 | grep -q "OK"; then
    echo -e "   ${GREEN}✅ Database connection successful${NC}"
else
    echo -e "   ${RED}❌ Database connection failed${NC}"
    echo -e "   ${CYAN}Check your .env file DATABASE_URL setting${NC}"
fi

# Test Redis cache
echo -e "\n${YELLOW}7️⃣  Testing Redis cache...${NC}"
CACHE_STATUS=$(python -c "from src.services.cache_service import get_cache_service; cache = get_cache_service(); print('OK' if cache.enabled else 'DISABLED')" 2>&1)
if echo "$CACHE_STATUS" | grep -q "OK"; then
    echo -e "   ${GREEN}✅ Redis cache connected and enabled ⚡${NC}"
elif echo "$CACHE_STATUS" | grep -q "DISABLED"; then
    echo -e "   ${YELLOW}⚠️  Redis cache disabled (install Redis for faster performance)${NC}"
else
    echo -e "   ${RED}❌ Cache test error${NC}"
fi

# Display setup summary
echo -e "\n${CYAN}📊 Setup Summary${NC}"
echo -e "${CYAN}================${NC}\n"

# Get cache stats
echo -e "${YELLOW}Cache Statistics:${NC}"
python -c "from src.services.cache_service import get_cache_service; import json; cache = get_cache_service(); print(json.dumps(cache.get_stats(), indent=2))" 2>&1 || echo "Cache unavailable"

# Count database tables
echo -e "\n${YELLOW}Database Tables:${NC}"
if [ -z "$POSTGRES_PASSWORD" ]; then
    export PGPASSWORD="niknotes_pass"
else
    export PGPASSWORD="$POSTGRES_PASSWORD"
fi
psql -U niknotes_user -d niknotes_db -h localhost -c "\dt" 2>&1 || echo "Database unavailable"

# Display next steps
echo -e "\n${GREEN}✅ Setup Complete!${NC}"
echo -e "\n${CYAN}🚀 Next Steps:${NC}"
echo -e "   1. Start the web app: ${GREEN}python web_app.py${NC}"
echo -e "   2. Open browser: ${GREEN}http://localhost:5000${NC}"
echo -e "   3. Create a trip and test AI suggestions"
echo -e "   4. Watch console for cache performance (${CYAN}🚀 Cache HIT${NC} messages)"

echo -e "\n${CYAN}📚 Documentation:${NC}"
echo -e "   - Performance guide: ${GREEN}PERFORMANCE_SETUP.md${NC}"
echo -e "   - AI configuration: ${GREEN}GEMINI_SETUP.md${NC}"
echo -e "   - Database guide: ${GREEN}DATABASE.md${NC}"
echo -e "   - Web interface: ${GREEN}WEB_INTERFACE.md${NC}"

echo -e "\n${CYAN}💡 System Service Setup (Optional):${NC}"
echo -e "   To ensure PostgreSQL and Redis start on boot:"
echo -e "   ${GREEN}sudo systemctl enable postgresql${NC}"
echo -e "   ${GREEN}sudo systemctl enable redis-server${NC}"

echo -e "\n${CYAN}🔧 Troubleshooting:${NC}"
echo -e "   PostgreSQL: ${GREEN}sudo systemctl status postgresql${NC}"
echo -e "   Redis: ${GREEN}sudo systemctl status redis-server${NC}"
echo -e "   Logs: ${GREEN}sudo journalctl -u postgresql${NC}"
echo ""
