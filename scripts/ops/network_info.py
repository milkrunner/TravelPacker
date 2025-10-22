#!/usr/bin/env python3
"""
Network Information Display Script
Shows all the ways to access the NikNotes web application
"""

import socket
import sys


def get_local_ip():
    """Get the local IP address"""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None


def get_hostname():
    """Get the hostname"""
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def display_access_info(port=5000):
    """Display all access methods"""
    local_ip = get_local_ip()
    hostname = get_hostname()
    
    print("\n" + "="*60)
    print("🌐 NikNotes - Network Access Information")
    print("="*60 + "\n")
    
    print("📍 Your Computer:")
    print(f"   Hostname: {hostname}")
    if local_ip:
        print(f"   Local IP: {local_ip}")
    else:
        print("   Local IP: Could not determine (check network connection)")
    
    print("\n🔗 Access URLs:")
    print(f"   Localhost:     http://localhost:{port}")
    print(f"   127.0.0.1:     http://127.0.0.1:{port}")
    
    if local_ip:
        print(f"   Network:       http://{local_ip}:{port}")
        print(f"   Hostname:      http://{hostname}.local:{port}")
    
    print("\n📱 Mobile Access:")
    if local_ip:
        print(f"   1. Connect mobile to same Wi-Fi network")
        print(f"   2. Open browser and go to: http://{local_ip}:{port}")
        print(f"   3. Or scan this QR code (if available)")
    else:
        print("   Connect to Wi-Fi first, then run this script again")
    
    print("\n🔥 Firewall:")
    print(f"   Ensure port {port} is allowed through your firewall")
    
    if sys.platform == "win32":
        print("   Windows: Run as Admin:")
        print(f"   New-NetFirewallRule -DisplayName 'Flask Dev' -Direction Inbound -Protocol TCP -LocalPort {port} -Action Allow")
    elif sys.platform == "linux":
        print("   Linux:")
        print(f"   sudo ufw allow {port}/tcp")
    
    print("\n📚 Documentation:")
    print("   See docs/NETWORK_ACCESS.md for detailed instructions")
    
    print("\n" + "="*60 + "\n")


def generate_qr_code(url):
    """Generate QR code for the URL (optional)"""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        print("\n📲 Scan this QR code with your mobile device:")
        qr.print_ascii(invert=True)
        print()
    except ImportError:
        print("\n💡 Tip: Install 'qrcode' package to generate QR codes:")
        print("   pip install qrcode[pil]\n")


if __name__ == "__main__":
    port = 5000
    
    # Check for custom port argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python network_info.py [port]")
            print("Example: python network_info.py 5000")
            sys.exit(1)
    
    display_access_info(port)
    
    # Try to generate QR code
    local_ip = get_local_ip()
    if local_ip:
        url = f"http://{local_ip}:{port}"
        generate_qr_code(url)
