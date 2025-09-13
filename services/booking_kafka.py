import json
import asyncio
from kafka import KafkaProducer
from kafka.errors import KafkaError
from typing import Dict, Any
import os
from datetime import datetime

class BookingKafkaProducer:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = os.getenv("BOOKING_TOPIC", "booking-events")
        self.producer = None
    
    def _get_producer(self):
        """Get or create Kafka producer"""
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                retry_backoff_ms=100,
                request_timeout_ms=5000
            )
        return self.producer
    
    def send_booking_event(self, event_type: str, booking_data: Dict[str, Any], user_data: Dict[str, Any]):
        """Send booking event to Kafka"""
        try:
            producer = self._get_producer()
            
            # Create event message
            event_message = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "booking": booking_data,
                "user": user_data
            }
            
            # Use booking_id as key for partitioning
            key = str(booking_data.get("id", "unknown"))
            
            # Send message
            future = producer.send(
                self.topic,
                key=key,
                value=event_message
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            print(f"Booking event sent successfully: {event_type} for booking {booking_data.get('id')}")
            return True
            
        except KafkaError as e:
            print(f"Failed to send booking event: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending booking event: {e}")
            return False
    
    def close(self):
        """Close the producer"""
        if self.producer:
            self.producer.close()
            self.producer = None

# Global producer instance
booking_producer = BookingKafkaProducer()
