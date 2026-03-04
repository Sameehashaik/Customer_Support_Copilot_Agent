"""Cost Tracker for AWS Bedrock"""

import json
from datetime import datetime
from pathlib import Path

class BedrockCostTracker:
    """Track AWS Bedrock costs"""

    PRICING = {
        'input': 0.80,   # per 1M tokens
        'output': 4.00
    }

    def __init__(self, log_file='project4_costs.json'):
        self.log_file = Path(log_file)
        self.session_costs = []
        self._load_history()

    def _load_history(self):
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def _save_history(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def track_call(self, agent_name: str, input_tokens: int, output_tokens: int, description: str = ""):
        """Track a Bedrock API call"""
        input_cost = (input_tokens / 1_000_000) * self.PRICING['input']
        output_cost = (output_tokens / 1_000_000) * self.PRICING['output']
        total_cost = input_cost + output_cost

        call_data = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_cost': total_cost,
            'description': description
        }

        self.session_costs.append(call_data)
        self.history.append(call_data)
        self._save_history()

        return total_cost

    def print_session_summary(self):
        """Print cost summary"""
        if not self.session_costs:
            print("No costs tracked")
            return

        total = sum(c['total_cost'] for c in self.session_costs)
        print(f"\n{'='*60}")
        print(f"Session Costs: ${total:.4f}")
        print(f"Total calls: {len(self.session_costs)}")
        print(f"{'='*60}\n")
