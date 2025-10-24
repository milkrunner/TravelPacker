"""
Rate limiting utilities for blueprints
"""

def get_rate_limit_decorator(limit_string):
    """
    Get a rate limiter decorator function
    
    Args:
        limit_string: Rate limit string like "20 per hour"
        
    Returns:
        A decorator function that can be applied to routes
    """
    from src.extensions import limiter
    
    if limiter is not None:
        return limiter.limit(limit_string)
    else:
        # Return a no-op decorator if limiter not available
        def noop_decorator(f):
            return f
        return noop_decorator
