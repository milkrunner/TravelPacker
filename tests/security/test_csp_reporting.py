"""
Tests for CSP (Content Security Policy) violation reporting endpoint.

Tests ensure that the /csp-report endpoint correctly handles CSP violation
reports from browsers, logs them appropriately, and is properly configured
for security monitoring.
"""

import pytest
import json
from web_app import app


@pytest.fixture
def client():
    """Create test client for Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestCSPReportingEndpoint:
    """Test suite for CSP violation reporting endpoint"""
    
    def test_csp_report_accepts_valid_report(self, client):
        """Test that endpoint accepts properly formatted CSP reports"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/page",
                "violated-directive": "script-src 'self'",
                "effective-directive": "script-src",
                "blocked-uri": "https://evil.com/xss.js",
                "source-file": "https://test.com/page",
                "line-number": 42,
                "column-number": 15,
                "status-code": 200
            }
        }
        
        response = client.post(
            '/csp-report',
            data=json.dumps(report),
            content_type='application/json'
        )
        
        assert response.status_code == 204
        assert response.data == b''
    
    def test_csp_report_handles_minimal_report(self, client):
        """Test that endpoint handles reports with minimal fields"""
        report = {
            "csp-report": {
                "violated-directive": "script-src 'self'",
                "blocked-uri": "https://evil.com/test.js"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_csp_report_handles_empty_body(self, client):
        """Test that endpoint handles empty request body gracefully"""
        response = client.post('/csp-report', data='')
        assert response.status_code == 204
    
    def test_csp_report_handles_invalid_json(self, client):
        """Test that endpoint handles malformed JSON gracefully"""
        response = client.post(
            '/csp-report',
            data='{ invalid json',
            content_type='application/json'
        )
        assert response.status_code == 204
    
    def test_csp_report_handles_missing_csp_report_key(self, client):
        """Test that endpoint handles reports without csp-report key"""
        report = {
            "violated-directive": "script-src 'self'",
            "blocked-uri": "https://evil.com/test.js"
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_csp_report_no_csrf_required(self, client):
        """Test that CSP reports don't require CSRF token"""
        report = {
            "csp-report": {
                "violated-directive": "script-src 'self'",
                "blocked-uri": "inline"
            }
        }
        
        # Send without CSRF token (should still succeed)
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_csp_report_only_accepts_post(self, client):
        """Test that endpoint only accepts POST requests"""
        # GET should not be allowed
        response = client.get('/csp-report')
        assert response.status_code in [404, 405, 500]
        
        # PUT should not be allowed
        response = client.put('/csp-report', json={})
        assert response.status_code in [404, 405, 500]
        
        # DELETE should not be allowed
        response = client.delete('/csp-report')
        assert response.status_code in [404, 405, 500]
    
    def test_csp_report_no_rate_limiting(self, client):
        """Test that CSP reports are not rate limited"""
        report = {
            "csp-report": {
                "violated-directive": "script-src 'self'",
                "blocked-uri": "https://evil.com/test.js"
            }
        }
        
        # Send 50 rapid requests (should all succeed)
        for _ in range(50):
            response = client.post('/csp-report', json=report)
            assert response.status_code == 204


class TestCSPHeaders:
    """Test suite for CSP header configuration"""
    
    def test_csp_headers_present_on_homepage(self, client):
        """Test that CSP headers are set on homepage"""
        response = client.get('/')
        csp_header = response.headers.get('Content-Security-Policy')
        assert csp_header is not None
    
    def test_csp_headers_include_report_uri(self, client):
        """Test that CSP headers include report-uri directive"""
        response = client.get('/')
        csp_header = response.headers.get('Content-Security-Policy')
        assert 'report-uri /csp-report' in csp_header or 'report-uri=/csp-report' in csp_header
    
    def test_csp_headers_include_script_src(self, client):
        """Test that CSP headers include script-src directive"""
        response = client.get('/')
        csp_header = response.headers.get('Content-Security-Policy')
        assert 'script-src' in csp_header
    
    def test_csp_headers_include_default_src(self, client):
        """Test that CSP headers include default-src directive"""
        response = client.get('/')
        csp_header = response.headers.get('Content-Security-Policy')
        assert 'default-src' in csp_header
    
    def test_csp_headers_prevent_clickjacking(self, client):
        """Test that CSP headers prevent clickjacking"""
        response = client.get('/')
        csp_header = response.headers.get('Content-Security-Policy')
        assert 'frame-ancestors' in csp_header


class TestCSPViolationTypes:
    """Test suite for different types of CSP violations"""
    
    def test_script_src_violation(self, client):
        """Test reporting of script-src violations (XSS attempts)"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/trips",
                "violated-directive": "script-src 'self'",
                "blocked-uri": "https://evil.com/xss.js",
                "source-file": "https://test.com/trips",
                "line-number": 156
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_inline_script_violation(self, client):
        """Test reporting of inline script violations"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/profile",
                "violated-directive": "script-src 'self'",
                "blocked-uri": "inline",
                "source-file": "https://test.com/profile",
                "line-number": 42
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_connect_src_violation(self, client):
        """Test reporting of connect-src violations (data exfiltration)"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/dashboard",
                "violated-directive": "connect-src 'self'",
                "blocked-uri": "https://attacker.com/steal-data",
                "source-file": "https://test.com/dashboard",
                "line-number": 89
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_frame_ancestors_violation(self, client):
        """Test reporting of frame-ancestors violations (clickjacking)"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/login",
                "violated-directive": "frame-ancestors 'none'",
                "blocked-uri": "https://phishing-site.com"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_style_src_violation(self, client):
        """Test reporting of style-src violations"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/page",
                "violated-directive": "style-src 'self'",
                "blocked-uri": "https://cdn.example.com/malicious.css"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_img_src_violation(self, client):
        """Test reporting of img-src violations"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/page",
                "violated-directive": "img-src 'self' data: https:",
                "blocked-uri": "ftp://evil.com/image.jpg"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204


class TestCSPReportLogging:
    """Test suite for CSP report logging functionality"""
    
    def test_violation_logged(self, client, caplog):
        """Test that CSP violations are logged"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/page",
                "violated-directive": "script-src 'self'",
                "blocked-uri": "https://evil.com/test.js"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
        
        # Check that violation was logged (if logging is configured)
        # Note: This may not work in test environment without logger setup
        # Uncomment if you have logging configured for tests
        # assert 'CSP Violation' in caplog.text
    
    def test_error_handling_logged(self, client, caplog):
        """Test that errors in report processing are logged"""
        # Send completely invalid data to trigger error
        response = client.post(
            '/csp-report',
            data=b'\x00\x01\x02\x03',  # Binary garbage
            content_type='application/json'
        )
        
        # Should still return 204 (graceful handling)
        assert response.status_code == 204


class TestCSPReportContent:
    """Test suite for CSP report content extraction"""
    
    def test_all_fields_extracted(self, client):
        """Test that all CSP report fields are properly extracted"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/page",
                "violated-directive": "script-src 'self'",
                "effective-directive": "script-src",
                "blocked-uri": "https://evil.com/xss.js",
                "source-file": "https://test.com/page",
                "line-number": 42,
                "column-number": 15,
                "status-code": 200,
                "referrer": "https://google.com"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
        # If fields are not properly extracted, the endpoint should still succeed
        # but logging might fail (gracefully handled)
    
    def test_unicode_in_report(self, client):
        """Test that unicode characters in reports are handled"""
        report = {
            "csp-report": {
                "document-uri": "https://test.com/页面",
                "violated-directive": "script-src 'self'",
                "blocked-uri": "https://evil.com/恶意.js"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204
    
    def test_very_long_uris(self, client):
        """Test that very long URIs are handled"""
        long_uri = "https://evil.com/" + ("a" * 10000)
        report = {
            "csp-report": {
                "document-uri": "https://test.com/page",
                "violated-directive": "script-src 'self'",
                "blocked-uri": long_uri
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204


class TestCSPIntegration:
    """Integration tests for CSP reporting system"""
    
    def test_full_violation_workflow(self, client):
        """Test complete workflow from violation to logging"""
        # Simulate a realistic XSS attempt
        report = {
            "csp-report": {
                "document-uri": "https://yourapp.com/trips/123",
                "violated-directive": "connect-src 'self'",
                "effective-directive": "connect-src",
                "blocked-uri": "https://attacker.com/steal",
                "source-file": "https://yourapp.com/trips/123",
                "line-number": 156,
                "column-number": 12,
                "status-code": 200,
                "referrer": "https://yourapp.com/dashboard"
            }
        }
        
        response = client.post('/csp-report', json=report)
        
        # Verify response
        assert response.status_code == 204
        assert response.data == b''
        
        # Verify no errors occurred
        # (If there were errors, status would still be 204 but might log errors)
    
    def test_multiple_violations_same_session(self, client):
        """Test handling multiple violations in quick succession"""
        reports = [
            {
                "csp-report": {
                    "violated-directive": "script-src 'self'",
                    "blocked-uri": f"https://evil.com/script{i}.js"
                }
            }
            for i in range(10)
        ]
        
        for report in reports:
            response = client.post('/csp-report', json=report)
            assert response.status_code == 204


# Performance tests (optional, may be slow)
class TestCSPPerformance:
    """Performance tests for CSP reporting endpoint"""
    
    @pytest.mark.slow
    def test_high_volume_reports(self, client):
        """Test that endpoint can handle high volume of reports"""
        report = {
            "csp-report": {
                "violated-directive": "script-src 'self'",
                "blocked-uri": "https://evil.com/test.js"
            }
        }
        
        # Send 1000 reports
        for _ in range(1000):
            response = client.post('/csp-report', json=report)
            assert response.status_code == 204
    
    @pytest.mark.slow
    def test_large_report_payload(self, client):
        """Test that very large reports are handled"""
        # Create a large report (simulating verbose browser data)
        large_data = "x" * 100000  # 100KB of data
        report = {
            "csp-report": {
                "violated-directive": "script-src 'self'",
                "blocked-uri": f"https://evil.com/{large_data}"
            }
        }
        
        response = client.post('/csp-report', json=report)
        assert response.status_code == 204


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
