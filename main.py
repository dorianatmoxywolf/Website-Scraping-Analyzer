from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from models.database import Database
from models.preferences import PreferenceManager
from agents.document_access import DocumentAccessAgent
from agents.content_analysis import ContentAnalysisAgent
from agents.technical_validation import TechnicalValidationAgent
from agents.decision_making import DecisionMakingAgent
from urllib.parse import urlparse, urljoin
import traceback
import uuid

app = Flask(__name__)
CORS(app)

try:
    # Initialize database and preference manager
    print("Initializing database and preference manager...")
    db = Database()
    pref_manager = PreferenceManager(db)

    # Initialize agents
    print("Initializing agents...")
    doc_agent = DocumentAccessAgent(pref_manager)
    content_agent = ContentAnalysisAgent(pref_manager)
    tech_agent = TechnicalValidationAgent(pref_manager)
    decision_agent = DecisionMakingAgent(pref_manager)
    print("Initialization complete!")
except Exception as e:
    print(f"Error during initialization: {str(e)}")
    print(traceback.format_exc())
    raise

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.netloc])
    except:
        return False

def get_primary_domain(url):
    """Extract and format the primary domain from URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get and validate input
        data = request.get_json()
        print(f"Received data: {data}")

        if not data:
            return jsonify({'status': 'error', 'error': 'No data provided'}), 400

        url = data.get('url', '').strip()
        print(f"Processing URL: {url}")

        if not url:
            return jsonify({'status': 'error', 'error': 'URL is required'}), 400

        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        print(f"Final URL: {url}")

        if not is_valid_url(url):
            return jsonify({'status': 'error', 'error': f'Invalid URL format: {url}'}), 400

        primary_domain = get_primary_domain(url)
        print(f"Primary domain: {primary_domain}")

        # Fetch documents
        print("Fetching robots.txt...")
        robots_content = doc_agent.fetch_document(url, 'robots.txt')
        print("Fetching ToS...")
        tos_content = doc_agent.fetch_document(url, 'tos')
        print("Fetching main page...")
        main_content = doc_agent.fetch_document(url, 'main')

        # Analyze content
        print("Analyzing robots.txt...")
        robots_analysis = content_agent.analyze_robots_txt(robots_content)
        print("Analyzing ToS...")
        tos_analysis = content_agent.analyze_tos(tos_content)
        print("Analyzing technical restrictions...")
        tech_analysis = tech_agent.check_technical_restrictions(main_content)

        # Prepare rules for decision making
        rules_examined = []

        # Add robots.txt analysis with proper name
        if robots_analysis:
            robots_analysis['name'] = 'Robots.txt Analysis'
            print(f"Robots.txt analysis: {robots_analysis}")
            rules_examined.append(robots_analysis)

        # Add ToS analysis with proper name
        if tos_analysis:
            tos_analysis['name'] = 'Terms of Service Analysis'
            print(f"ToS analysis: {tos_analysis}")
            rules_examined.append(tos_analysis)

        # Add technical analysis with proper name
        if tech_analysis:
            tech_analysis['name'] = 'Technical Analysis'
            print(f"Technical analysis: {tech_analysis}")
            rules_examined.append(tech_analysis)

        print(f"Total rules examined: {len(rules_examined)}")
        for rule in rules_examined:
            print(f"Rule: {rule.get('name')}, Status: {rule.get('status')}")

        # Make final decision using Decision Making Agent
        print("Making final decision...")
        license_decision = decision_agent.make_decision(rules_examined, url)
        print(f"Decision made: {license_decision.get('usageLicenseType')}")

        # Get decision explanation
        decision_explanation = decision_agent.explain_decision(license_decision)
        print("Decision explanation:", decision_explanation)

        # Format final result
        analysis_result = {
            "Issuer": {
                "directoryUrls": [
                    {
                        "directoryUrl": url
                    }
                ],
                "primaryDomain": primary_domain,
                "LicenseType": {
                    **license_decision,
                    "usageRulesExamined": [
                        {
                            "usageRuleExamined": {
                                "@id": rule.get('@id', url),
                                "@type": "UsageRuleExamined",
                                "checked": True,
                                "confidenceScore": rule.get('confidenceScore', 85.0),
                                "details": rule.get('details', ''),
                                "elementId": rule.get('elementId', str(uuid.uuid4())),
                                "name": rule.get('name', 'Unknown Analysis'),
                                "statusText": rule.get('status', 'unknown'),
                                "url": rule.get('url', url)
                            }
                        } for rule in rules_examined
                    ]
                }
            }
        }

        # Save analysis to database
        try:
            db.save_analysis(url, analysis_result)
            print("Analysis saved to database")
        except Exception as e:
            print(f"Warning: Could not save to database: {e}")

        return jsonify(analysis_result)

    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'error': error_msg
        }), 500

@app.route('/test-db')
def test_db():
    try:
        # Test preference saving
        db.save_preference('test_agent', 'test_context', 0.9)
        value = db.get_preference('test_agent', 'test_context')
        return jsonify({
            'status': 'success',
            'message': 'Database is working',
            'test_preference_value': value
        })
    except Exception as e:
        print(f"Database test error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/get-recent-analyses')
def get_recent_analyses():
    try:
        analyses = db.get_recent_analyses()
        return jsonify({
            'status': 'success',
            'analyses': analyses
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/get-decision-explanation/<path:url>')
def get_decision_explanation(url):
    try:
        analysis = db.get_analysis(url)
        if not analysis:
            return jsonify({
                'status': 'error',
                'error': 'Analysis not found'
            }), 404

        explanation = decision_agent.explain_decision(analysis['Issuer']['LicenseType'])
        return jsonify({
            'status': 'success',
            'explanation': explanation
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)