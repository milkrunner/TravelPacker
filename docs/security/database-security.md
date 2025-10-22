# Database Security Guide

## Overview

This guide covers secure management of database credentials for NikNotes, implementing best practices to protect against unauthorized access.

## Security Improvements Implemented

### ✅ 1. Environment Variable Configuration

All database credentials are now managed through environment variables instead of hard-coded values.

#### Docker Compose Configuration

```yaml
# docker-compose.yml
environment:
  POSTGRES_DB: ${POSTGRES_DB:-niknotes_db}
  POSTGRES_USER: ${POSTGRES_USER:-niknotes_user}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD environment variable is required}
```

**Key Features:**

- `${POSTGRES_PASSWORD:?...}` - **REQUIRED**: Deployment fails if not set
- `${POSTGRES_USER:-niknotes_user}` - **OPTIONAL**: Uses default if not set
- Prevents accidental deployment with missing credentials

### ✅ 2. Localhost-Only Port Binding

Database ports are now bound to localhost only, preventing external network access:

```yaml
# PostgreSQL
ports:
  - "127.0.0.1:5432:5432"  # Only accessible from localhost

# Redis
ports:
  - "127.0.0.1:6379:6379"  # Only accessible from localhost
```

**Security Benefits:**

- Blocks direct database access from external networks
- Prevents port scanning and brute force attacks
- Requires SSH tunnel or VPN for remote access

### ✅ 3. Secure Example Files

The `.env.example` file no longer contains default passwords:

```bash
# .env.example
POSTGRES_PASSWORD=CHANGE_ME_TO_A_SECURE_PASSWORD  # Not a real password
```

### ✅ 4. Setup Scripts Updated

All setup scripts now read passwords from environment variables:

```powershell
# PowerShell
if (-not $env:POSTGRES_PASSWORD) {
    Write-Host "⚠️  POSTGRES_PASSWORD not set. Using default (change this!)"
    $env:PGPASSWORD = "niknotes_pass"
} else {
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD
}
```

```bash
# Bash
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "⚠️  POSTGRES_PASSWORD not set. Using default (change this!)"
    export PGPASSWORD="niknotes_pass"
else
    export PGPASSWORD="$POSTGRES_PASSWORD"
fi
```

## Configuration Guide

### Development Setup

1. **Copy the example environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Set strong database credentials in `.env`:**

   ```bash
   # PostgreSQL Credentials
   POSTGRES_DB=niknotes_db
   POSTGRES_USER=niknotes_user
   POSTGRES_PASSWORD=your_strong_password_here  # CHANGE THIS!

   # Application Database URL
   DATABASE_URL=postgresql://niknotes_user:your_strong_password_here@localhost:5432/niknotes_db
   ```

3. **Generate a strong password:**

   ```bash
   # Linux/Mac
   openssl rand -base64 32

   # PowerShell
   -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})

   # Python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **Start Docker services:**

```bash
docker-compose up -d
```

### Production Deployment

#### Option 1: Environment Variables (Recommended)

Set environment variables before starting services:

```bash
# Linux/Mac
export POSTGRES_PASSWORD="your_production_password"
export POSTGRES_USER="niknotes_prod_user"
export POSTGRES_DB="niknotes_prod_db"
docker-compose up -d

# PowerShell
$env:POSTGRES_PASSWORD="your_production_password"
$env:POSTGRES_USER="niknotes_prod_user"
$env:POSTGRES_DB="niknotes_prod_db"
docker-compose up -d
```

#### Option 2: Docker Secrets (Production Best Practice)

For production environments, use Docker Swarm secrets:

```bash
# Create secrets
echo "your_strong_password" | docker secret create postgres_password -
echo "your_db_user" | docker secret create postgres_user -

# Update docker-compose.yml to use secrets
```

**docker-compose.prod.yml:**

```yaml
version: "3.8"
services:
  postgres:
    secrets:
      - postgres_password
      - postgres_user
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_USER_FILE: /run/secrets/postgres_user

secrets:
  postgres_password:
    external: true
  postgres_user:
    external: true
```

#### Option 3: HashiCorp Vault Integration

For enterprise deployments:

```bash
# Store credentials in Vault
vault kv put secret/niknotes/db \
  username=niknotes_user \
  password=your_strong_password

# Retrieve and set environment variables
export POSTGRES_PASSWORD=$(vault kv get -field=password secret/niknotes/db)
export POSTGRES_USER=$(vault kv get -field=username secret/niknotes/db)
```

## Security Best Practices

### Password Requirements

✅ **Minimum 20 characters** for production databases
✅ **Mix of uppercase, lowercase, numbers, symbols**
✅ **No dictionary words or common patterns**
✅ **Unique per environment** (dev, staging, production)

### Password Rotation

Rotate database passwords regularly:

```sql
-- Connect as superuser
ALTER USER niknotes_user WITH PASSWORD 'new_strong_password';

-- Update .env file with new password
-- Restart application
```

### Access Control

1. **Principle of Least Privilege:**

   ```sql
   -- Create read-only user for reporting
   CREATE USER niknotes_readonly WITH PASSWORD 'readonly_password';
   GRANT CONNECT ON DATABASE niknotes_db TO niknotes_readonly;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO niknotes_readonly;
   ```

1. **Restrict Network Access:**

```text
# postgresql.conf
listen_addresses = 'localhost'  # Only accept local connections

# pg_hba.conf
local   all   all                     peer
host    all   all   127.0.0.1/32     scram-sha-256
```

**Firewall Rules:**

```bash
# Only allow connections from application server
sudo ufw allow from 10.0.1.0/24 to any port 5432
```

### Encryption

1. **Enable SSL/TLS for PostgreSQL:**

   ```yaml
   # docker-compose.yml
   environment:
     POSTGRES_HOST_AUTH_METHOD: scram-sha-256
     POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
   ```

2. **Update connection string:**

   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```

### Monitoring & Auditing

1. **Enable PostgreSQL logging:**

   ```sql
   ALTER SYSTEM SET log_connections = 'on';
   ALTER SYSTEM SET log_disconnections = 'on';
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();
   ```

2. **Monitor failed login attempts:**

   ```bash
   # Check PostgreSQL logs
   docker logs niknotes-postgres | grep "authentication failed"
   ```

## Environment-Specific Configuration

### Development

```bash
# .env (development)
POSTGRES_PASSWORD=dev_password_123  # Simpler for local dev
DATABASE_URL=postgresql://niknotes_user:dev_password_123@localhost:5432/niknotes_db
```

### Staging

```bash
# .env.staging
POSTGRES_PASSWORD=${STAGING_DB_PASSWORD}  # From CI/CD secrets
DATABASE_URL=postgresql://${STAGING_DB_USER}:${STAGING_DB_PASSWORD}@staging-db:5432/niknotes_staging
```

### Production

```bash
# .env.production
POSTGRES_PASSWORD=${PROD_DB_PASSWORD}  # From secure vault
DATABASE_URL=postgresql://${PROD_DB_USER}:${PROD_DB_PASSWORD}@prod-db:5432/niknotes_prod
```

## Troubleshooting

### Issue: "POSTGRES_PASSWORD environment variable is required"

**Cause:** Starting Docker Compose without setting the password

**Solution:**

```bash
# Set password before starting
export POSTGRES_PASSWORD="your_password"
docker-compose up -d
```

### Issue: Can't connect from external network

**Cause:** Ports bound to localhost only (by design)

**Solution for testing:**

```yaml
# Temporarily change in docker-compose.yml (NOT FOR PRODUCTION!)
ports:
  - "0.0.0.0:5432:5432" # Allows external connections
```

**Solution for production:**

```bash
# Use SSH tunnel
ssh -L 5432:localhost:5432 user@server

# Or VPN access
# Configure your VPN to access internal network
```

### Issue: Password contains special characters causing issues

**Solution:**

```bash
# URL-encode special characters in DATABASE_URL
# Or use separate environment variables
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=niknotes_db
DATABASE_USER=niknotes_user
DATABASE_PASSWORD="pass!@#$word"  # Quoted for shell safety
```

## Migration from Hard-coded Passwords

If upgrading from an older version with hard-coded passwords:

1. **Stop all services:**

   ```bash
   docker-compose down
   ```

2. **Set new strong password:**

   ```bash
   export POSTGRES_PASSWORD="new_strong_password"
   ```

3. **Update existing database password:**

   ```bash
   docker-compose run postgres psql -U postgres -c \
     "ALTER USER niknotes_user WITH PASSWORD 'new_strong_password';"
   ```

4. **Update .env file with new password**

5. **Restart services:**

   ```bash
   docker-compose up -d
   ```

## Compliance & Standards

### OWASP Guidelines

✅ **A02:2021 - Cryptographic Failures:** Passwords encrypted in transit and at rest
✅ **A05:2021 - Security Misconfiguration:** No default credentials in production
✅ **A07:2021 - Identification and Authentication Failures:** Strong password requirements

### Industry Standards

- **PCI DSS:** Unique credentials per environment
- **HIPAA:** Encryption in transit, access logging
- **SOC 2:** Password rotation, audit logging

## Security Checklist

Before deploying to production:

- [ ] Strong, unique password set (minimum 20 characters)
- [ ] POSTGRES_PASSWORD environment variable configured
- [ ] No hard-coded passwords in code or config files
- [ ] Database ports bound to localhost only (or removed entirely)
- [ ] SSL/TLS enabled for database connections
- [ ] Firewall rules configured to restrict access
- [ ] PostgreSQL authentication set to scram-sha-256
- [ ] Connection logging enabled
- [ ] Regular password rotation scheduled
- [ ] Backup encryption configured
- [ ] Secrets stored in secure vault (not in git)
- [ ] .env file added to .gitignore

## Additional Resources

- **PostgreSQL Security:** <https://www.postgresql.org/docs/current/auth-methods.html>
- **Docker Secrets:** <https://docs.docker.com/engine/swarm/secrets/>
- **OWASP Database Security:** <https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html>

---

**Last Updated:** January 2025
**Version:** 1.1.0
**Status:** ✅ PRODUCTION READY
