# Authentication Quick Start Guide

## 🚀 Getting Started

### First Time Setup

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set your Flask secret key**:

   ```bash
   # Linux/Mac
   export FLASK_SECRET_KEY="your-secure-random-key-here"

   # Windows PowerShell
   $env:FLASK_SECRET_KEY="your-secure-random-key-here"

   # Windows CMD
   set FLASK_SECRET_KEY=your-secure-random-key-here
   ```

3. **Initialize database** (creates users and trips tables):

   ```bash
   python -c "from src.database import init_db; init_db()"
   ```

4. **Start the application**:

   ```bash
   python web_app.py
   ```

5. **Register your account**: Visit <http://localhost:5000/register>

### Migrating Existing Installation

If you already have a NikNotes database with trips:

1. **Backup your database**:

   ```bash
   cp niknotes.db niknotes.db.backup
   ```

2. **Install new dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run migration script**:

   ```bash
   python scripts/migrate_auth.py
   ```

4. **Start the application**:

   ```bash
   python web_app.py
   ```

5. **Login with default admin** (if created by migration):
   - Username: `admin`
   - Password: `changeme123`
   - ⚠️ **CHANGE THIS PASSWORD IMMEDIATELY**

## 👤 User Guide

### Creating an Account

1. Visit <http://localhost:5000/register>
2. Enter:
   - **Username** (3-50 characters, letters/numbers/underscores only)
   - **Email** (valid email address)
   - **Password** (minimum 8 characters)
   - **Confirm Password** (must match)
3. Click "Create Account"
4. You'll be logged in automatically

### Logging In

1. Visit <http://localhost:5000/login>
2. Enter your username and password
3. Optionally check "Remember me" for extended session
4. Click "Login"

### Logging Out

Click the "Logout" button in the navigation bar (top right)

### Accessing Your Trips

- All your trips are listed at <http://localhost:5000/>
- You can **only see and manage your own trips**
- Other users cannot access your trips
- Templates you create are private to your account

## 🔐 Security Features

### What's Protected

✅ **All routes require authentication** - You must be logged in  
✅ **Trip ownership** - You can only access your own trips  
✅ **Secure passwords** - Hashed with PBKDF2-SHA256  
✅ **Session security** - Secure cookies, auto-logout  
✅ **CSRF protection** - All forms protected against attacks

### Password Requirements

- Minimum **8 characters**
- No maximum length
- Can contain any characters
- Stored as secure hash (never plaintext)

### Best Practices

1. **Use a strong password**: Mix letters, numbers, symbols
2. **Don't share accounts**: Each user should have their own
3. **Log out on shared computers**: Click logout when done
4. **Change default admin password**: If using migrated database

## 🛠️ Troubleshooting

### "Please log in to access this page"

**Cause**: You're not logged in  
**Solution**: Go to `/login` or `/register`

### "Trip not found or access denied"

**Cause**: You're trying to access someone else's trip  
**Solution**: This is expected - you can only access your own trips

### Can't see my old trips after migration

**Cause**: Trips may be assigned to wrong user  
**Solution**:

1. Check if you logged in with the correct user
2. Run migration script again if needed
3. All existing trips are assigned to the default admin user

### Forgot password

**Current limitation**: Password reset not yet implemented  
**Workaround**: Admin must reset password via database script

### Migration script fails

**Cause**: Database locked or corrupted  
**Solution**:

1. Close all connections to niknotes.db
2. Restore from backup: `cp niknotes.db.backup niknotes.db`
3. Try migration again

## 📖 Additional Resources

- **Full Documentation**: `docs/AUTHENTICATION.md`
- **Implementation Details**: `docs/AUTHENTICATION_IMPLEMENTATION_SUMMARY.md`
- **Security Audit**: `SECURITY_AUDIT.md`
- **CSRF Protection**: `docs/CSRF_PROTECTION.md`

## 💡 Tips

### For Developers

- User object available as `current_user` in all templates
- Check authentication: `current_user.is_authenticated`
- Get user ID: `current_user.id`
- Get username: `current_user.username`

### For Users

- **One account per person**: Don't share login credentials
- **Remember me**: Use this on your personal devices only
- **Public computers**: Always log out when done
- **Multiple trips**: No limit - create as many as you need

## 🆘 Getting Help

### Common Questions

**Q: Do I need to create an account?**  
A: Yes, all users must register to use NikNotes now.

**Q: Can I use NikNotes without logging in?**  
A: No, authentication is required for all features.

**Q: Can other users see my trips?**  
A: No, your trips are private and only visible to you.

**Q: How do I change my password?**  
A: Password change feature coming soon. For now, contact admin.

**Q: Can I delete my account?**  
A: Account deletion feature coming soon.

**Q: Is my data secure?**  
A: Yes - passwords are hashed, sessions are secure, access is controlled.

### Error Messages

| Message                             | Meaning                    | Action                                 |
| ----------------------------------- | -------------------------- | -------------------------------------- |
| "Please log in to access this page" | Not authenticated          | Login or register                      |
| "Trip not found or access denied"   | Wrong user or missing trip | Check you're logged in as correct user |
| "Invalid username or password"      | Login failed               | Check credentials                      |
| "Username already taken"            | Registration conflict      | Choose different username              |
| "Email already registered"          | Registration conflict      | Use different email or login           |

## 🔄 What Changed

If you used NikNotes before authentication:

### Before (v1.0.0)

- ❌ No login required
- ❌ Anyone could access any trip
- ❌ No user accounts
- ❌ Single shared database

### After (v1.1.0)

- ✅ Login required for all features
- ✅ Users can only access their own trips
- ✅ Personal user accounts
- ✅ Multi-user support with isolation

## 📞 Support

For issues or questions:

1. Check this guide
2. Read `docs/AUTHENTICATION.md`
3. Check `SECURITY_AUDIT.md`
4. Review error messages
5. Contact your administrator

---

**NikNotes v1.1.0** - Secure Multi-User Trip Planning 🎒✨
