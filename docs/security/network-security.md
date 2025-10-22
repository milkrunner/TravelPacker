# 🌐 Network Access Configuration

## Overview

NikNotes is configured to be accessible from all network interfaces, allowing you to access the web application from:

- **Localhost**: `http://localhost:5000`
- **Local IP**: `http://YOUR_LOCAL_IP:5000`
- **Other devices**: Access from phones, tablets, other computers on your network

## 🚀 Quick Start

### Find Your Local IP Address

**Windows:**

```powershell
# Get your local IP address
ipconfig | Select-String "IPv4"

# Or get it directly
(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi" | Select-Object IPAddress).IPAddress
```

**Linux/Mac:**

```bash
# Get your local IP address
hostname -I | awk '{print $1}'

# Or use ip command (Linux)
ip addr show | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1
```

### Start the Application

```powershell
# Start the web app (binds to 0.0.0.0:5000)
python web_app.py
```

You'll see:

```text
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.XXX:5000
```

### Access from Different Devices

1. **From the same computer:**

   - `http://localhost:5000`
   - `http://127.0.0.1:5000`

2. **From another device on the network:**

   - `http://YOUR_LOCAL_IP:5000`
   - Example: `http://192.168.1.100:5000`

3. **From mobile phone/tablet:**
   - Connect to the same Wi-Fi network
   - Open browser and go to `http://YOUR_LOCAL_IP:5000`

## 🐳 Docker Deployment

Docker containers are already configured to listen on all interfaces:

```bash
# Start with Docker Compose
docker-compose up -d

# Access the app
# Local: http://localhost:5000
# Network: http://YOUR_LOCAL_IP:5000
```

The `docker-compose.yml` maps port 5000 from the container to your host, making it accessible on all network interfaces.

## 🔒 Security Considerations

### Development Mode (Current Setup)

✅ **Suitable for:**

- Local development
- Testing on local network
- Demo to colleagues on same network

⚠️ **Not suitable for:**

- Production deployment
- Public internet exposure
- Untrusted networks

### Development vs Production

**Current Configuration (Development):**

```python
app.run(host='0.0.0.0', debug=True, port=5000)
```

**Production Configuration:**
Use a production WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

## 🛡️ Firewall Configuration

### Windows Firewall

If you can't access from other devices, check Windows Firewall:

```powershell
# Check if port 5000 is allowed
Get-NetFirewallRule -DisplayName "*5000*"

# Allow port 5000 (run as Administrator)
New-NetFirewallRule -DisplayName "Flask Dev Server" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow

# Or allow Python through firewall
New-NetFirewallRule -DisplayName "Python Flask" -Direction Inbound -Program "C:\Path\To\Python\python.exe" -Action Allow
```

### Linux Firewall (UFW)

```bash
# Allow port 5000
sudo ufw allow 5000/tcp

# Check status
sudo ufw status
```

### macOS Firewall

1. Open **System Preferences** → **Security & Privacy** → **Firewall**
2. Click **Firewall Options**
3. Add Python to allowed apps

## 📱 Mobile Testing

### Same Wi-Fi Network

1. **Connect mobile device** to same Wi-Fi as development machine
2. **Find your local IP** (see above)
3. **Open mobile browser** and navigate to `http://YOUR_LOCAL_IP:5000`

### QR Code Access

Generate a QR code for easy mobile access:

```powershell
# Install qrcode library
pip install qrcode[pil]

# Generate QR code (Python)
python -c "import qrcode; import socket; ip = socket.gethostbyname(socket.gethostname()); qr = qrcode.QRCode(); qr.add_data(f'http://{ip}:5000'); qr.make(); qr.print_ascii()"
```

## 🔧 Troubleshooting

### Cannot Access from Other Devices

**1. Check if app is running on 0.0.0.0:**

```text
 * Running on all addresses (0.0.0.0)  ← Should see this
```

**2. Verify firewall is not blocking:**

```powershell
# Windows: Test port 5000
Test-NetConnection -ComputerName localhost -Port 5000

# Linux: Check if port is listening
netstat -tuln | grep 5000
```

**3. Confirm both devices on same network:**

```powershell
# Get your network info
ipconfig /all  # Windows
ip addr show   # Linux
```

**4. Try different browser on mobile:**

- Some browsers cache DNS/network settings
- Try Chrome, Firefox, Safari

### App Shows "Running on 127.0.0.1" Only

If you see:

```text
 * Running on http://127.0.0.1:5000
```

**Fix:** Update `web_app.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)  # ← Must have host='0.0.0.0'
```

### Connection Refused

**Possible causes:**

1. App not running
2. Firewall blocking port 5000
3. Wrong IP address
4. Different network (mobile on cellular, computer on Wi-Fi)

**Solutions:**

```powershell
# 1. Verify app is running
ps | Select-String "python.*web_app"

# 2. Check firewall (see Firewall Configuration above)

# 3. Double-check IP address
ipconfig | Select-String "IPv4"

# 4. Ensure both devices on same Wi-Fi
```

## 🌍 External Access (Advanced)

### Using ngrok (for demos/testing)

```bash
# Install ngrok
choco install ngrok  # Windows
brew install ngrok   # Mac
# Or download from https://ngrok.com

# Start Flask app
python web_app.py

# In another terminal, create tunnel
ngrok http 5000

# You'll get a public URL like:
# https://abc123.ngrok.io → http://localhost:5000
```

**Use cases:**

- Demo to remote clients
- Test webhooks
- Share with team members remotely

⚠️ **Warning:** This exposes your local app to the internet. Only use for testing!

### Using Tailscale/ZeroTier (secure option)

Create a private network that works anywhere:

**Tailscale** (recommended):

```bash
# Install Tailscale on both devices
# Windows: https://tailscale.com/download
# Mobile: App Store / Play Store

# Both devices join your Tailscale network
# Access using Tailscale IP: http://100.x.x.x:5000
```

## 📊 Network Configuration Summary

| Access Method | URL Pattern               | Use Case                |
| ------------- | ------------------------- | ----------------------- |
| **Localhost** | `http://localhost:5000`   | Same machine            |
| **Local IP**  | `http://192.168.1.X:5000` | Local network           |
| **Docker**    | `http://localhost:5000`   | Container deployment    |
| **ngrok**     | `https://xyz.ngrok.io`    | Temporary public access |
| **Tailscale** | `http://100.x.x.x:5000`   | Secure remote access    |

## ✅ Configuration Checklist

- [x] `web_app.py` uses `host='0.0.0.0'`
- [x] Dockerfile runs Flask on `0.0.0.0`
- [x] Port 5000 exposed in Docker
- [ ] Firewall allows port 5000 (if needed)
- [ ] Both devices on same network (for local access)
- [ ] HTTPS/Authentication for production (when deploying)

## 📖 Related Documentation

- [Quick Reference](QUICK_REFERENCE.md) - Command cheat sheet
- [Docker Deployment](DOCKER_DEPLOYMENT.md) - Production deployment
- [Performance Setup](PERFORMANCE_SETUP.md) - Optimization guide

---

**🎉 Enjoy testing NikNotes on all your devices!**
