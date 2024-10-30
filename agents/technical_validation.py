from .base_agent import BaseAgent
import re
from bs4 import BeautifulSoup

class TechnicalValidationAgent(BaseAgent):
    def __init__(self, pref_manager):
        super().__init__(pref_manager)
        self.captcha_patterns = [
            'captcha',
            'recaptcha',
            'g-recaptcha',
            'h-captcha',
            'cloudflare-challenge',
            'verify you are human',
            'human verification',
            'bot protection',
            'prove you are human'
        ]

    def check_technical_restrictions(self, main_content):
        """Analyze technical restrictions like CAPTCHA and metadata"""
        if not main_content or not main_content.get('success', False):
            return {
                'status': 'allowed',
                'confidence': 0.85,
                'details': 'Could not check technical restrictions',
                'url': main_content.get('url', 'not found')
            }

        restrictions = []
        confidence = 0.85
        html_content = main_content.get('content', '')
        headers = main_content.get('headers', {})

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Check meta robots
            meta_robots = soup.find('meta', attrs={'name': 'robots'})
            if meta_robots:
                content = meta_robots.get('content', '').lower()
                if 'noindex' in content or 'nofollow' in content:
                    restrictions.append(f'Meta robots tag: {content}')
                    confidence = 0.95

            # Check X-Robots-Tag header
            robots_header = headers.get('X-Robots-Tag', '').lower()
            if 'noindex' in robots_header or 'nofollow' in robots_header:
                restrictions.append(f'X-Robots-Tag header: {robots_header}')
                confidence = 0.95

            # Check for CAPTCHA
            page_text = html_content.lower()
            for pattern in self.captcha_patterns:
                if pattern in page_text:
                    restrictions.append(f'CAPTCHA detected: {pattern}')
                    confidence = 0.98
                    break

            # Check for rate limiting headers
            rate_limit_headers = [
                'X-RateLimit-Limit',
                'X-RateLimit-Remaining',
                'X-RateLimit-Reset',
                'Retry-After'
            ]
            for header in rate_limit_headers:
                if header.lower() in {k.lower(): v for k, v in headers.items()}:
                    restrictions.append(f'Rate limiting detected: {header}')
                    confidence = 0.90

            # Apply learned preferences
            context = f"technical_{len(restrictions)}"
            confidence_modifier = self.get_preference(context)
            confidence *= confidence_modifier

        except Exception as e:
            return {
                'status': 'allowed',
                'confidence': 0.85,
                'details': f'Error analyzing technical restrictions: {str(e)}',
                'url': main_content.get('url', 'not found')
            }

        return {
            'status': 'restricted' if restrictions else 'allowed',
            'confidence': confidence,
            'details': restrictions if restrictions else 'No technical restrictions found',
            'url': main_content.get('url', 'not found'),
            'specific_restrictions': {
                'has_captcha': any('CAPTCHA' in r for r in restrictions),
                'has_meta_robots': any('robots tag' in r for r in restrictions),
                'has_rate_limiting': any('Rate limiting' in r for r in restrictions)
            }
        }