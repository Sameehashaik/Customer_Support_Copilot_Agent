"""
Order Lookup Tool - Check order status

Simulates order database (in production, connect to real API)
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class OrderLookupTool:
    """Look up order status (simulated)"""

    # Simulated order database
    SAMPLE_ORDERS = {
        'ORDER12345': {
            'order_id': 'ORDER12345',
            'status': 'shipped',
            'order_date': '2024-02-28',
            'ship_date': '2024-03-01',
            'expected_delivery': '2024-03-05',
            'tracking_number': 'TRACK123456789',
            'items': ['Blue Widget', 'Red Gadget'],
            'total': 49.99
        },
        'ORDER67890': {
            'order_id': 'ORDER67890',
            'status': 'processing',
            'order_date': '2024-03-02',
            'ship_date': None,
            'expected_delivery': '2024-03-08',
            'tracking_number': None,
            'items': ['Green Thing'],
            'total': 29.99
        }
    }

    def check_order(self, order_id: str) -> Optional[Dict]:
        """
        Check order status

        Args:
            order_id: Order number

        Returns:
            Order information or None if not found
        """
        logger.info(f"Looking up order: {order_id}")

        # Normalize order ID
        order_id = order_id.upper().strip()

        # Check if in database
        if order_id in self.SAMPLE_ORDERS:
            order = self.SAMPLE_ORDERS[order_id]
            logger.info(f"Found order: {order['status']}")
            return order

        # If not found, check if it looks like a valid order ID
        if order_id.startswith('ORDER') and len(order_id) >= 10:
            # Generate random status for demo
            return self._generate_demo_order(order_id)

        logger.warning(f"Order not found: {order_id}")
        return None

    def _generate_demo_order(self, order_id: str) -> Dict:
        """Generate demo order for testing"""
        statuses = ['processing', 'shipped', 'delivered']
        status = random.choice(statuses)

        order_date = datetime.now() - timedelta(days=random.randint(1, 10))

        order = {
            'order_id': order_id,
            'status': status,
            'order_date': order_date.strftime('%Y-%m-%d'),
            'ship_date': None,
            'expected_delivery': None,
            'tracking_number': None,
            'items': ['Demo Item'],
            'total': 39.99
        }

        if status in ['shipped', 'delivered']:
            ship_date = order_date + timedelta(days=1)
            order['ship_date'] = ship_date.strftime('%Y-%m-%d')
            order['expected_delivery'] = (ship_date + timedelta(days=5)).strftime('%Y-%m-%d')
            order['tracking_number'] = f'TRACK{random.randint(100000, 999999)}'

        return order

    def format_order_info(self, order: Dict) -> str:
        """Format order information for display"""
        if not order:
            return "Order not found. Please verify the order number."

        info = [
            f"## Order {order['order_id']}",
            f"**Status:** {order['status'].upper()}",
            f"**Order Date:** {order['order_date']}",
        ]

        if order['ship_date']:
            info.append(f"**Shipped:** {order['ship_date']}")

        if order['expected_delivery']:
            info.append(f"**Expected Delivery:** {order['expected_delivery']}")

        if order['tracking_number']:
            info.append(f"**Tracking:** {order['tracking_number']}")

        info.append(f"**Items:** {', '.join(order['items'])}")
        info.append(f"**Total:** ${order['total']:.2f}")

        return "\n".join(info)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tool = OrderLookupTool()

    # Test order lookup
    test_orders = ['ORDER12345', 'ORDER67890', 'ORDER99999']

    for order_id in test_orders:
        print(f"\n{'='*60}")
        order = tool.check_order(order_id)
        print(tool.format_order_info(order))
