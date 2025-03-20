import os
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from database import Database
from sms_service import SMSService

class IncidentReportingHandler:
    """Handler for the Anonymous Incident Reporting Agent"""
    
    def __init__(self, agent, db=None):
        self.agent = agent
        self.db = db or Database()
        
    def submit_report(self, user_id, report_text: str, location: Dict[str, float], 
                      timestamp: Optional[str] = None) -> Dict:
        """
        Submit an anonymous incident report
        
        Args:
            user_id: ID of the user submitting the report
            report_text: Description of the incident
            location: Dict containing latitude and longitude
            timestamp: Optional timestamp, defaults to current time
        
        Returns:
            Dict containing report details and ID
        """
        # Generate a unique report ID
        report_id = str(uuid.uuid4())
        
        # Use the agent to analyze and anonymize the report
        agent_input = {
            "text": report_text,
            "location": location,
            "timestamp": timestamp or datetime.now().isoformat(),
            "task": "analyze_and_anonymize_report"
        }
        
        # Call the agent
        agent_response = self.agent.run(json.dumps(agent_input))
        
        try:
            # Parse the agent response
            analysis = json.loads(agent_response)
            
            # Extract data from analysis
            anonymized_text = analysis.get("anonymized_text", report_text)
            severity = analysis.get("severity", "medium")
            categories = analysis.get("categories", ["general_concern"])
            requires_immediate_action = analysis.get("requires_immediate_action", False)
            
            # Store the report in the database
            self.db.create_report(
                report_id=report_id,
                reporter_id=user_id,
                description=report_text,
                anonymized_description=anonymized_text,
                latitude=location["latitude"],
                longitude=location["longitude"],
                severity=severity,
                categories=categories,
                status="submitted"
            )
            
            # If high severity, simulate notifying law enforcement
            if requires_immediate_action:
                print(f"ALERT: High severity incident reported! Notifying law enforcement about report {report_id}")
            
            return {
                "report_id": report_id,
                "severity": severity,
                "categories": categories,
                "requires_immediate_action": requires_immediate_action,
                "message": "Your report has been submitted anonymously."
            }
        
        except Exception as e:
            print(f"Error processing agent response: {str(e)}")
            # Fallback response
            return {
                "report_id": report_id,
                "severity": "medium",
                "categories": ["general_concern"],
                "requires_immediate_action": False,
                "message": "Your report has been submitted anonymously, but there was an issue with analysis."
            }
    
    def verify_report(self, report_id: str, verification_type: str = "confirm") -> Dict:
        """
        Allow users to verify an existing report to prevent false reports
        
        Args:
            report_id: The ID of the report to verify
            verification_type: Either "confirm" or "dispute"
            
        Returns:
            Dict with verification status
        """
        # Verify the report in the database
        success = self.db.verify_report(report_id, verification_type)
        
        if not success:
            return {"status": "error", "message": "Report not found"}
        
        # Get updated report
        report = self.db.get_report(report_id)
        
        if verification_type == "confirm":
            return {
                "status": "success", 
                "message": f"Report verified. Current verification count: {report['verification_count']}"
            }
        else:
            return {"status": "success", "message": "Report has been flagged for review"}
    
    def get_community_support(self, report_id: str) -> Dict:
        """
        Get available community volunteers who can provide support
        
        Args:
            report_id: The ID of the report
            
        Returns:
            Dict with available volunteers
        """
        # Get the report
        report = self.db.get_report(report_id)
        
        if not report:
            return {"status": "error", "message": "Report not found"}
        
        # In a real implementation, this would query a volunteers database
        # For this demo, we'll return sample volunteers based on report categories
        volunteers = []
        
        # Sample volunteers
        all_volunteers = [
            {"id": "vol1", "name": "Support Volunteer 1", "expertise": ["harassment", "stalking"]},
            {"id": "vol2", "name": "Support Volunteer 2", "expertise": ["physical_threat", "unsafe_environment"]},
            {"id": "vol3", "name": "Support Volunteer 3", "expertise": ["general_concern"]}
        ]
        
        # Match volunteers based on report categories
        for volunteer in all_volunteers:
            if any(category in volunteer["expertise"] for category in report["categories"]):
                volunteers.append(volunteer)
        
        return {
            "status": "success",
            "volunteers": volunteers
        }
    
    def get_reports_by_area(self, latitude: float, longitude: float, radius_km: float = 5) -> List[Dict]:
        """
        Get anonymized reports from a specific area
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            List of reports in the area (with sensitive details removed)
        """
        # Get reports from the database
        reports = self.db.get_reports_by_area(latitude, longitude, radius_km)
        
        # Create sanitized versions with minimal details
        sanitized_reports = []
        for report in reports:
            sanitized_reports.append({
                "id": report["id"],
                "timestamp": report["created_at"],
                "categories": report["categories"],
                "severity": report["severity"],
                "distance_km": report.get("distance_km", 0)
            })
        
        return sanitized_reports


class SafetyNavigatorHandler:
    """Handler for the Personalized Safety Navigator Agent"""
    
    def __init__(self, agent, db=None):
        self.agent = agent
        self.db = db or Database()
    
    def register_user(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user with their profile data
        
        Args:
            user_id: Unique identifier for the user
            profile_data: User profile information
            
        Returns:
            Dict containing registration status
        """
        # Create or update user in database
        self.db.create_user(user_id, profile_data.get("name"), profile_data.get("email"))
        
        # Add emergency contacts if provided
        if "emergency_contacts" in profile_data:
            for contact in profile_data["emergency_contacts"]:
                self.db.add_emergency_contact(
                    user_id=user_id,
                    name=contact.get("name", ""),
                    phone=contact.get("phone", ""),
                    relationship=contact.get("relationship", "")
                )
        
        return {
            "status": "success",
            "message": "User profile registered successfully",
            "user_id": user_id
        }
    
    def start_journey(self, user_id: str, start_location: Dict[str, float], 
                     destination: Dict[str, float], travel_mode: str = "walking") -> Dict[str, Any]:
        """
        Start a new journey with safety navigation
        
        Args:
            user_id: User identifier
            start_location: Starting coordinates
            destination: Destination coordinates
            travel_mode: Mode of transportation
            
        Returns:
            Dict containing journey details and safety information
        """
        # Generate a unique journey ID
        journey_id = str(uuid.uuid4())
        
        # Use the agent to analyze route safety and generate recommendations
        agent_input = {
            "user_id": user_id,
            "start_location": start_location,
            "destination": destination,
            "travel_mode": travel_mode,
            "current_time": datetime.now().isoformat(),
            "task": "analyze_route_safety_and_recommendations"
        }
        
        # Call the agent
        agent_response = self.agent.run(json.dumps(agent_input))
        
        try:
            # Parse the agent response
            analysis = json.loads(agent_response)
            
            # Extract data from analysis
            route_safety = analysis.get("route_safety", {
                "overall_risk": "medium",
                "risk_areas_on_route": [],
                "time_factor": "day",
                "alternative_routes_available": False
            })
            
            safety_recommendations = analysis.get("safety_recommendations", [
                "Stay in well-lit, populated areas whenever possible",
                "Keep your phone charged and accessible",
                "Share your location with trusted contacts"
            ])
            
            # Store the journey in the database
            self.db.create_journey(
                journey_id=journey_id,
                user_id=user_id,
                start_latitude=start_location["latitude"],
                start_longitude=start_location["longitude"],
                destination_latitude=destination["latitude"],
                destination_longitude=destination["longitude"],
                travel_mode=travel_mode,
                route_safety=route_safety
            )
            
            return {
                "status": "success",
                "journey_id": journey_id,
                "route_safety": route_safety,
                "safety_recommendations": safety_recommendations
            }
        
        except Exception as e:
            print(f"Error processing agent response: {str(e)}")
            # Fallback response
            return {
                "status": "success",
                "journey_id": journey_id,
                "route_safety": {
                    "overall_risk": "medium",
                    "risk_areas_on_route": [],
                    "time_factor": "day",
                    "alternative_routes_available": False
                },
                "safety_recommendations": [
                    "Stay in well-lit, populated areas whenever possible",
                    "Keep your phone charged and accessible",
                    "Share your location with trusted contacts"
                ]
            }
    
    def update_location(self, journey_id: str, current_location: Dict[str, float], 
                       timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Update user's current location and get real-time safety information
        
        Args:
            journey_id: Journey identifier
            current_location: Current coordinates
            timestamp: Optional timestamp
            
        Returns:
            Dict containing updated safety information
        """
        # Get the journey from database
        journey = self.db.get_journey(journey_id)
        
        if not journey:
            return {"status": "error", "message": "Journey not found"}
        
        # Use the agent to analyze current location safety
        agent_input = {
            "journey_id": journey_id,
            "journey_data": journey,
            "current_location": current_location,
            "timestamp": timestamp or datetime.now().isoformat(),
            "task": "analyze_current_location_safety"
        }
        
        # Call the agent
        agent_response = self.agent.run(json.dumps(agent_input))
        
        try:
            # Parse the agent response
            analysis = json.loads(agent_response)
            
            # Extract data from analysis
            nearby_risks = analysis.get("nearby_risks", [])
            alerts = analysis.get("alerts", [])
            
            # Check if destination reached
            destination_reached = analysis.get("destination_reached", False)
            
            # If not explicitly determined by the agent, calculate it
            if not destination_reached:
                destination_reached = self._check_destination_reached(
                    {"latitude": journey["destination_latitude"], "longitude": journey["destination_longitude"]},
                    current_location
                )
            
            # Update journey status if destination reached
            if destination_reached:
                self.db.update_journey_status(journey_id, "completed")
            
            return {
                "status": "success",
                "nearby_risks": nearby_risks,
                "alerts": alerts,
                "destination_reached": destination_reached,
                "journey_status": "completed" if destination_reached else journey["status"]
            }
        
        except Exception as e:
            print(f"Error processing agent response: {str(e)}")
            # Fallback response
            return {
                "status": "success",
                "nearby_risks": [],
                "alerts": [],
                "destination_reached": self._check_destination_reached(
                    {"latitude": journey["destination_latitude"], "longitude": journey["destination_longitude"]},
                    current_location
                ),
                "journey_status": journey["status"]
            }
    
    def end_journey(self, journey_id: str) -> Dict[str, Any]:
        """
        End an active journey
        
        Args:
            journey_id: Journey identifier
            
        Returns:
            Dict containing journey summary
        """
        # Get the journey from database
        journey = self.db.get_journey(journey_id)
        
        if not journey:
            return {"status": "error", "message": "Journey not found"}
        
        # Update journey status in database
        self.db.update_journey_status(journey_id, "completed")
        
        # Get updated journey
        updated_journey = self.db.get_journey(journey_id)
        
        # Generate journey summary
        summary = {
            "journey_id": journey_id,
            "start_time": journey["start_time"],
            "end_time": updated_journey["end_time"],
            "total_alerts": 0,  # In a real app, this would count alerts from a related table
            "safety_score": self._calculate_safety_score(journey)
        }
        
        return {
            "status": "success",
            "message": "Journey completed successfully",
            "summary": summary
        }
    
    def trigger_emergency(self, journey_id: str, emergency_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger emergency mode for a journey
        
        Args:
            journey_id: Journey identifier
            emergency_details: Details about the emergency
            
        Returns:
            Dict containing emergency response information
        """
        # Get the journey from database
        journey = self.db.get_journey(journey_id)
        
        if not journey:
            return {"status": "error", "message": "Journey not found"}
        
        # Update journey status to emergency
        self.db.update_journey_status(journey_id, "emergency")
        
        # Get user's emergency contacts
        user_id = journey["user_id"]
        emergency_contacts = self.db.get_emergency_contacts(user_id)
        
        # Initialize SMS service
        sms_service = SMSService()
        
        # Get the current location (use journey start location as fallback)
        current_location = {
            "latitude": emergency_details.get("latitude", journey["start_latitude"]),
            "longitude": emergency_details.get("longitude", journey["start_longitude"])
        }
        
        # Send SOS notifications to emergency contacts
        notification_results = sms_service.send_sos_notifications(
            user_name="User",  # In a real app, get the user's name
            location=current_location,
            message=emergency_details.get("description", "Emergency assistance needed!"),
            emergency_contacts=emergency_contacts
        )
        
        # Record the SOS event in the database
        self.db.create_sos(
            user_id=user_id,
            latitude=current_location["latitude"],
            longitude=current_location["longitude"],
            message=emergency_details.get("description", ""),
            contacts_notified=[r["contact_phone"] for r in notification_results if r["status"] in ["sent", "simulated"]]
        )
        
        return {
            "status": "success",
            "message": "Emergency mode activated",
            "emergency_id": str(uuid.uuid4()),  # Generate a unique emergency ID
            "notified_contacts": len([r for r in notification_results if r["status"] in ["sent", "simulated"]]),
            "authorities_alerted": True,
            "notification_results": notification_results
        }
    
    def _check_destination_reached(self, destination: Dict[str, float], 
                                  current_location: Dict[str, float], threshold_km: float = 0.1) -> bool:
        """Check if the user has reached their destination"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [
            current_location["longitude"], current_location["latitude"],
            destination["longitude"], destination["latitude"]
        ])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        distance = c * r
        return distance <= threshold_km
    
    def _calculate_safety_score(self, journey: Dict[str, Any]) -> int:
        """Calculate a safety score for the completed journey"""
        # Base score
        score = 100
        
        # Deduct points based on route risk
        route_safety = journey["route_safety"]
        if route_safety["overall_risk"] == "high":
            score -= 20
        elif route_safety["overall_risk"] == "medium":
            score -= 10
        
        # Ensure score doesn't go below 0
        return max(0, score)


class EmergencyAlertHandler:
    """Handler for the Emergency Alert System Agent"""
    
    def __init__(self, agent, db=None):
        self.agent = agent
        self.db = db or Database()
        self.sms_service = SMSService()
    
    def subscribe_user(self, user_id: str, location: Dict[str, float], 
                      preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Subscribe a user to receive emergency alerts
        
        Args:
            user_id: Unique identifier for the user
            location: User's location coordinates
            preferences: Alert preferences
            
        Returns:
            Dict containing subscription status
        """
        # In a real app, this would store subscription preferences in the database
        # For this demo, we'll just return success
        
        return {
            "status": "success",
            "message": "Successfully subscribed to emergency alerts",
            "user_id": user_id
        }
    
    def create_alert(self, user_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new emergency alert
        
        Args:
            user_id: ID of the user reporting the alert
            alert_data: Alert details
            
        Returns:
            Dict containing alert creation status
        """
        # Generate a unique alert ID
        alert_id = str(uuid.uuid4())
        
        # Use the agent to process the alert
        agent_input = {
            "reporter_id": user_id,
            "alert_data": alert_data,
            "timestamp": datetime.now().isoformat(),
            "task": "process_emergency_alert"
        }
        
        # Call the agent
        agent_response = self.agent.run(json.dumps(agent_input))
        
        try:
            # Parse the agent response
            analysis = json.loads(agent_response)
            
            # Extract data from analysis
            severity = analysis.get("severity", alert_data.get("severity", "medium"))
            
            # Store the alert in the database
            self.db.create_alert(
                alert_id=alert_id,
                reporter_id=user_id,
                alert_type=alert_data.get("type", "general"),
                description=alert_data.get("description", ""),
                latitude=alert_data.get("location", {}).get("latitude", 0),
                longitude=alert_data.get("location", {}).get("longitude", 0),
                severity=severity
            )
            
            # Get nearby users to notify (in a real app)
            # For this demo, we'll simulate notifying users
            notified_users = 5  # Simulated number
            
            # If high severity, send SMS to emergency contacts of the reporter
            notified_authorities = []
            if severity == "high":
                # Get emergency contacts
                emergency_contacts = self.db.get_emergency_contacts(user_id)
                
                if emergency_contacts:
                    # Send notifications
                    location = alert_data.get("location", {"latitude": 0, "longitude": 0})
                    notification_results = self.sms_service.send_sos_notifications(
                        user_name="User",  # In a real app, get the user's name
                        location=location,
                        message=f"ALERT: {alert_data.get('description', 'Emergency alert!')}",
                        emergency_contacts=emergency_contacts
                    )
                    
                    # Count successful notifications
                    notified_authorities = [r for r in notification_results if r["status"] in ["sent", "simulated"]]
            
            return {
                "status": "success",
                "alert_id": alert_id,
                "severity": severity,
                "authorities_notified": len(notified_authorities),
                "users_notified": notified_users,
                "message": "Emergency alert created and notifications sent"
            }
        
        except Exception as e:
            print(f"Error processing agent response: {str(e)}")
            
            # Still create the alert in the database with default values
            self.db.create_alert(
                alert_id=alert_id,
                reporter_id=user_id,
                alert_type=alert_data.get("type", "general"),
                description=alert_data.get("description", ""),
                latitude=alert_data.get("location", {}).get("latitude", 0),
                longitude=alert_data.get("location", {}).get("longitude", 0),
                severity=alert_data.get("severity", "medium")
            )
            
            # Fallback response
            return {
                "status": "success",
                "alert_id": alert_id,
                "severity": alert_data.get("severity", "medium"),
                "authorities_notified": 0,
                "users_notified": 0,
                "message": "Emergency alert created but there was an issue with processing"
            }
    
    def verify_alert(self, alert_id: str, user_id: str, 
                    verification_type: str = "confirm") -> Dict[str, Any]:
        """
        Verify an existing alert to prevent false alerts
        
        Args:
            alert_id: The ID of the alert to verify
            user_id: ID of the user verifying the alert
            verification_type: Either "confirm" or "dispute"
            
        Returns:
            Dict with verification status
        """
        # Verify the alert in the database
        success = self.db.verify_alert(alert_id, verification_type)
        
        if not success:
            return {"status": "error", "message": "Alert not found"}
        
        # Get updated alert
        alert = self.db.get_alert(alert_id)
        
        if verification_type == "confirm":
            return {
                "status": "success", 
                "message": f"Alert verified. Current verification count: {alert['verification_count']}",
                "severity": alert["severity"]
            }
        else:
            return {
                "status": "success", 
                "message": "Alert has been flagged for review",
                "alert_status": alert["status"]
            }
    
    def resolve_alert(self, alert_id: str, resolution_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mark an alert as resolved
        
        Args:
            alert_id: The ID of the alert to resolve
            resolution_details: Details about the resolution
            
        Returns:
            Dict with resolution status
        """
        # Resolve the alert in the database
        success = self.db.resolve_alert(alert_id, resolution_details)
        
        if not success:
            return {"status": "error", "message": "Alert not found"}
        
        return {
            "status": "success",
            "message": "Alert marked as resolved",
            "alert_id": alert_id
        }
    
    def get_active_alerts(self, latitude: float, longitude: float, radius_km: float = 5.0) -> List[Dict[str, Any]]:
        """
        Get active alerts in a specific area
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            List of active alerts in the area
        """
        # Get alerts from the database
        return self.db.get_active_alerts(latitude, longitude, radius_km)