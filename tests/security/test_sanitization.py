"""
Tests for Content Sanitization Service

Tests XSS prevention, HTML filtering, and input sanitization.
"""

import pytest
from src.services.sanitization_service import ContentSanitizer


class TestStrictSanitization:
    """Test strict sanitization (no HTML allowed)"""
    
    def test_remove_script_tags(self):
        """Test that script tags are removed"""
        malicious = '<script>alert("XSS")</script>Hello'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<script>' not in result
        # Bleach strips tags but preserves text content
        assert result == 'alert("XSS")Hello'
    
    def test_remove_img_tags(self):
        """Test that img tags are removed"""
        malicious = '<img src=x onerror="alert(1)">Test'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<img' not in result
        assert 'onerror' not in result
        assert result == 'Test'
    
    def test_remove_all_html_tags(self):
        """Test that all HTML tags are removed in strict mode"""
        html = '<b>Bold</b> <i>Italic</i> <a href="#">Link</a>'
        result = ContentSanitizer.sanitize_strict(html)
        assert '<b>' not in result
        assert '<i>' not in result
        assert '<a>' not in result
        assert result == 'Bold Italic Link'
    
    def test_remove_event_handlers(self):
        """Test that event handlers are removed"""
        malicious = '<div onclick="alert(1)">Click me</div>'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert 'onclick' not in result
        assert '<div>' not in result
        assert result == 'Click me'
    
    def test_plain_text_unchanged(self):
        """Test that plain text passes through unchanged"""
        text = 'This is plain text with no HTML'
        result = ContentSanitizer.sanitize_strict(text)
        assert result == text
    
    def test_empty_string(self):
        """Test empty string handling"""
        assert ContentSanitizer.sanitize_strict('') == ''
        assert ContentSanitizer.sanitize_strict(None) == ''
    
    def test_whitespace_trimmed(self):
        """Test that leading/trailing whitespace is trimmed"""
        text = '  Hello World  '
        result = ContentSanitizer.sanitize_strict(text)
        assert result == 'Hello World'
    
    def test_javascript_protocol(self):
        """Test that javascript: protocol is blocked"""
        malicious = '<a href="javascript:alert(1)">Click</a>'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert 'javascript:' not in result
        assert '<a' not in result
    
    def test_data_uri_blocked(self):
        """Test that data URIs are handled safely"""
        malicious = '<img src="data:text/html,<script>alert(1)</script>">'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<img' not in result
        assert '<script>' not in result


class TestBasicSanitization:
    """Test basic sanitization (simple formatting allowed)"""
    
    def test_allow_basic_formatting(self):
        """Test that basic formatting tags are allowed"""
        html = '<b>Bold</b> <i>Italic</i> <em>Emphasis</em> <strong>Strong</strong>'
        result = ContentSanitizer.sanitize_basic(html)
        assert '<b>Bold</b>' in result
        assert '<i>Italic</i>' in result
        assert '<em>Emphasis</em>' in result
        assert '<strong>Strong</strong>' in result
    
    def test_remove_script_in_basic(self):
        """Test that scripts are still removed in basic mode"""
        malicious = '<b>Bold</b><script>alert(1)</script>'
        result = ContentSanitizer.sanitize_basic(malicious)
        assert '<b>Bold</b>' in result
        assert '<script>' not in result
        # Text content from script tags remains
        assert result == '<b>Bold</b>alert(1)'
    
    def test_remove_links_in_basic(self):
        """Test that links are removed in basic mode"""
        html = '<b>Bold</b> <a href="#">Link</a>'
        result = ContentSanitizer.sanitize_basic(html)
        assert '<b>Bold</b>' in result
        assert '<a' not in result
        assert 'Link' in result
    
    def test_allow_br_tags(self):
        """Test that line breaks are allowed"""
        html = 'Line 1<br>Line 2'
        result = ContentSanitizer.sanitize_basic(html)
        assert '<br' in result or '<br>' in result


class TestStandardSanitization:
    """Test standard sanitization (formatting and lists)"""
    
    def test_allow_paragraphs(self):
        """Test that paragraphs are allowed"""
        html = '<p>Paragraph 1</p><p>Paragraph 2</p>'
        result = ContentSanitizer.sanitize_standard(html)
        assert '<p>Paragraph 1</p>' in result
        assert '<p>Paragraph 2</p>' in result
    
    def test_allow_lists(self):
        """Test that lists are allowed"""
        html = '<ul><li>Item 1</li><li>Item 2</li></ul>'
        result = ContentSanitizer.sanitize_standard(html)
        assert '<ul>' in result
        assert '<li>Item 1</li>' in result
        assert '<li>Item 2</li>' in result
    
    def test_allow_ordered_lists(self):
        """Test that ordered lists are allowed"""
        html = '<ol><li>First</li><li>Second</li></ol>'
        result = ContentSanitizer.sanitize_standard(html)
        assert '<ol>' in result
        assert '<li>First</li>' in result
    
    def test_remove_scripts_in_standard(self):
        """Test that scripts are removed in standard mode"""
        malicious = '<p>Text</p><script>alert(1)</script>'
        result = ContentSanitizer.sanitize_standard(malicious)
        assert '<p>Text</p>' in result
        assert '<script>' not in result


class TestRichSanitization:
    """Test rich sanitization (full formatting with links)"""
    
    def test_allow_safe_links(self):
        """Test that safe links are allowed"""
        html = '<a href="https://example.com">Safe Link</a>'
        result = ContentSanitizer.sanitize_rich(html)
        assert '<a href="https://example.com">Safe Link</a>' in result
    
    def test_block_javascript_links(self):
        """Test that javascript: links are blocked"""
        malicious = '<a href="javascript:alert(1)">Bad Link</a>'
        result = ContentSanitizer.sanitize_rich(malicious)
        assert 'javascript:' not in result
        # Link should be stripped but text preserved
        assert 'Bad Link' in result
    
    def test_allow_mailto_links(self):
        """Test that mailto links are allowed"""
        html = '<a href="mailto:test@example.com">Email</a>'
        result = ContentSanitizer.sanitize_rich(html)
        assert 'mailto:test@example.com' in result
    
    def test_allow_title_attribute(self):
        """Test that title attribute on links is allowed"""
        html = '<a href="https://example.com" title="Example">Link</a>'
        result = ContentSanitizer.sanitize_rich(html)
        assert 'title="Example"' in result
    
    def test_remove_onclick_from_links(self):
        """Test that onclick is removed from links"""
        malicious = '<a href="https://example.com" onclick="alert(1)">Link</a>'
        result = ContentSanitizer.sanitize_rich(malicious)
        assert 'onclick' not in result
        assert 'href="https://example.com"' in result
    
    def test_allow_span_with_class(self):
        """Test that span with class is allowed"""
        html = '<span class="highlight">Important</span>'
        result = ContentSanitizer.sanitize_rich(html)
        assert '<span class="highlight">Important</span>' in result


class TestEmailSanitization:
    """Test email sanitization"""
    
    def test_valid_email(self):
        """Test valid email is accepted"""
        email = 'user@example.com'
        result = ContentSanitizer.sanitize_email(email)
        assert result == 'user@example.com'
    
    def test_email_lowercase(self):
        """Test email is converted to lowercase"""
        email = 'User@EXAMPLE.COM'
        result = ContentSanitizer.sanitize_email(email)
        assert result == 'user@example.com'
    
    def test_email_whitespace_trimmed(self):
        """Test email whitespace is trimmed"""
        email = '  user@example.com  '
        result = ContentSanitizer.sanitize_email(email)
        assert result == 'user@example.com'
    
    def test_email_with_html_removed(self):
        """Test HTML is removed from email"""
        malicious = '<script>alert(1)</script>user@example.com'
        result = ContentSanitizer.sanitize_email(malicious)
        assert '<script>' not in result
        # Script tags stripped but text content remains
        assert result == 'alert(1)user@example.com'
    
    def test_invalid_email_no_at(self):
        """Test invalid email without @ returns empty"""
        invalid = 'notanemail'
        result = ContentSanitizer.sanitize_email(invalid)
        assert result == ''
    
    def test_invalid_email_nothing_before_at(self):
        """Test invalid email with nothing before @ returns empty"""
        invalid = '@example.com'
        result = ContentSanitizer.sanitize_email(invalid)
        assert result == ''
    
    def test_invalid_email_nothing_after_at(self):
        """Test invalid email with nothing after @ returns empty"""
        invalid = 'user@'
        result = ContentSanitizer.sanitize_email(invalid)
        assert result == ''
    
    def test_empty_email(self):
        """Test empty email handling"""
        assert ContentSanitizer.sanitize_email('') == ''
        assert ContentSanitizer.sanitize_email(None) == ''


class TestURLSanitization:
    """Test URL sanitization"""
    
    def test_valid_http_url(self):
        """Test valid HTTP URL is accepted"""
        url = 'http://example.com'
        result = ContentSanitizer.sanitize_url(url)
        assert result == 'http://example.com'
    
    def test_valid_https_url(self):
        """Test valid HTTPS URL is accepted"""
        url = 'https://example.com/path'
        result = ContentSanitizer.sanitize_url(url)
        assert result == 'https://example.com/path'
    
    def test_valid_mailto_url(self):
        """Test valid mailto URL is accepted"""
        url = 'mailto:user@example.com'
        result = ContentSanitizer.sanitize_url(url)
        assert result == 'mailto:user@example.com'
    
    def test_javascript_protocol_blocked(self):
        """Test javascript: protocol is blocked"""
        malicious = 'javascript:alert(1)'
        result = ContentSanitizer.sanitize_url(malicious)
        assert result == ''
    
    def test_data_protocol_blocked(self):
        """Test data: protocol is blocked"""
        malicious = 'data:text/html,<script>alert(1)</script>'
        result = ContentSanitizer.sanitize_url(malicious)
        assert result == ''
    
    def test_url_whitespace_trimmed(self):
        """Test URL whitespace is trimmed"""
        url = '  https://example.com  '
        result = ContentSanitizer.sanitize_url(url)
        assert result == 'https://example.com'
    
    def test_empty_url(self):
        """Test empty URL handling"""
        assert ContentSanitizer.sanitize_url('') == ''
        assert ContentSanitizer.sanitize_url(None) == ''


class TestTripDataSanitization:
    """Test trip data sanitization"""
    
    def test_sanitize_destination(self):
        """Test destination is sanitized strictly"""
        data = {
            'destination': '<script>alert(1)</script>Paris',
            'start_date': '2024-01-01',
            'end_date': '2024-01-07'
        }
        result = ContentSanitizer.sanitize_trip_data(data)
        # Tags removed but text content remains
        assert result['destination'] == 'alert(1)Paris'
        assert '<script>' not in result['destination']
    
    def test_sanitize_special_notes(self):
        """Test special notes allow rich formatting"""
        data = {
            'destination': 'Paris',
            'special_notes': '<b>Important:</b> <a href="https://example.com">Check this</a>'
        }
        result = ContentSanitizer.sanitize_trip_data(data)
        assert '<b>Important:</b>' in result['special_notes']
        assert 'href="https://example.com"' in result['special_notes']
    
    def test_sanitize_special_notes_removes_scripts(self):
        """Test special notes remove scripts"""
        data = {
            'destination': 'Paris',
            'special_notes': 'Note <script>alert(1)</script> here'
        }
        result = ContentSanitizer.sanitize_trip_data(data)
        assert '<script>' not in result['special_notes']
        # Text content remains after tags stripped
        assert result['special_notes'] == 'Note alert(1) here'
    
    def test_sanitize_travelers_list(self):
        """Test travelers are sanitized strictly"""
        data = {
            'destination': 'Paris',
            'travelers': ['<b>John</b>', '<script>alert(1)</script>Jane', 'Bob']
        }
        result = ContentSanitizer.sanitize_trip_data(data)
        # Tags removed but text content remains
        assert result['travelers'] == ['John', 'alert(1)Jane', 'Bob']
    
    def test_sanitize_activities_list(self):
        """Test activities allow standard formatting"""
        data = {
            'destination': 'Paris',
            'activities': ['<b>Sightseeing</b>', '<script>alert(1)</script>Dining']
        }
        result = ContentSanitizer.sanitize_trip_data(data)
        # Standard sanitization allows <b> tags
        assert '<b>Sightseeing</b>' in result['activities'][0]
        assert '<script>' not in result['activities'][1]
    
    def test_sanitize_template_name(self):
        """Test template name allows basic formatting"""
        data = {
            'destination': 'Paris',
            'template_name': '<b>Summer</b> <script>alert(1)</script>Trip'
        }
        result = ContentSanitizer.sanitize_trip_data(data)
        assert '<b>Summer</b>' in result['template_name']
        assert '<script>' not in result['template_name']
    
    def test_passthrough_fields_unchanged(self):
        """Test non-text fields pass through unchanged"""
        data = {
            'destination': 'Paris',
            'start_date': '2024-01-01',
            'end_date': '2024-01-07',
            'duration': 7,
            'travel_style': 'leisure',
            'transportation': 'flight'
        }
        result = ContentSanitizer.sanitize_trip_data(data)
        assert result['start_date'] == '2024-01-01'
        assert result['end_date'] == '2024-01-07'
        assert result['duration'] == 7
        assert result['travel_style'] == 'leisure'
        assert result['transportation'] == 'flight'


class TestItemDataSanitization:
    """Test packing item data sanitization"""
    
    def test_sanitize_item_name(self):
        """Test item name is sanitized strictly"""
        data = {
            'name': '<script>alert(1)</script>Passport',
            'category': 'documents'
        }
        result = ContentSanitizer.sanitize_item_data(data)
        # Tags removed but text content remains
        assert result['name'] == 'alert(1)Passport'
        assert '<script>' not in result['name']
    
    def test_sanitize_item_notes(self):
        """Test item notes allow rich formatting"""
        data = {
            'name': 'Passport',
            'notes': '<b>Keep safe!</b> <a href="https://embassy.com">Embassy link</a>'
        }
        result = ContentSanitizer.sanitize_item_data(data)
        assert '<b>Keep safe!</b>' in result['notes']
        assert 'href="https://embassy.com"' in result['notes']
    
    def test_sanitize_item_notes_removes_scripts(self):
        """Test item notes remove scripts"""
        data = {
            'name': 'Passport',
            'notes': 'Note <script>alert(1)</script> here'
        }
        result = ContentSanitizer.sanitize_item_data(data)
        assert '<script>' not in result['notes']
    
    def test_passthrough_item_fields(self):
        """Test non-text item fields pass through"""
        data = {
            'name': 'Passport',
            'category': 'documents',
            'quantity': 1,
            'is_packed': False,
            'is_essential': True
        }
        result = ContentSanitizer.sanitize_item_data(data)
        assert result['category'] == 'documents'
        assert result['quantity'] == 1
        assert result['is_packed'] is False
        assert result['is_essential'] is True


class TestXSSAttackVectors:
    """Test various XSS attack vectors are blocked"""
    
    def test_svg_xss(self):
        """Test SVG-based XSS is blocked"""
        malicious = '<svg onload="alert(1)">'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<svg' not in result
        assert 'onload' not in result
    
    def test_iframe_injection(self):
        """Test iframe injection is blocked"""
        malicious = '<iframe src="javascript:alert(1)"></iframe>'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<iframe' not in result
        assert 'javascript:' not in result
    
    def test_object_tag_blocked(self):
        """Test object tag is blocked"""
        malicious = '<object data="javascript:alert(1)"></object>'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<object' not in result
    
    def test_embed_tag_blocked(self):
        """Test embed tag is blocked"""
        malicious = '<embed src="javascript:alert(1)">'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<embed' not in result
    
    def test_form_injection(self):
        """Test form injection is blocked"""
        malicious = '<form action="https://evil.com"><input name="password"></form>'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<form' not in result
        assert '<input' not in result
    
    def test_style_tag_blocked(self):
        """Test style tag is blocked"""
        malicious = '<style>body { background: url("javascript:alert(1)") }</style>'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<style' not in result
    
    def test_meta_refresh_blocked(self):
        """Test meta refresh is blocked"""
        malicious = '<meta http-equiv="refresh" content="0;url=javascript:alert(1)">'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<meta' not in result
    
    def test_base_tag_blocked(self):
        """Test base tag is blocked"""
        malicious = '<base href="javascript:alert(1)">'
        result = ContentSanitizer.sanitize_strict(malicious)
        assert '<base' not in result


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_unicode_handling(self):
        """Test Unicode characters are preserved"""
        text = 'Café ☕ München 🇩🇪 naïve'
        result = ContentSanitizer.sanitize_strict(text)
        assert result == text
    
    def test_numbers_and_symbols(self):
        """Test numbers and symbols are preserved (with HTML encoding)"""
        text = '1234567890 !@#$%^&*()-_=+[]{}|;:,.<>?'
        result = ContentSanitizer.sanitize_strict(text)
        # Bleach HTML-encodes special characters
        assert '1234567890' in result
        assert '&amp;' in result  # & becomes &amp;
        assert '&lt;' in result   # < becomes &lt;
        assert '&gt;' in result   # > becomes &gt;
    
    def test_newlines_preserved(self):
        """Test newlines are preserved"""
        text = 'Line 1\nLine 2\nLine 3'
        result = ContentSanitizer.sanitize_strict(text)
        assert '\n' in result
    
    def test_very_long_input(self):
        """Test very long input is handled"""
        long_text = 'A' * 10000
        result = ContentSanitizer.sanitize_strict(long_text)
        assert len(result) == 10000
    
    def test_nested_html_tags(self):
        """Test deeply nested HTML is cleaned"""
        nested = '<div><div><div><script>alert(1)</script></div></div></div>'
        result = ContentSanitizer.sanitize_strict(nested)
        assert '<script>' not in result
        assert '<div>' not in result
    
    def test_malformed_html(self):
        """Test malformed HTML doesn't break sanitization"""
        malformed = '<b>Bold<i>Italic</b></i>'
        result = ContentSanitizer.sanitize_strict(malformed)
        # Should still remove all tags
        assert '<b>' not in result
        assert '<i>' not in result
        assert 'BoldItalic' in result
