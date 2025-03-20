import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SMSService:
    def __init__(self):
        """Initialize the SMS service with Twilio credentials"""
        # Get Twilio credentials from environment variables
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # Check if credentials are available
        self.enabled = all([self.account_sid, self.auth_token, self.from_number])
        
        if self.enabled:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            print("Warning: Twilio credentials not found. SMS notifications will be simulated.")
    
    def send_sms(self, to_number, message):
        """
        Send an SMS message
        
        Args:
            to_number: Recipient's phone number (with country code)
            message: Message content
            
        Returns:
            Dict with status and message ID if successful
        """
        if not self.enabled:
            # Simulate sending SMS
            print(f"SIMULATED SMS to {to_number}: {message}")
            return {
                "status": "simulated",
                "message": "SMS notification simulated (Twilio credentials not configured)"
            }
        
        try:
            # Send the SMS using Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            return {
                "status": "sent",
                "message_id": twilio_message.sid
            }
        
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def send_sos_notifications(self, user_name, location, message, emergency_contacts):
        """
        Send SOS notifications to all emergency contacts
        
        Args:
            user_name: Name of the user in distress
            location: Dict with latitude and longitude
            message: Custom message or description of the emergency
            emergency_contacts: List of contact dicts with name and phone
            
        Returns:
            List of notification results
        """
        results = []
        
        # Format the location as a Google Maps link
        maps_link = f"https://www.google.com/maps?q={location['latitude']},{location['longitude']}"
        
        # Create the SOS message
        sos_message = f"EMERGENCY SOS from {user_name}! Location: {maps_link}"
        
        if message:
            sos_message += f"\nMessage: {message}"
        
        sos_message += "\nPlease respond immediately or contact authorities."
        
        # Send to each emergency contact
        for contact in emergency_contacts:
            phone = contact.get('phone')
            if phone:
                # Make sure phone number has country code
                if not phone.startswith('+'):
                    phone = '+' + phone
                
                result = self.send_sms(phone, sos_message)
                result['contact_name'] = contact.get('name')
                result['contact_phone'] = phone
                results.append(result)
        
        return results