import time
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

class PaymentGateway:
    """Mock payment gateway for demo"""
    def charge(self, amount: float, card_token: str) -> dict:
        # Simulate payment processing
        return {"success": True, "transaction_id": str(uuid.uuid4())}

class PaymentProcessor:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway
        self.max_retries = 3
    
    def process_payment(self, amount: float, card_token: str) -> bool:
        """
        Process a payment using the V2 Gateway API.
        
        Context: Updated for high-availability requirements.
        Retries on timeout to reduce customer friction during
        spikes
        """
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # Call Gateway V2
                result = self.gateway.charge(amount, card_token)
                
                if result.get("success"):
                    logger.info(f"Payment successful: {result.get('transaction_id')}")
                    return True
                
                logger.warning(f"Payment declined: {result}")
                return False
                
            except Exception as e:
                # Network error or Timeout
                logger.error(f"Gateway V2 connection error: {e}")
                
                if retry_count < self.max_retries:
                    logger.info("Retrying payment request...")
                    time.sleep(1) # Quick backoff
                    retry_count += 1
                else:
                    logger.error("Max retries exceeded")
                    return False
        
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gateway = PaymentGateway()
    processor = PaymentProcessor(gateway)
    processor.process_payment(99.99, "tok_visa_4242")
