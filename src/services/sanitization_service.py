"""
Content Sanitization Service

Provides HTML/text sanitization to prevent XSS attacks in user-generated content.
Uses Bleach library to clean and validate user input.
"""

import bleach
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class ContentSanitizer:
    """
    Content sanitization service for protecting against XSS attacks.
    
    Provides different sanitization levels for different types of content:
    - STRICT: No HTML allowed (plain text only)
    - BASIC: Basic formatting only (b, i, em, strong, u)
    - STANDARD: Common formatting and lists
    - RICH: Full formatting with links (for notes/descriptions)
    """
    
    # Sanitization profiles
    STRICT_TAGS = []
    STRICT_ATTRIBUTES = {}
    
    BASIC_TAGS = ['b', 'i', 'em', 'strong', 'u', 'br']
    BASIC_ATTRIBUTES = {}
    
    STANDARD_TAGS = ['b', 'i', 'em', 'strong', 'u', 'br', 'p', 'ul', 'ol', 'li']
    STANDARD_ATTRIBUTES = {}
    
    RICH_TAGS = ['b', 'i', 'em', 'strong', 'u', 'br', 'p', 'ul', 'ol', 'li', 'a', 'span']
    RICH_ATTRIBUTES = {
        'a': ['href', 'title'],
        'span': ['class']
    }
    
    # URL protocols allowed in links
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    @staticmethod
    def sanitize_text(text: Optional[str], 
                     allowed_tags: Optional[List[str]] = None,
                     allowed_attributes: Optional[Dict] = None,
                     strip: bool = True) -> str:
        """
        Sanitize text content using Bleach.
        
        Args:
            text: The text to sanitize
            allowed_tags: List of allowed HTML tags (default: STRICT - no tags)
            allowed_attributes: Dict of allowed attributes per tag (default: {})
            strip: Whether to strip disallowed tags (True) or escape them (False)
            
        Returns:
            Sanitized text safe for rendering
        """
        if not text:
            return ""
        
        # Default to strict mode if not specified
        if allowed_tags is None:
            allowed_tags = ContentSanitizer.STRICT_TAGS
        if allowed_attributes is None:
            allowed_attributes = ContentSanitizer.STRICT_ATTRIBUTES
        
        try:
            # Clean the HTML
            cleaned = bleach.clean(
                text,
                tags=allowed_tags,
                attributes=allowed_attributes,
                protocols=ContentSanitizer.ALLOWED_PROTOCOLS,
                strip=strip
            )
            
            # Additional normalization
            cleaned = cleaned.strip()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error sanitizing text: {e}")
            # On error, return empty string (fail secure)
            return ""
    
    @staticmethod
    def sanitize_strict(text: Optional[str]) -> str:
        """
        Strict sanitization - removes all HTML, plain text only.
        Use for: usernames, traveler names, item names, destinations.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Plain text with all HTML removed
        """
        return ContentSanitizer.sanitize_text(
            text,
            allowed_tags=ContentSanitizer.STRICT_TAGS,
            allowed_attributes=ContentSanitizer.STRICT_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def sanitize_basic(text: Optional[str]) -> str:
        """
        Basic sanitization - allows basic text formatting only.
        Use for: template names, short descriptions.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Text with basic formatting allowed (b, i, em, strong, u, br)
        """
        return ContentSanitizer.sanitize_text(
            text,
            allowed_tags=ContentSanitizer.BASIC_TAGS,
            allowed_attributes=ContentSanitizer.BASIC_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def sanitize_standard(text: Optional[str]) -> str:
        """
        Standard sanitization - allows common formatting and lists.
        Use for: general notes, activity descriptions.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Text with standard formatting (paragraphs, lists, basic formatting)
        """
        return ContentSanitizer.sanitize_text(
            text,
            allowed_tags=ContentSanitizer.STANDARD_TAGS,
            allowed_attributes=ContentSanitizer.STANDARD_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def sanitize_rich(text: Optional[str]) -> str:
        """
        Rich sanitization - allows full formatting including links.
        Use for: special notes, detailed descriptions, item notes.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Text with rich formatting including safe links
        """
        return ContentSanitizer.sanitize_text(
            text,
            allowed_tags=ContentSanitizer.RICH_TAGS,
            allowed_attributes=ContentSanitizer.RICH_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def sanitize_url(url: Optional[str]) -> str:
        """
        Sanitize and validate a URL.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL or empty string if invalid
        """
        if not url:
            return ""
        
        url = url.strip()
        
        # Use linkify to validate and clean URLs
        try:
            # Check if URL starts with allowed protocol
            if not any(url.lower().startswith(f"{protocol}:") 
                      for protocol in ContentSanitizer.ALLOWED_PROTOCOLS):
                return ""
            
            # Clean the URL
            cleaned = bleach.clean(
                url,
                tags=[],
                attributes={},
                protocols=ContentSanitizer.ALLOWED_PROTOCOLS,
                strip=True
            )
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error sanitizing URL: {e}")
            return ""
    
    @staticmethod
    def sanitize_email(email: Optional[str]) -> str:
        """
        Sanitize email address.
        
        Args:
            email: Email to sanitize
            
        Returns:
            Sanitized email in lowercase
        """
        if not email:
            return ""
        
        # Remove all HTML
        sanitized = ContentSanitizer.sanitize_strict(email)
        
        # Basic email validation (very permissive)
        sanitized = sanitized.strip().lower()
        
        # Must contain @ and have characters before and after
        if '@' not in sanitized or len(sanitized) < 3:
            return ""
        
        parts = sanitized.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return ""
        
        return sanitized
    
    @staticmethod
    def sanitize_trip_data(data: Dict) -> Dict:
        """
        Sanitize all fields in trip data.
        
        Args:
            data: Dictionary containing trip data
            
        Returns:
            Dictionary with sanitized values
        """
        sanitized = {}
        
        # Strict fields (no HTML)
        strict_fields = ['destination']
        for field in strict_fields:
            if field in data:
                sanitized[field] = ContentSanitizer.sanitize_strict(data[field])
        
        # Rich fields (allow formatting)
        rich_fields = ['special_notes']
        for field in rich_fields:
            if field in data:
                sanitized[field] = ContentSanitizer.sanitize_rich(data[field])
        
        # List fields (each item sanitized strictly)
        if 'travelers' in data:
            sanitized['travelers'] = [
                ContentSanitizer.sanitize_strict(traveler)
                for traveler in data.get('travelers', [])
                if traveler
            ]
        
        if 'activities' in data:
            sanitized['activities'] = [
                ContentSanitizer.sanitize_standard(activity)
                for activity in data.get('activities', [])
                if activity
            ]
        
        # Pass through non-text fields unchanged
        passthrough_fields = ['start_date', 'end_date', 'duration', 'travel_style', 
                            'transportation', 'is_template', 'weather_conditions']
        for field in passthrough_fields:
            if field in data:
                sanitized[field] = data[field]
        
        # Template name (basic formatting)
        if 'template_name' in data:
            sanitized['template_name'] = ContentSanitizer.sanitize_basic(data['template_name'])
        
        return sanitized
    
    @staticmethod
    def sanitize_item_data(data: Dict) -> Dict:
        """
        Sanitize all fields in packing item data.
        
        Args:
            data: Dictionary containing packing item data
            
        Returns:
            Dictionary with sanitized values
        """
        sanitized = {}
        
        # Item name (strict - no HTML)
        if 'name' in data:
            sanitized['name'] = ContentSanitizer.sanitize_strict(data['name'])
        
        # Notes (rich formatting allowed)
        if 'notes' in data:
            sanitized['notes'] = ContentSanitizer.sanitize_rich(data['notes'])
        
        # Pass through non-text fields
        passthrough_fields = ['category', 'quantity', 'is_packed', 
                            'is_essential', 'ai_suggested', 'display_order']
        for field in passthrough_fields:
            if field in data:
                sanitized[field] = data[field]
        
        return sanitized
