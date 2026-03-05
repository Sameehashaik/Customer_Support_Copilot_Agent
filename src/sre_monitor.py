"""
SRE Monitor - Track metrics and alert on anomalies

Introduction to SRE concepts (expanded in Project 5!)
"""

from typing import Dict, List
from datetime import datetime
from collections import deque
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SREMonitor:
    """
    Monitor copilot health and performance

    Tracks:
    - PII filter success rate
    - Escalation rate
    - Sentiment trends
    - Response times
    - Costs

    Alerts on:
    - PII filter failures
    - High escalation rates
    - Cost spikes
    - Performance degradation
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize SRE monitor

        Args:
            window_size: Number of recent events to track
        """
        self.window_size = window_size

        # Metrics storage (rolling window)
        self.metrics = {
            'pii_filter_success': deque(maxlen=window_size),
            'escalations': deque(maxlen=window_size),
            'sentiment_scores': deque(maxlen=window_size),
            'response_times': deque(maxlen=window_size),
            'costs': deque(maxlen=window_size)
        }

        # Baseline metrics (learned from first 100 interactions)
        self.baselines = {
            'escalation_rate': 0.15,      # 15% is normal
            'avg_sentiment': 0.6,          # Slightly positive
            'avg_cost': 0.008,             # $0.008 per interaction
            'pii_success_rate': 0.99       # 99% success
        }

        # Alert log
        self.alerts = []

        logger.info("SRE Monitor initialized")

    def track_interaction(self, metrics: Dict):
        """
        Track single customer interaction

        Args:
            metrics: {
                'pii_filter_success': bool,
                'escalated': bool,
                'sentiment_score': float,
                'response_time_ms': int,
                'cost': float
            }
        """
        self.metrics['pii_filter_success'].append(metrics.get('pii_filter_success', True))
        self.metrics['escalations'].append(metrics.get('escalated', False))
        self.metrics['sentiment_scores'].append(metrics.get('sentiment_score', 0.5))
        self.metrics['response_times'].append(metrics.get('response_time_ms', 0))
        self.metrics['costs'].append(metrics.get('cost', 0.0))

        # Check for anomalies
        self._check_anomalies(metrics)

    def _check_anomalies(self, current_metrics: Dict):
        """Check for anomalies and alert"""

        # CRITICAL: PII filter failure
        if not current_metrics.get('pii_filter_success', True):
            self._alert_critical(
                "PII Filter Failure",
                "PII filter failed to process message",
                current_metrics
            )

        # WARNING: High escalation rate
        escalation_rate = self.get_escalation_rate()
        if escalation_rate > 0.30:  # >30% escalations
            self._alert_warning(
                "High Escalation Rate",
                f"Escalation rate at {escalation_rate:.1%} (baseline: {self.baselines['escalation_rate']:.1%})",
                {'current_rate': escalation_rate}
            )

        # WARNING: Very negative sentiment spike
        recent_sentiments = list(self.metrics['sentiment_scores'])[-10:]
        if recent_sentiments:
            avg_recent = sum(recent_sentiments) / len(recent_sentiments)
            if avg_recent < 0.3:
                self._alert_warning(
                    "Negative Sentiment Spike",
                    f"Recent average sentiment: {avg_recent:.2f}",
                    {'avg_sentiment': avg_recent}
                )

        # WARNING: Cost spike
        if current_metrics.get('cost', 0) > self.baselines['avg_cost'] * 5:
            self._alert_warning(
                "Cost Spike",
                f"Single interaction cost: ${current_metrics['cost']:.4f}",
                current_metrics
            )

    def _alert_critical(self, title: str, message: str, details: Dict):
        """Log critical alert"""
        alert = {
            'severity': 'CRITICAL',
            'title': title,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        self.alerts.append(alert)
        logger.error(f"CRITICAL: {title} - {message}")

        # In production: Send to PagerDuty, Slack, email

    def _alert_warning(self, title: str, message: str, details: Dict):
        """Log warning alert"""
        alert = {
            'severity': 'WARNING',
            'title': title,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        self.alerts.append(alert)
        logger.warning(f"WARNING: {title} - {message}")

    def get_escalation_rate(self) -> float:
        """Calculate current escalation rate"""
        if not self.metrics['escalations']:
            return 0.0

        escalations = list(self.metrics['escalations'])
        return sum(escalations) / len(escalations)

    def get_pii_success_rate(self) -> float:
        """Calculate PII filter success rate"""
        if not self.metrics['pii_filter_success']:
            return 1.0

        successes = list(self.metrics['pii_filter_success'])
        return sum(successes) / len(successes)

    def get_avg_sentiment(self) -> float:
        """Calculate average sentiment"""
        if not self.metrics['sentiment_scores']:
            return 0.5

        return sum(self.metrics['sentiment_scores']) / len(self.metrics['sentiment_scores'])

    def get_dashboard_metrics(self) -> Dict:
        """Get metrics for dashboard display"""
        return {
            'escalation_rate': self.get_escalation_rate(),
            'pii_success_rate': self.get_pii_success_rate(),
            'avg_sentiment': self.get_avg_sentiment(),
            'total_interactions': len(self.metrics['sentiment_scores']),
            'recent_alerts': len([a for a in self.alerts if a['severity'] == 'CRITICAL']),
            'avg_cost': sum(self.metrics['costs']) / len(self.metrics['costs']) if self.metrics['costs'] else 0
        }

    def print_health_report(self):
        """Print health status report"""
        metrics = self.get_dashboard_metrics()

        print("\n" + "=" * 60)
        print("COPILOT HEALTH REPORT")
        print("=" * 60)
        print(f"Total Interactions: {metrics['total_interactions']}")
        print(f"Escalation Rate: {metrics['escalation_rate']:.1%} (Baseline: {self.baselines['escalation_rate']:.1%})")
        print(f"PII Success Rate: {metrics['pii_success_rate']:.1%} (Target: 99%+)")
        print(f"Avg Sentiment: {metrics['avg_sentiment']:.2f} (Baseline: {self.baselines['avg_sentiment']:.2f})")
        print(f"Avg Cost: ${metrics['avg_cost']:.4f}")
        print(f"Critical Alerts: {metrics['recent_alerts']}")
        print("=" * 60)

        if self.alerts:
            print("\nRecent Alerts:")
            for alert in self.alerts[-5:]:
                print(f"  [{alert['severity']}] {alert['title']}: {alert['message']}")

        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    monitor = SREMonitor()

    # Simulate interactions
    for i in range(20):
        monitor.track_interaction({
            'pii_filter_success': True,
            'escalated': i % 10 == 0,  # 10% escalation
            'sentiment_score': 0.6,
            'response_time_ms': 2000,
            'cost': 0.008
        })

    monitor.print_health_report()
