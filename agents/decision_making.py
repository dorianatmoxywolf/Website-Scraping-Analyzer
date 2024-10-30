from .base_agent import BaseAgent
from typing import Dict, List, Any
import uuid

class DecisionMakingAgent(BaseAgent):
    def __init__(self, pref_manager):
        super().__init__(pref_manager)
        # Base weights for different rules
        self.weights = {
            'Robots.txt': 0.35,      # High weight as it's explicit
            'Terms of Service': 0.35, # Equal to robots.txt
            'Technical': 0.30         # Slightly lower as it's more inferential
        }

        # Confidence thresholds
        self.high_confidence = 90.0
        self.medium_confidence = 75.0

        # Risk levels for different restriction types
        self.restriction_severity = {
            'explicit_prohibition': 1.0,    # Direct "no scraping" statements
            'rate_limiting': 0.7,           # Technical barriers
            'authentication': 0.8,          # Required login/auth
            'implicit_prohibition': 0.6,    # Indirect restrictions
            'no_specification': 0.2         # No clear statement
        }

    def calculate_weighted_score(self, rule: Dict[str, Any]) -> float:
        """Calculate weighted score for a single rule"""
        # Determine rule type from the analysis
        rule_type = None
        if 'robots' in str(rule.get('details', '')).lower():
            rule_type = 'Robots.txt'
        elif 'terms of service' in str(rule.get('details', '')).lower():
            rule_type = 'Terms of Service'
        else:
            rule_type = 'Technical'

        base_weight = self.weights.get(rule_type, 0.2)
        confidence_factor = float(rule.get('confidence', 85.0)) / 100.0

        # Adjust weight based on confidence
        if confidence_factor * 100 >= self.high_confidence:
            confidence_multiplier = 1.2
        elif confidence_factor * 100 >= self.medium_confidence:
            confidence_multiplier = 1.0
        else:
            confidence_multiplier = 0.8

        return base_weight * confidence_factor * confidence_multiplier

    def analyze_restriction_severity(self, rule: Dict[str, Any]) -> float:
        """Analyze how severe the restrictions are"""
        details = rule.get('details', '')
        if isinstance(details, list):
            details = ' '.join(map(str, details))
        elif isinstance(details, dict):
            details = str(details)

        severity = 0.0
        details_lower = str(details).lower()

        # Check for explicit prohibitions
        if any(phrase in details_lower for phrase in [
            'prohibited', 'forbidden', 'not allowed', 'not permitted'
        ]):
            severity = max(severity, self.restriction_severity['explicit_prohibition'])

        # Check for rate limiting
        if any(phrase in details_lower for phrase in [
            'rate limit', 'throttling', 'requests per'
        ]):
            severity = max(severity, self.restriction_severity['rate_limiting'])

        # Check for authentication requirements
        if any(phrase in details_lower for phrase in [
            'login required', 'authentication required', 'authorized access'
        ]):
            severity = max(severity, self.restriction_severity['authentication'])

        return severity if severity > 0 else self.restriction_severity['no_specification']

    def make_decision(self, rules: List[Dict[str, Any]], url: str) -> Dict[str, Any]:
        """Make final decision based on all analyses"""
        total_weighted_score = 0.0
        total_weight = 0.0
        restriction_details = []
        highest_confidence = 0.0

        for rule in rules:
            weighted_score = self.calculate_weighted_score(rule)
            severity = self.analyze_restriction_severity(rule)

            # Track the highest confidence score
            confidence = float(rule.get('confidence', 85.0))
            highest_confidence = max(highest_confidence, confidence)

            # If this rule indicates restrictions
            if rule.get('status', '').lower() == 'restricted':
                restriction_details.append({
                    'source': rule.get('details', 'Unknown source'),
                    'severity': severity,
                    'confidence': confidence,
                    'details': rule.get('details', '')
                })
                total_weighted_score += weighted_score * severity

            total_weight += weighted_score

        # Calculate final restriction score
        restriction_score = total_weighted_score / total_weight if total_weight > 0 else 0

        # Determine rights based on restriction score and context
        is_restricted = restriction_score > 0.5

        # Get learning preferences
        context = f"decision_{is_restricted}"
        confidence_modifier = self.get_preference(context)

        return {
            "rightsToDerivate": not is_restricted,
            "rightsToRedistribute": not is_restricted,
            "rightsToScrape": not is_restricted,
            "rightsToTag": not is_restricted,
            "rightsToTransform": not is_restricted,
            "schemaVersion": "1",
            "usageLicenseType": "RESTRICTED" if is_restricted else "OPEN",
            "details": {
                "decision_confidence": highest_confidence * confidence_modifier,
                "restriction_score": restriction_score * 100,
                "restrictions_found": restriction_details,
                "analysis_summary": "Detailed analysis of scraping permissions based on multiple factors",
            },
            "elementId": str(uuid.uuid4()),
            "@id": url,
            "@type": "LicenseType",
            "licenseRightsReference": url
        }

    def explain_decision(self, decision: Dict[str, Any]) -> str:
        """Provide human-readable explanation of the decision"""
        is_restricted = decision['usageLicenseType'] == 'RESTRICTED'
        explanation = []

        explanation.append(
            f"Final Decision: Scraping is {'NOT ' if is_restricted else ''}allowed "
            f"(Confidence: {decision['details']['decision_confidence']:.1f}%)"
        )

        if decision['details']['restrictions_found']:
            explanation.append("\nRestrictions found:")
            for restriction in decision['details']['restrictions_found']:
                explanation.append(
                    f"- {restriction['source']}: Severity {restriction['severity']:.2f} "
                    f"(Confidence: {restriction['confidence']:.1f}%)"
                )
        else:
            explanation.append("\nNo explicit restrictions found.")

        return "\n".join(explanation)