import re
from .base_agent import BaseAgent

class ContentAnalysisAgent(BaseAgent):
    def __init__(self, pref_manager):
        super().__init__(pref_manager)
        self.restriction_patterns = {
            'scraping': [
                'scraping is (strictly )?prohibited',
                'web scraping is (explicitly )?forbidden',
                'automated data collection is (strictly )?prohibited',
                'data scraping is (expressly )?forbidden',
                'no automated access',
                'no scraping allowed',
                'prohibits web crawling',
                'automated access prohibited'
            ],
            'copyright': [
                'all rights reserved',
                'no reproduction without permission',
                'prohibited without explicit permission',
                'unauthorized access prohibited',
                'content is protected by copyright'
            ]
        }

    def analyze_content(self, content, content_type):
        """Analyze content for restrictions"""
        if not content or not content.get('success', False):
            context = f"{content_type}_not_found"
            confidence = self.get_preference(context)
            return {
                'status': 'allowed',
                'confidence': 0.85 * confidence,
                'details': f'No {content_type} content found or accessible',
                'url': content.get('url', 'not found')  # Add default value
            }

        text = content.get('content', '').lower()
        found_restrictions = []
        patterns = self.restriction_patterns.get(content_type, [])

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                found_restrictions.append(pattern)

        # Apply learned preferences
        context = f"{content_type}_{len(found_restrictions)}"
        confidence_modifier = self.get_preference(context)

        return {
            'status': 'restricted' if found_restrictions else 'allowed',
            'confidence': 0.90 * confidence_modifier if found_restrictions else 0.85,
            'details': found_restrictions if found_restrictions else 'No explicit restrictions found',
            'url': content.get('url', 'not found')  # Add default value
        }

    def analyze_robots_txt(self, robots_content):
        """Specifically analyze robots.txt content"""
        return self.analyze_content(robots_content, 'scraping')

    def analyze_tos(self, tos_content):
        """Specifically analyze Terms of Service content"""
        if not tos_content or not tos_content.get('success', False):
            return {
                'status': 'allowed',
                'confidence': 0.85,
                'details': 'No Terms of Service found',
                'url': tos_content.get('url', 'not found')  # Add default value
            }

        tos_result = self.analyze_content(tos_content, 'scraping')
        copyright_result = self.analyze_content(tos_content, 'copyright')

        # Combine results, taking the more restrictive outcome
        if tos_result['status'] == 'restricted' or copyright_result['status'] == 'restricted':
            return {
                'status': 'restricted',
                'confidence': max(tos_result['confidence'], copyright_result['confidence']),
                'details': {
                    'scraping_restrictions': tos_result['details'],
                    'copyright_restrictions': copyright_result['details']
                },
                'url': tos_content.get('url', 'not found')  # Add default value
            }

        return {
            'status': 'allowed',
            'confidence': min(tos_result['confidence'], copyright_result['confidence']),
            'details': 'No restrictions found in Terms of Service',
            'url': tos_content.get('url', 'not found')  # Add default value
        }