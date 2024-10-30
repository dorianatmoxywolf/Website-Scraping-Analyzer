import requests
from urllib.parse import urljoin
from .base_agent import BaseAgent

class DocumentAccessAgent(BaseAgent):
    def __init__(self, pref_manager):
        super().__init__(pref_manager)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_document(self, url, doc_type):
        """Fetch different types of documents (robots.txt, ToS, etc.)"""
        try:
            if doc_type == 'robots.txt':
                parsed_url = urljoin(url, '/robots.txt')
                response = self.session.get(parsed_url, timeout=10)
                return {
                    'success': response.status_code == 200,
                    'content': response.text if response.status_code == 200 else '',
                    'url': parsed_url,
                    'headers': dict(response.headers)
                }
            elif doc_type == 'tos':
                tos_paths = ['/terms', '/terms-of-service', '/tos', '/terms-and-conditions']
                for path in tos_paths:
                    try:
                        full_url = urljoin(url, path)
                        response = self.session.get(full_url, timeout=10)
                        if response.status_code == 200:
                            return {
                                'success': True,
                                'content': response.text,
                                'url': full_url,
                                'headers': dict(response.headers)
                            }
                    except:
                        continue
                return {
                    'success': False,
                    'error': 'No ToS found',
                    'url': url,
                    'headers': {}
                }
            else:  # main page
                response = self.session.get(url, timeout=10)
                return {
                    'success': response.status_code == 200,
                    'content': response.text if response.status_code == 200 else '',
                    'url': url,
                    'headers': dict(response.headers)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'headers': {}
            }