import json
import asyncio
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import os
from datetime import datetime
from typing import Dict, Any
import time

class BookingEventConsumer:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = os.getenv("BOOKING_TOPIC", "booking-events")
        self.consumer = None
        self.running = False
    
    def _get_consumer(self):
        """Get or create Kafka consumer"""
        if self.consumer is None:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='booking-email-service',
                consumer_timeout_ms=1000
            )
        return self.consumer
    
    def process_booking_event(self, message: Dict[str, Any]):
        """Process a booking event and send email notification"""
        try:
            event_type = message.get("event_type")
            booking_data = message.get("booking", {})
            user_data = message.get("user", {})
            
            print(f"Processing booking event: {event_type}")
            print(f"Booking ID: {booking_data.get('id')}")
            print(f"User: {user_data.get('name')} ({user_data.get('email')})")
            
            # Send email notification based on event type
            if event_type == "booking_created":
                self._send_booking_confirmation_email(user_data, booking_data)
            elif event_type == "booking_confirmed":
                self._send_booking_confirmed_email(user_data, booking_data)
            elif event_type == "booking_cancelled":
                self._send_booking_cancelled_email(user_data, booking_data)
            else:
                print(f"Unknown event type: {event_type}")
                
        except Exception as e:
            print(f"Error processing booking event: {e}")
    
    def _send_booking_confirmation_email(self, user_data: Dict[str, Any], booking_data: Dict[str, Any]):
        """Send booking confirmation email (mocked)"""
        print("=" * 60)
        print("📧 EMAIL NOTIFICATION: Booking Confirmation")
        print("=" * 60)
        print(f"To: {user_data.get('email')}")
        print(f"Subject: Booking Confirmation - Booking #{booking_data.get('id')}")
        print()
        print(f"Dear {user_data.get('name')},")
        print()
        print(f"Your booking has been successfully created!")
        print(f"Booking ID: {booking_data.get('id')}")
        print(f"Ticket ID: {booking_data.get('ticket_id')}")
        print(f"Status: {booking_data.get('status')}")
        print(f"Created: {booking_data.get('created_at')}")
        print(f"Expires: {booking_data.get('expires_at')}")
        print()
        print("Please confirm your booking within 10 minutes to secure your ticket.")
        print("If you don't confirm within this time, your reservation will expire.")
        print()
        print("Thank you for choosing our service!")
        print("=" * 60)
    
    def _send_booking_confirmed_email(self, user_data: Dict[str, Any], booking_data: Dict[str, Any]):
        """Send booking confirmed email (mocked)"""
        print("=" * 60)
        print("📧 EMAIL NOTIFICATION: Booking Confirmed")
        print("=" * 60)
        print(f"To: {user_data.get('email')}")
        print(f"Subject: Booking Confirmed - Booking #{booking_data.get('id')}")
        print()
        print(f"Dear {user_data.get('name')},")
        print()
        print(f"Great news! Your booking has been confirmed!")
        print(f"Booking ID: {booking_data.get('id')}")
        print(f"Ticket ID: {booking_data.get('ticket_id')}")
        print(f"Status: {booking_data.get('status')}")
        print(f"Confirmed: {booking_data.get('confirmed_at')}")
        print()
        print("Your ticket is now secured and ready for the event.")
        print("Please arrive at the venue at least 30 minutes before the show starts.")
        print()
        print("We look forward to seeing you at the event!")
        print("=" * 60)
    
    def _send_booking_cancelled_email(self, user_data: Dict[str, Any], booking_data: Dict[str, Any]):
        """Send booking cancelled email (mocked)"""
        print("=" * 60)
        print("📧 EMAIL NOTIFICATION: Booking Cancelled")
        print("=" * 60)
        print(f"To: {user_data.get('email')}")
        print(f"Subject: Booking Cancelled - Booking #{booking_data.get('id')}")
        print()
        print(f"Dear {user_data.get('name')},")
        print()
        print(f"Your booking has been cancelled as requested.")
        print(f"Booking ID: {booking_data.get('id')}")
        print(f"Ticket ID: {booking_data.get('ticket_id')}")
        print(f"Status: {booking_data.get('status')}")
        print(f"Cancelled: {booking_data.get('cancelled_at')}")
        print()
        print("The ticket has been released and is now available for other customers.")
        print("If you have any questions, please contact our support team.")
        print()
        print("We hope to serve you again in the future!")
        print("=" * 60)
    
    def start_consuming(self):
        """Start consuming booking events"""
        print("Starting booking event consumer...")
        self.running = True
        
        try:
            consumer = self._get_consumer()
            
            while self.running:
                try:
                    # Poll for messages
                    message_batch = consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            self.process_booking_event(message.value)
                            
                except Exception as e:
                    print(f"Error in consumer loop: {e}")
                    time.sleep(1) 
                    
        except KeyboardInterrupt:
            print("Stopping booking event consumer...")
        except Exception as e:
            print(f"Error in booking consumer: {e}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming events"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            self.consumer = None
        print("Booking event consumer stopped.")

# Global consumer instance
booking_consumer = BookingEventConsumer()
