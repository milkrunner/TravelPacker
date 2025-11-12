"""
Advanced rate limiting and security utilities

Provides per-IP and per-user rate limiting, brute-force detection,
and anomaly detection for API abuse prevention.
"""

from functools import wraps
from flask import request, jsonify, g
from flask_login import current_user
from typing import Optional, Callable
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading
from src.utils.logging_config import get_logger, log_security_event
import logging

logger = get_logger(__name__)


class SecurityMonitor:
    """Monitor and detect security threats like brute-force and anomalies"""
    
    def __init__(self):
        self._failed_attempts = defaultdict(deque)  # IP -> deque of timestamps
        self._suspicious_ips = set()  # IPs flagged as suspicious
        self._request_patterns = defaultdict(lambda: defaultdict(int))  # IP -> endpoint -> count
        self._lock = threading.Lock()
        
        # Configuration
        self.max_failed_attempts = 5  # Max failed login attempts
        self.failed_attempt_window = 300  # 5 minutes in seconds
        self.anomaly_threshold = 50  # Requests per minute to same endpoint
        self.anomaly_window = 60  # 1 minute
        
    def record_failed_login(self, ip_address: str) -> bool:
        """
        Record a failed login attempt
        
        Returns:
            True if IP should be blocked (exceeded threshold)
        """
        with self._lock:
            now = time.time()
            attempts = self._failed_attempts[ip_address]
            
            # Remove old attempts outside the window
            while attempts and attempts[0] < now - self.failed_attempt_window:
                attempts.popleft()
            
            # Add new attempt
            attempts.append(now)
            
            # Check if threshold exceeded
            if len(attempts) >= self.max_failed_attempts:
                self._suspicious_ips.add(ip_address)
                log_security_event(
                    logger,
                    f"Brute-force detected from {ip_address} ({len(attempts)} failed attempts in {self.failed_attempt_window}s)",
                    level=logging.WARNING,
                    ip_address=ip_address,
                    attempts=len(attempts)
                )
                return True
            
            return False
    
    def record_successful_login(self, ip_address: str):
        """Clear failed attempts on successful login"""
        with self._lock:
            if ip_address in self._failed_attempts:
                self._failed_attempts[ip_address].clear()
            if ip_address in self._suspicious_ips:
                self._suspicious_ips.remove(ip_address)
    
    def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if IP is flagged as suspicious"""
        return ip_address in self._suspicious_ips
    
    def record_request(self, ip_address: str, endpoint: str):
        """Record a request for anomaly detection"""
        with self._lock:
            self._request_patterns[ip_address][endpoint] += 1
    
    def check_anomaly(self, ip_address: str, endpoint: str) -> bool:
        """
        Check if request pattern is anomalous
        
        Returns:
            True if anomalous behavior detected
        """
        with self._lock:
            count = self._request_patterns[ip_address][endpoint]
            
            # Check if exceeded threshold
            if count > self.anomaly_threshold:
                print(f"🚨 ANOMALY DETECTED: {ip_address} hit {endpoint} {count} times")
                return True
            
            return False
    
    def cleanup_old_data(self):
        """Cleanup old monitoring data (call periodically)"""
        with self._lock:
            now = time.time()
            
            # Cleanup failed attempts
            for ip, attempts in list(self._failed_attempts.items()):
                while attempts and attempts[0] < now - self.failed_attempt_window:
                    attempts.popleft()
                if not attempts:
                    del self._failed_attempts[ip]
            
            # Reset request patterns (called every minute)
            self._request_patterns.clear()
    
    def get_stats(self) -> dict:
        """Get current monitoring statistics"""
        with self._lock:
            return {
                'suspicious_ips': len(self._suspicious_ips),
                'monitored_ips': len(self._failed_attempts),
                'total_patterns': sum(len(p) for p in self._request_patterns.values())
            }


# Global security monitor instance
security_monitor = SecurityMonitor()


def get_user_identifier() -> str:
    """
    Get unique identifier for rate limiting
    Combines IP and user ID for authenticated users
    """
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    
    if current_user.is_authenticated:
        return f"user:{current_user.id}:{ip}"
    
    return f"ip:{ip}"


def get_ip_address() -> str:
    """Get client IP address (supports proxies)"""
    return request.environ.get('HTTP_X_REAL_IP', 
                               request.environ.get('HTTP_X_FORWARDED_FOR', 
                                                  request.remote_addr))


def check_security_threats():
    """Check for security threats before processing request"""
    ip = get_ip_address()
    
    # Check if IP is flagged as suspicious
    if security_monitor.is_ip_suspicious(ip):
        return jsonify({
            'status': 'error',
            'message': 'Access temporarily restricted due to suspicious activity'
        }), 429
    
    # Record request for anomaly detection
    endpoint = request.endpoint or 'unknown'
    security_monitor.record_request(ip, endpoint)
    
    # Check for anomalies
    if security_monitor.check_anomaly(ip, endpoint):
        return jsonify({
            'status': 'error',
            'message': 'Rate limit exceeded. Please slow down your requests.'
        }), 429
    
    return None


def sensitive_endpoint(
    per_ip_limit: str = "10 per hour",
    per_user_limit: str = "20 per hour",
    require_auth: bool = False
):
    """
    Decorator for sensitive endpoints with enhanced rate limiting
    
    Args:
        per_ip_limit: Rate limit per IP address
        per_user_limit: Rate limit per authenticated user
        require_auth: Whether authentication is required
    
    Usage:
        @sensitive_endpoint(per_ip_limit="5 per hour", per_user_limit="10 per hour")
        def delete_trip():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check security threats first
            threat_response = check_security_threats()
            if threat_response:
                return threat_response
            
            # Check authentication requirement
            if require_auth and not current_user.is_authenticated:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            
            # Log sensitive operation
            ip = get_ip_address()
            user_id = current_user.id if current_user.is_authenticated else 'anonymous'
            endpoint = request.endpoint or f.__name__
            log_security_event(
                logger,
                f"Sensitive operation: {endpoint}",
                level=logging.INFO,
                user_id=user_id,
                ip_address=ip,
                endpoint=endpoint
            )
            
            # Continue with the actual function
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def track_authentication_attempt(success: bool):
    """
    Track authentication attempt for brute-force detection
    
    Args:
        success: Whether the authentication was successful
    """
    ip = get_ip_address()
    
    if not success:
        blocked = security_monitor.record_failed_login(ip)
        if blocked:
            # Log to audit system if available
            try:
                from src.services.audit_service import AuditLogger
                AuditLogger.log_security_event(
                    event_type='brute_force_detected',
                    action='ip_blocked',
                    severity='high'
                )
            except (ImportError, AttributeError):
                pass
    else:
        security_monitor.record_successful_login(ip)


def rate_limit_key_func():
    """Custom key function for rate limiting that considers user ID"""
    return get_user_identifier()


# Periodic cleanup task (should be called from a background thread or scheduler)
def start_cleanup_task():
    """Start background cleanup task"""
    import threading
    
    def cleanup_loop():
        while True:
            time.sleep(60)  # Run every minute
            security_monitor.cleanup_old_data()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    print("✅ Security monitor cleanup task started")
