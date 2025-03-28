import streamlit as st
import json
import uuid
from datetime import datetime
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import os
from math import radians, cos, sin, asin, sqrt
import requests
from dotenv import load_dotenv
import time
import random

# Load environment variables
load_dotenv()

# Import our modules
from create_agents import create_women_safety_agents
from agent_handlers import IncidentReportingHandler, SafetyNavigatorHandler, EmergencyAlertHandler
from database import Database
from sms_service import SMSService

# Set page configuration
st.set_page_config(
    page_title="Safe Pulse",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# Initialize SMS service
sms_service = SMSService()

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'active_journey' not in st.session_state:
    st.session_state.active_journey = None
if 'reports' not in st.session_state:
    st.session_state.reports = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'agents_initialized' not in st.session_state:
    st.session_state.agents_initialized = False
if 'emergency_contacts' not in st.session_state:
    st.session_state.emergency_contacts = []
if 'user_location' not in st.session_state:
    # Default location (can be updated with geolocation)
    st.session_state.user_location = {"latitude": 22.5726, "longitude": 88.3639}
if 'location_tracking' not in st.session_state:
    st.session_state.location_tracking = False
if 'location_sharing' not in st.session_state:
    st.session_state.location_sharing = False
if 'location_sharing_code' not in st.session_state:
    st.session_state.location_sharing_code = str(uuid.uuid4())[:8]
if 'location_history' not in st.session_state:
    st.session_state.location_history = []
if 'last_location_update' not in st.session_state:
    st.session_state.last_location_update = datetime.now().isoformat()
if 'tracking_thread_active' not in st.session_state:
    st.session_state.tracking_thread_active = False

# Initialize agents automatically
@st.cache_resource
def get_agents_and_handlers():
    try:
        # Create the agents
        agents = create_women_safety_agents()
        
        # Create handlers for each agent
        handlers = {
            "incident_handler": IncidentReportingHandler(agents["incident_reporting_agent"], db),
            "navigator_handler": SafetyNavigatorHandler(agents["safety_navigator_agent"], db),
            "alert_handler": EmergencyAlertHandler(agents["emergency_alert_agent"], db)
        }
        
        st.session_state.agents_initialized = True
        return handlers
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None

# Auto-initialize agents
handlers = get_agents_and_handlers()

# Function to get directions using OpenStreetMap Nominatim (free)
def get_directions(origin, destination, mode="walking"):
    """Get directions between two points (simplified version)"""
    # This is a simplified version that just returns a straight line
    # For a real app, you could use the OSRM API or other free routing services
    return [
        {"lat": origin["latitude"], "lng": origin["longitude"]},
        {"lat": destination["latitude"], "lng": destination["longitude"]}
    ]

# Function to calculate distance between two points
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r

# Function to get a map with OpenStreetMap tiles
def get_map(center_lat, center_lng, zoom=13):
    """Create a folium map with OpenStreetMap tiles"""
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom,
        tiles="OpenStreetMap"  
    )
    return m

# Function to simulate getting current location
def get_current_location():
    """Simulate getting the current location"""
    # In a real app, this would use the browser's geolocation API
    # For this demo, we'll just return the current location from session state
    # or simulate a small movement if tracking is active
    
    current_lat = st.session_state.user_location["latitude"]
    current_lng = st.session_state.user_location["longitude"]
    
    # If tracking is active, simulate a small movement
    if st.session_state.location_tracking:
        # Add a small random movement (up to 0.001 degrees in any direction)
        lat_movement = random.uniform(-0.0005, 0.0005)
        lng_movement = random.uniform(-0.0005, 0.0005)
        
        current_lat += lat_movement
        current_lng += lng_movement
    
    # Update the session state
    timestamp = datetime.now().isoformat()
    st.session_state.user_location = {
        "latitude": current_lat,
        "longitude": current_lng
    }
    st.session_state.last_location_update = timestamp
    
    # Add to location history (keep last 100 points)
    st.session_state.location_history.append({
        "latitude": current_lat,
        "longitude": current_lng,
        "timestamp": timestamp,
        "accuracy": random.uniform(5, 20)  # Simulate accuracy between 5-20 meters
    })
    
    if len(st.session_state.location_history) > 100:
        st.session_state.location_history = st.session_state.location_history[-100:]
    
    return {
        "latitude": current_lat,
        "longitude": current_lng,
        "timestamp": timestamp,
        "accuracy": st.session_state.location_history[-1]["accuracy"]
    }

# Function to start location tracking
def start_location_tracking():
    """Start simulated location tracking"""
    st.session_state.location_tracking = True
    
    # Get initial location
    get_current_location()
    
    return True

# Function to stop location tracking
def stop_location_tracking():
    """Stop simulated location tracking"""
    st.session_state.location_tracking = False
    return True

# Function to update location periodically (called by a button)
def update_tracked_location():
    """Update location if tracking is active"""
    if st.session_state.location_tracking:
        location_data = get_current_location()
        return location_data
    return None

# Function to generate a location sharing link
def generate_location_sharing_link():
    # In a real app, this would create a unique URL that others can access
    # For this demo, we'll just generate a code
    sharing_code = st.session_state.location_sharing_code
    return f"https://example.com/share-location/{sharing_code}"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF5757;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #FF5757;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .emergency-button {
        background-color: #FF5757;
        color: white;
        font-weight: bold;
        padding: 15px;
        border-radius: 50%;
        width: 100px;
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        cursor: pointer;
        font-size: 24px;
    }
    .info-text {
        color: #6c757d;
        font-size: 0.9rem;
    }
    .highlight {
        background-color: #ffe0e0;
        padding: 5px;
        border-radius: 5px;
    }
    .safe-area {
        color: #28a745;
    }
    .warning-area {
        color: #ffc107;
    }
    .danger-area {
        color: #dc3545;
    }
    .contact-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #FF5757;
    }
    .sos-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
    }
    .map-search-container {
        margin-bottom: 15px;
    }
    .map-search-input {
        width: 100%;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
    }
    .location-tracking-active {
        background-color: #e6f7ff;
        border-left: 4px solid #1890ff;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .location-sharing-active {
        background-color: #f6ffed;
        border-left: 4px solid #52c41a;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .sharing-code {
        font-family: monospace;
        background-color: #f5f5f5;
        padding: 5px 10px;
        border-radius: 3px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='main-header'>Safe Pulse</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/shield.png", width=80)
    st.title("Navigation")
    
    # Navigation
    page = st.radio("Choose a feature:", [
        "🏠 Home",
        "🚨 Emergency Alert System",
        "🧭 Personalized Safety Navigator",
        "📝 Anonymous Incident Reporting",
        "📍 Live Location Tracking",
        "👥 Emergency Contacts",
        "⚙️ Settings"
    ])
    
    # User profile section
    st.markdown("---")
    st.subheader("User Profile")
    
    # Display user ID
    st.info(f"User ID: {st.session_state.user_id[:8]}...")
    
    # Location status
    if st.session_state.location_tracking:
        st.markdown("""
        <div class="location-tracking-active">
            📍 Location tracking is active
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.location_sharing:
        st.markdown(f"""
        <div class="location-sharing-active">
            🔗 Location sharing is active<br>
            Code: <span class="sharing-code">{st.session_state.location_sharing_code}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Emergency button
    st.markdown("---")
    
    # SOS Button
    if st.button("🆘 SOS EMERGENCY", use_container_width=True, type="primary"):
        # Get current location
        location_data = get_current_location()
        
        # Use the current location or the last known location
        current_location = st.session_state.user_location
        
        # Get emergency contacts
        emergency_contacts = db.get_emergency_contacts(st.session_state.user_id)
        
        if not emergency_contacts:
            st.error("No emergency contacts found. Please add emergency contacts in the Settings page.")
        else:
            # Send SOS notifications
            notification_results = sms_service.send_sos_notifications(
                user_name="User",  # In a real app, get the user's name
                location=current_location,
                message="EMERGENCY! I need immediate assistance!",
                emergency_contacts=emergency_contacts
            )
            
            # Record the SOS event
            db.create_sos(
                user_id=st.session_state.user_id,
                latitude=current_location["latitude"],
                longitude=current_location["longitude"],
                message="EMERGENCY! I need immediate assistance!",
                contacts_notified=[r["contact_phone"] for r in notification_results if r["status"] in ["sent", "simulated"]]
            )
            
            st.success(f"SOS alert sent to {len(notification_results)} emergency contacts!")
    
    st.markdown("<p class='info-text' style='text-align: center;'>Click for immediate help</p>", unsafe_allow_html=True)

# Home page
if page == "🏠 Home":
    st.markdown("<h2 class='sub-header'>Welcome to Safe Pulse</h2>", unsafe_allow_html=True)
    
    # Get current location
    if st.button("Update My Location"):
        with st.spinner("Getting your location..."):
            location_data = get_current_location()
            if location_data:
                st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.image("https://img.icons8.com/color/96/000000/siren.png", width=50)
        st.markdown("### Emergency Alert System")
        st.markdown("Real-time alerts for security threats and emergencies")
        st.button("Go to Emergency Alerts", key="goto_alerts", on_click=lambda: st.session_state.update({"page": "🚨 Emergency Alert System"}))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.image("https://img.icons8.com/color/96/000000/compass.png", width=50)
        st.markdown("### Personalized Safety Navigator")
        st.markdown("AI-driven assistant for safe navigation and real-time guidance")
        st.button("Go to Safety Navigator", key="goto_navigator", on_click=lambda: st.session_state.update({"page": "🧭 Personalized Safety Navigator"}))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.image("https://img.icons8.com/color/96/000000/survey.png", width=50)
        st.markdown("### Anonymous Incident Reporting")
        st.markdown("Securely report incidents and connect with community support")
        st.button("Go to Incident Reporting", key="goto_reporting", on_click=lambda: st.session_state.update({"page": "📝 Anonymous Incident Reporting"}))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.image("https://img.icons8.com/color/96/000000/location.png", width=50)
        st.markdown("### Live Location Tracking")
        st.markdown("Share your real-time location with trusted contacts")
        st.button("Go to Location Tracking", key="goto_location", on_click=lambda: st.session_state.update({"page": "📍 Live Location Tracking"}))
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Safety statistics
    st.markdown("<h2 class='sub-header'>Safety Overview</h2>", unsafe_allow_html=True)
    
    # Sample data for demonstration
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Alerts", "3", "-1")
    col2.metric("Reported Incidents", "12", "+2")
    col3.metric("Safe Journeys", "28", "+5")
    col4.metric("Community Volunteers", "15", "+3")
    
    # Sample map
    st.markdown("<h2 class='sub-header'>Safety Map</h2>", unsafe_allow_html=True)
    
    # Get current location
    location_data = get_current_location()
    
    # Create a map centered at user's location
    m = get_map(st.session_state.user_location["latitude"], 
               st.session_state.user_location["longitude"])
    
    # Add user marker
    folium.Marker(
        location=[st.session_state.user_location["latitude"], 
                 st.session_state.user_location["longitude"]],
        popup="Your Location",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(m)
    
    # Add some sample data points
    folium.Circle(
        location=[st.session_state.user_location["latitude"], 
                 st.session_state.user_location["longitude"]],
        radius=500,
        color='green',
        fill=True,
        fill_opacity=0.2,
        tooltip='Safe Area'
    ).add_to(m)
    
    folium.Circle(
        location=[st.session_state.user_location["latitude"] - 0.005, 
                 st.session_state.user_location["longitude"] - 0.01],
        radius=300,
        color='red',
        fill=True,
        fill_opacity=0.2,
        tooltip='High Risk Area'
    ).add_to(m)
    
    folium.Circle(
        location=[st.session_state.user_location["latitude"] + 0.003, 
                 st.session_state.user_location["longitude"] - 0.005],
        radius=400,
        color='orange',
        fill=True,
        fill_opacity=0.2,
        tooltip='Medium Risk Area'
    ).add_to(m)
    
    # Display the map
    folium_static(m)
    
    # Recent activity
    st.markdown("<h2 class='sub-header'>Recent Activity</h2>", unsafe_allow_html=True)
    
    # Sample activity data
    activities = [
        {"time": "10 min ago", "type": "Alert", "description": "Suspicious person reported near Central Park"},
        {"time": "25 min ago", "type": "Journey", "description": "Safe journey completed from College St to Park Street"},
        {"time": "1 hour ago", "type": "Report", "description": "Incident report verified by 3 community members"},
        {"time": "2 hours ago", "type": "Alert", "description": "Alert resolved: Area now safe"}
    ]
    
    for activity in activities:
        st.markdown(f"**{activity['time']}** - {activity['type']}: {activity['description']}")

# Live Location Tracking page
elif page == "📍 Live Location Tracking":
    st.markdown("<h2 class='sub-header'>Live Location Tracking</h2>", unsafe_allow_html=True)
    
    # If tracking is active, update location periodically
    if st.session_state.location_tracking:
        update_tracked_location()
    
    tabs = st.tabs(["My Location", "Location Sharing", "Track History"])
    
    with tabs[0]:
        st.markdown("### Current Location")
        st.markdown("View and update your current location.")
        
        # Location tracking controls
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.location_tracking:
                if st.button("Start Location Tracking", type="primary"):
                    with st.spinner("Starting location tracking..."):
                        if start_location_tracking():
                            st.success("Location tracking started!")
                            st.rerun()
            else:
                if st.button("Stop Location Tracking", type="primary"):
                    with st.spinner("Stopping location tracking..."):
                        if stop_location_tracking():
                            st.success("Location tracking stopped!")
                            st.rerun()
        
        with col2:
            if st.button("Get Current Location"):
                with st.spinner("Getting your location..."):
                    location_data = get_current_location()
                    if location_data:
                        st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                        st.rerun()
        
        # Manual location input
        st.markdown("### Manual Location Input")
        st.markdown("You can manually set your location by entering coordinates or clicking on the map.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            manual_lat = st.number_input("Latitude", value=st.session_state.user_location["latitude"], format="%.6f", step=0.001)
        
        with col2:
            manual_lng = st.number_input("Longitude", value=st.session_state.user_location["longitude"], format="%.6f", step=0.001)
        
        if st.button("Set Manual Location"):
            st.session_state.user_location = {"latitude": manual_lat, "longitude": manual_lng}
            st.session_state.last_location_update = datetime.now().isoformat()
            
            # Add to location history
            st.session_state.location_history.append({
                "latitude": manual_lat,
                "longitude": manual_lng,
                "timestamp": st.session_state.last_location_update,
                "accuracy": 10.0  # Default accuracy for manual input
            })
            
            if len(st.session_state.location_history) > 100:
                st.session_state.location_history = st.session_state.location_history[-100:]
            
            st.success(f"Location manually set to: {manual_lat:.6f}, {manual_lng:.6f}")
            st.rerun()
        
        # Display current location
        st.markdown("### Location Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Latitude", f"{st.session_state.user_location['latitude']:.6f}")
        
        with col2:
            st.metric("Longitude", f"{st.session_state.user_location['longitude']:.6f}")
        
        with col3:
            st.metric("Last Updated", st.session_state.last_location_update.split('T')[1].split('.')[0])
        
        # Show location on map
        st.markdown("### Location Map")
        
        # Create a map centered at user's location
        m = get_map(st.session_state.user_location["latitude"], 
                   st.session_state.user_location["longitude"],
                   zoom=15)
        
        # Add user marker
        folium.Marker(
            location=[st.session_state.user_location["latitude"], 
                     st.session_state.user_location["longitude"]],
            popup="Your Current Location",
            icon=folium.Icon(color="blue", icon="user")
        ).add_to(m)
        
        # Add accuracy circle if available
        if st.session_state.location_history and "accuracy" in st.session_state.location_history[-1]:
            accuracy = st.session_state.location_history[-1]["accuracy"]
            folium.Circle(
                location=[st.session_state.user_location["latitude"], 
                         st.session_state.user_location["longitude"]],
                radius=accuracy,  # Accuracy in meters
                color='blue',
                fill=True,
                fill_opacity=0.1,
                tooltip=f'Accuracy: {accuracy:.1f} meters'
            ).add_to(m)
        
        # Display the map
        folium_static(m)
        
        # Location tracking status
        if st.session_state.location_tracking:
            st.info("📍 Location tracking is active. Your location will be updated automatically.")
            
            # Add a button to manually update location while tracking
            if st.button("Update Tracked Location"):
                location_data = update_tracked_location()
                if location_data:
                    st.success(f"Location updated: {location_data['latitude']:.6f}, {location_data['longitude']:.6f}")
                    st.rerun()
        else:
            st.warning("⚠️ Location tracking is not active. Click 'Start Location Tracking' to enable automatic updates.")
    
    with tabs[1]:
        st.markdown("### Share Your Location")
        st.markdown("Share your real-time location with trusted contacts.")
        
        # Location sharing controls
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.location_sharing:
                if st.button("Start Location Sharing", type="primary"):
                    # Enable location tracking if not already enabled
                    if not st.session_state.location_tracking:
                        with st.spinner("Starting location tracking..."):
                            start_location_tracking()
                    
                    # Generate sharing code if needed
                    if not st.session_state.location_sharing_code:
                        st.session_state.location_sharing_code = str(uuid.uuid4())[:8]
                    
                    st.session_state.location_sharing = True
                    st.success("Location sharing started!")
                    st.rerun()
            else:
                if st.button("Stop Location Sharing", type="primary"):
                    st.session_state.location_sharing = False
                    st.success("Location sharing stopped!")
                    st.rerun()
        
        with col2:
            if st.button("Generate New Sharing Code"):
                st.session_state.location_sharing_code = str(uuid.uuid4())[:8]
                st.success("New sharing code generated!")
                st.rerun()
        
        # Display sharing information
        if st.session_state.location_sharing:
            st.markdown("### Sharing Details")
            
            st.markdown(f"""
            <div class="card">
                <h4>Your location is being shared</h4>
                <p>Share this code with trusted contacts:</p>
                <h3 class="sharing-code">{st.session_state.location_sharing_code}</h3>
                <p class="info-text">They can use this code to view your real-time location</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Share via SMS option
            st.markdown("### Share via SMS")
            
            # Get emergency contacts
            emergency_contacts = db.get_emergency_contacts(st.session_state.user_id)
            
            if emergency_contacts:
                selected_contacts = st.multiselect(
                    "Select contacts to share with",
                    options=[contact["name"] for contact in emergency_contacts],
                    format_func=lambda x: x
                )
                
                if st.button("Send Sharing Link via SMS"):
                    if selected_contacts:
                        sharing_link = generate_location_sharing_link()
                        
                        # Send SMS to each selected contact
                        sent_count = 0
                        for contact_name in selected_contacts:
                            # Find the contact in the list
                            contact = next((c for c in emergency_contacts if c["name"] == contact_name), None)
                            
                            if contact:
                                # Create message
                                message = f"I'm sharing my live location with you. Use this code to track me: {st.session_state.location_sharing_code}\nOr click this link: {sharing_link}"
                                
                                # Send SMS
                                result = sms_service.send_sms(contact["phone"], message)
                                
                                if result["status"] in ["sent", "simulated"]:
                                    sent_count += 1
                        
                        st.success(f"Location sharing information sent to {sent_count} contacts!")
                    else:
                        st.error("Please select at least one contact.")
            else:
                st.warning("No emergency contacts found. Add contacts in the Emergency Contacts page.")
        else:
            st.info("Location sharing is not active. Click 'Start Location Sharing' to share your location with trusted contacts.")
    
    with tabs[2]:
        st.markdown("### Location History")
        st.markdown("View your location history and movement patterns.")
        
        if st.session_state.location_history:
            # Display history on map
            st.markdown("### Movement Map")
            
            # Create a map centered at the average of all points
            avg_lat = sum(point["latitude"] for point in st.session_state.location_history) / len(st.session_state.location_history)
            avg_lng = sum(point["longitude"] for point in st.session_state.location_history) / len(st.session_state.location_history)
            
            m = get_map(avg_lat, avg_lng, zoom=14)
            
            # Add markers for each point
            for i, point in enumerate(st.session_state.location_history):
                # Only add markers for every 5th point to avoid clutter
                if i % 5 == 0 or i == len(st.session_state.location_history) - 1:
                    folium.Marker(
                        location=[point["latitude"], point["longitude"]],
                        popup=f"Time: {point['timestamp'].split('T')[1].split('.')[0]}",
                        icon=folium.Icon(color="blue" if i < len(st.session_state.location_history) - 1 else "red", 
                                        icon="record" if i < len(st.session_state.location_history) - 1 else "user")
                    ).add_to(m)
            
            # Add a line connecting all points
            folium.PolyLine(
                locations=[[point["latitude"], point["longitude"]] for point in st.session_state.location_history],
                color="blue",
                weight=3,
                opacity=0.7
            ).add_to(m)
            
            # Display the map
            folium_static(m)
            
            # Display history table
            st.markdown("### Location Data")
            
            # Convert to DataFrame for display
            history_df = pd.DataFrame([
                {
                    "Time": point["timestamp"].split('T')[1].split('.')[0],
                    "Latitude": f"{point['latitude']:.6f}",
                    "Longitude": f"{point['longitude']:.6f}",
                    "Accuracy (m)": f"{point.get('accuracy', 'N/A')}"
                }
                for point in reversed(st.session_state.location_history)
            ])
            
            st.dataframe(history_df, use_container_width=True)
            
            # Clear history option
            if st.button("Clear Location History"):
                st.session_state.location_history = []
                st.success("Location history cleared!")
                st.rerun()
        else:
            st.info("No location history available. Start location tracking to record your movements.")

# Emergency Alert System page
elif page == "🚨 Emergency Alert System":
    st.markdown("<h2 class='sub-header'>Emergency Alert System</h2>", unsafe_allow_html=True)
    
    tabs = st.tabs(["Create Alert", "View Alerts", "Verify Alerts"])
    
    with tabs[0]:
        st.markdown("### Report an Emergency")
        st.markdown("Create an alert to notify authorities and nearby users about a safety concern.")
        
        alert_type = st.selectbox("Alert Type", ["security", "safety", "emergency", "suspicious_person", "unsafe_area"])
        alert_description = st.text_area("Description", placeholder="Describe the situation in detail...")
        
        # Location input with map
        st.markdown("### Alert Location")
        
        # Get current location button
        if st.button("Use My Current Location"):
            with st.spinner("Getting your location..."):
                location_data = get_current_location()
                if location_data:
                    st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                    st.rerun()
        
        # Location search (simplified)
        location_search = st.text_input("Search location (e.g., 'New York, NY')", 
                                       key="alert_location_search",
                                       help="Enter a location to search")
        
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=st.session_state.user_location["latitude"], format="%.6f")
        with col2:
            longitude = st.number_input("Longitude", value=st.session_state.user_location["longitude"], format="%.6f")
        
        # Show location on map
        alert_map = get_map(latitude, longitude, zoom=15)
        folium.Marker(
            location=[latitude, longitude],
            popup="Alert Location",
            icon=folium.Icon(color="red", icon="warning-sign")
        ).add_to(alert_map)
        folium_static(alert_map)
        
        severity = st.select_slider("Severity", options=["low", "medium", "high"], value="medium")
        
        if st.button("Submit Alert", type="primary"):
            alert_data = {
                "type": alert_type,
                "description": alert_description,
                "location": {"latitude": latitude, "longitude": longitude},
                "severity": severity
            }
            
            with st.spinner("Processing alert..."):
                response = handlers["alert_handler"].create_alert(st.session_state.user_id, alert_data)
            
            if response["status"] == "success":
                st.success(f"Alert created successfully! Alert ID: {response['alert_id']}")
                st.session_state.alerts.append({
                    "id": response["alert_id"],
                    "type": alert_type,
                    "description": alert_description,
                    "severity": severity,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Show notification details
                st.markdown("### Alert Notifications")
                st.markdown(f"- **Authorities Notified**: {response['authorities_notified']}")
                st.markdown(f"- **Users Notified**: {response['users_notified']}")
            else:
                st.error("Failed to create alert. Please try again.")
    
    with tabs[1]:
        st.markdown("### Active Alerts")
        st.markdown("View alerts in your area and get safety information.")
        
        # Location input for viewing alerts
        st.markdown("### Search Area")
        
        # Get current location button
        if st.button("Use My Current Location", key="view_use_current"):
            with st.spinner("Getting your location..."):
                location_data = get_current_location()
                if location_data:
                    st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                    st.rerun()
        
        # Location search (simplified)
        view_location_search = st.text_input("Search location (e.g., 'New York, NY')", 
                                           key="view_location_search",
                                           help="Enter a location to search")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            view_latitude = st.number_input("Latitude", value=st.session_state.user_location["latitude"], format="%.6f", key="view_lat")
        with col2:
            view_longitude = st.number_input("Longitude", value=st.session_state.user_location["longitude"], format="%.6f", key="view_lng")
        with col3:
            radius = st.number_input("Radius (km)", value=5.0, min_value=0.1, max_value=50.0)
        
        if st.button("Get Alerts"):
            location = {"latitude": view_latitude, "longitude": view_longitude}
            
            with st.spinner("Fetching alerts..."):
                alerts = handlers["alert_handler"].get_active_alerts(view_latitude, view_longitude, radius)
            
            if alerts:
                # Create a map
                m = get_map(view_latitude, view_longitude, zoom=13)
                
                # Add user location marker
                folium.Marker(
                    location=[view_latitude, view_longitude],
                    popup="Your Location",
                    icon=folium.Icon(color="blue", icon="user")
                ).add_to(m)
                
                # Add circle for search radius
                folium.Circle(
                    location=[view_latitude, view_longitude],
                    radius=radius * 1000,  # Convert to meters
                    color='blue',
                    fill=False,
                    popup="Search Radius"
                ).add_to(m)
                
                # Add alert markers
                for alert in alerts:
                    color = "red" if alert["severity"] == "high" else "orange" if alert["severity"] == "medium" else "green"
                    folium.Marker(
                        location=[alert["latitude"], alert["longitude"]],
                        popup=f"{alert['alert_type']} - {alert['description']}",
                        tooltip=f"{alert['severity'].upper()} - {alert['alert_type']}",
                        icon=folium.Icon(color=color, icon="warning-sign")
                    ).add_to(m)
                
                # Display the map
                folium_static(m)
                
                # Display alerts in a table
                st.markdown("### Alert Details")
                
                for alert in alerts:
                    severity_class = "danger-area" if alert["severity"] == "high" else "warning-area" if alert["severity"] == "medium" else "safe-area"
                    
                    st.markdown(f"""
                    <div class='card'>
                        <h4 class='{severity_class}'>{alert['severity'].upper()} - {alert['alert_type']}</h4>
                        <p>{alert['description']}</p>
                        <p class='info-text'>Distance: {alert.get('distance_km', 'N/A')} km • Reported: {alert['created_at']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No active alerts in this area.")
    
    with tabs[2]:
        st.markdown("### Verify Alerts")
        st.markdown("Help verify alerts to prevent false alarms and improve community safety.")
        
        # Display alerts that can be verified
        if st.session_state.alerts:
            for i, alert in enumerate(st.session_state.alerts):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class='card'>
                        <h4>{alert['type']}</h4>
                        <p>{alert['description']}</p>
                        <p class='info-text'>Severity: {alert['severity']} • Reported: {alert['timestamp']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("Confirm", key=f"confirm_{i}"):
                        with st.spinner("Verifying alert..."):
                            response = handlers["alert_handler"].verify_alert(alert["id"], st.session_state.user_id, "confirm")
                        
                        if response["status"] == "success":
                            st.success(response["message"])
                        else:
                            st.error("Verification failed. Please try again.")
                    
                    if st.button("Dispute", key=f"dispute_{i}"):
                        with st.spinner("Disputing alert..."):
                            response = handlers["alert_handler"].verify_alert(alert["id"], st.session_state.user_id, "dispute")
                        
                        if response["status"] == "success":
                            st.success(response["message"])
                        else:
                            st.error("Dispute failed. Please try again.")
        else:
            st.info("No alerts available for verification.")

# Personalized Safety Navigator page
elif page == "🧭 Personalized Safety Navigator":
    st.markdown("<h2 class='sub-header'>Personalized Safety Navigator</h2>", unsafe_allow_html=True)
    
    tabs = st.tabs(["Start Journey", "Active Journey", "Emergency"])
    
    with tabs[0]:
        st.markdown("### Plan Your Journey")
        st.markdown("Get personalized safety recommendations for your journey.")
        
        # User profile setup
        if "navigator_profile_setup" not in st.session_state:
            st.markdown("#### Set Up Your Profile")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ec_name = st.text_input("Emergency Contact Name")
                ec_phone = st.text_input("Emergency Contact Phone")
            
            with col2:
                has_safety_app = st.checkbox("I have a safety app installed", value=True)
                preferred_transport = st.selectbox("Preferred Transportation", ["walking", "public_transport", "private_vehicle", "taxi"])
            
            # Safety preferences
            st.markdown("#### Safety Preferences")
            avoid_poorly_lit = st.checkbox("Avoid poorly lit areas", value=True)
            prefer_main_roads = st.checkbox("Prefer main roads", value=True)
            alert_threshold = st.select_slider("Alert Threshold", options=["low", "medium", "high"], value="medium")
            
            if st.button("Save Profile"):
                # Create profile data
                profile_data = {
                    "emergency_contacts": [
                        {"name": ec_name, "phone": ec_phone}
                    ],
                    "has_safety_app": has_safety_app,
                    "preferred_transportation": preferred_transport,
                    "safety_preferences": {
                        "avoid_poorly_lit_areas": avoid_poorly_lit,
                        "prefer_main_roads": prefer_main_roads,
                        "alert_threshold": alert_threshold
                    }
                }
                
                # Register user
                with st.spinner("Saving profile..."):
                    response = handlers["navigator_handler"].register_user(st.session_state.user_id, profile_data)
                
                if response["status"] == "success":
                    st.success("Profile saved successfully!")
                    st.session_state.navigator_profile_setup = True
                    
                    # Add emergency contact to database
                    if ec_name and ec_phone:
                        db.add_emergency_contact(st.session_state.user_id, ec_name, ec_phone)
                    
                    st.rerun()
                else:
                    st.error("Failed to save profile. Please try again.")
        
        else:
            # Journey planning
            st.markdown("#### Plan Your Route")
            
            # Starting point
            st.markdown("##### Starting Point")
            
            # Get current location button
            if st.button("Use My Current Location", key="start_use_current"):
                with st.spinner("Getting your location..."):
                    location_data = get_current_location()
                    if location_data:
                        st.success(f"Starting location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                        st.rerun()
            
            start_location_search = st.text_input("Search starting location", 
                                                key="start_location_search",
                                                help="Enter a location to search")
            
            col1, col2 = st.columns(2)
            with col1:
                start_lat = st.number_input("Latitude", value=st.session_state.user_location["latitude"], format="%.6f", key="start_lat")
            with col2:
                start_lng = st.number_input("Longitude", value=st.session_state.user_location["longitude"], format="%.6f", key="start_lng")
            
            # Destination
            st.markdown("##### Destination")
            dest_location_search = st.text_input("Search destination", 
                                               key="dest_location_search",
                                               help="Enter a location to search")
            
            col1, col2 = st.columns(2)
            with col1:
                dest_lat = st.number_input("Latitude", value=st.session_state.user_location["latitude"] + 0.01, format="%.6f", key="dest_lat")
            with col2:
                dest_lng = st.number_input("Longitude", value=st.session_state.user_location["longitude"] + 0.01, format="%.6f", key="dest_lng")
            
            travel_mode = st.selectbox("Travel Mode", ["walking", "driving", "bicycling", "transit"])
            
            # Enable live tracking
            enable_tracking = st.checkbox("Enable live location tracking during journey", value=True)
            
            # Get directions
            origin = {"latitude": start_lat, "longitude": start_lng}
            destination = {"latitude": dest_lat, "longitude": dest_lng}
            
            # Create a map to visualize the journey
            m = get_map((start_lat + dest_lat)/2, (start_lng + dest_lng)/2, zoom=13)
            
            # Add markers for start and destination
            folium.Marker(
                location=[start_lat, start_lng],
                popup="Starting Point",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)
            
            folium.Marker(
                location=[dest_lat, dest_lng],
                popup="Destination",
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(m)
            
            # Get route points
            route_points = get_directions(origin, destination, travel_mode)
            
            # Add route line
            route_coords = [[point["lat"], point["lng"]] for point in route_points]
            folium.PolyLine(
                locations=route_coords,
                color="blue",
                weight=3,
                opacity=0.7
            ).add_to(m)
            
            # Add sample risk areas
            folium.Circle(
                location=[start_lat + 0.005, start_lng + 0.005],
                radius=300,
                color='red',
                fill=True,
                fill_opacity=0.2,
                tooltip='High Risk Area'
            ).add_to(m)
            
            folium.Circle(
                location=[start_lat + 0.008, start_lng + 0.003],
                radius=200,
                color='orange',
                fill=True,
                fill_opacity=0.2,
                tooltip='Medium Risk Area'
            ).add_to(m)
            
            # Display the map
            folium_static(m)
            
            if st.button("Start Journey", type="primary"):
                # Start location tracking if enabled
                if enable_tracking and not st.session_state.location_tracking:
                    with st.spinner("Starting location tracking..."):
                        start_location_tracking()
                
                start_location = {"latitude": start_lat, "longitude": start_lng}
                destination = {"latitude": dest_lat, "longitude": dest_lng}
                
                with st.spinner("Analyzing route safety..."):
                    response = handlers["navigator_handler"].start_journey(
                        st.session_state.user_id, 
                        start_location, 
                        destination, 
                        travel_mode
                    )
                
                if response["status"] == "success":
                    st.success("Journey started successfully!")
                    st.session_state.active_journey = {
                        "id": response["journey_id"],
                        "start": start_location,
                        "destination": destination,
                        "route_safety": response["route_safety"],
                        "recommendations": response["safety_recommendations"],
                        "travel_mode": travel_mode
                    }
                    
                    # Display safety information
                    safety_level = response["route_safety"]["overall_risk"]
                    safety_class = "danger-area" if safety_level == "high" else "warning-area" if safety_level == "medium" else "safe-area"
                    
                    st.markdown(f"""
                    <div class='card'>
                        <h4>Route Safety: <span class='{safety_class}'>{safety_level.upper()}</span></h4>
                        <p>Time factor: {response["route_safety"]["time_factor"]}</p>
                        <p>Alternative routes available: {"Yes" if response["route_safety"]["alternative_routes_available"] else "No"}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### Safety Recommendations")
                    for i, rec in enumerate(response["safety_recommendations"], 1):
                        st.markdown(f"{i}. {rec}")
                else:
                    st.error("Failed to start journey. Please try again.")
    
    with tabs[1]:
        st.markdown("### Active Journey")
        
        if st.session_state.active_journey:
            journey = st.session_state.active_journey
            
            st.markdown(f"""
            <div class='card'>
                <h4>Journey in Progress</h4>
                <p>From: ({journey["start"]["latitude"]}, {journey["start"]["longitude"]})</p>
                <p>To: ({journey["destination"]["latitude"]}, {journey["destination"]["longitude"]})</p>
                <p>Travel Mode: {journey["travel_mode"]}</p>
                <p class='info-text'>Journey ID: {journey["id"]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Update location
            st.markdown("#### Update Your Location")
            
            # Get current location button
            if st.button("Use My Current Location", key="journey_use_current"):
                with st.spinner("Getting your location..."):
                    location_data = get_current_location()
                    if location_data:
                        st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                        st.rerun()
            
            col1, col2 = st.columns(2)
            
            with col1:
                current_lat = st.number_input("Current Latitude", value=st.session_state.user_location["latitude"], format="%.6f")
            with col2:
                current_lng = st.number_input("Current Longitude", value=st.session_state.user_location["longitude"], format="%.6f")
            
            # Update user location in session state
            st.session_state.user_location = {"latitude": current_lat, "longitude": current_lng}
            
            # Create a map to visualize the journey progress
            m = get_map(current_lat, current_lng, zoom=13)
            
            # Add markers for start, current location, and destination
            folium.Marker(
                location=[journey["start"]["latitude"], journey["start"]["longitude"]],
                popup="Starting Point",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)
            
            folium.Marker(
                location=[current_lat, current_lng],
                popup="Current Location",
                icon=folium.Icon(color="blue", icon="user")
            ).add_to(m)
            
            folium.Marker(
                location=[journey["destination"]["latitude"], journey["destination"]["longitude"]],
                popup="Destination",
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(m)
            
            # Get route points
            route_points = get_directions(
                journey["start"], 
                journey["destination"], 
                journey["travel_mode"]
            )
            
            # Add route line
            route_coords = [[point["lat"], point["lng"]] for point in route_points]
            folium.PolyLine(
                locations=route_coords,
                color="blue",
                weight=3,
                opacity=0.7
            ).add_to(m)
            
            # Add a line from current location to destination
            current_to_dest = get_directions(
                {"latitude": current_lat, "longitude": current_lng},
                journey["destination"],
                journey["travel_mode"]
            )
            current_to_dest_coords = [[point["lat"], point["lng"]] for point in current_to_dest]
            folium.PolyLine(
                locations=current_to_dest_coords,
                color="green",
                weight=3,
                opacity=0.7,
                dash_array="5"
            ).add_to(m)
            
            # Display the map
            folium_static(m)
            
            # Location tracking status
            if st.session_state.location_tracking:
                st.info("📍 Live location tracking is active. Your location is being updated automatically.")
            else:
                st.warning("⚠️ Live location tracking is not active. Enable tracking for real-time updates.")
                if st.button("Enable Live Tracking"):
                    with st.spinner("Starting location tracking..."):
                        if start_location_tracking():
                            st.success("Location tracking started!")
                            st.rerun()
            
            if st.button("Update Location"):
                current_location = {"latitude": current_lat, "longitude": current_lng}
                
                with st.spinner("Updating location..."):
                    response = handlers["navigator_handler"].update_location(journey["id"], current_location)
                
                if response["status"] == "success":
                    st.success("Location updated successfully!")
                    
                    # Display nearby risks if any
                    if response["nearby_risks"]:
                        st.markdown("### Nearby Risks")
                        for risk in response["nearby_risks"]:
                            risk_class = "danger-area" if risk["risk_level"] == "high" else "warning-area" if risk["risk_level"] == "medium" else "safe-area"
                            
                            st.markdown(f"""
                            <div class='card'>
                                <h4 class='{risk_class}'>{risk["risk_level"].upper()} Risk Area</h4>
                                <p>{risk["reason"]}</p>
                                <p class='info-text'>Distance: {risk["distance_km"]} km</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No risks detected in your current area.")
                    
                    # Display alerts if any
                    if response["alerts"]:
                        st.markdown("### Safety Alerts")
                        for alert in response["alerts"]:
                            alert_class = "danger-area" if alert["risk_level"] == "high" else "warning-area" if alert["risk_level"] == "medium" else "safe-area"
                            
                            st.markdown(f"""
                            <div class='card'>
                                <h4 class='{alert_class}'>{alert["type"]}</h4>
                                <p>{alert["message"]}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Check if destination reached
                    if response["destination_reached"]:
                        st.balloons()
                        st.success("Congratulations! You have reached your destination safely.")
                        
                        # End the journey
                        end_response = handlers["navigator_handler"].end_journey(journey["id"])
                        
                        if end_response["status"] == "success":
                            st.markdown("### Journey Summary")
                            st.markdown(f"""
                            <div class='card'>
                                <h4>Journey Completed</h4>
                                <p>Safety Score: {end_response["summary"]["safety_score"]}/100</p>
                                <p>Total Alerts: {end_response["summary"]["total_alerts"]}</p>
                                <p>Start Time: {end_response["summary"]["start_time"]}</p>
                                <p>End Time: {end_response["summary"]["end_time"]}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Clear active journey
                            st.session_state.active_journey = None
                else:
                    st.error("Failed to update location. Please try again.")
            
            # Share journey option
            st.markdown("### Share Journey Status")
            
            if st.button("Share My Journey Status"):
                # Get emergency contacts
                emergency_contacts = db.get_emergency_contacts(st.session_state.user_id)
                
                if emergency_contacts:
                    selected_contacts = st.multiselect(
                        "Select contacts to share with",
                        options=[contact["name"] for contact in emergency_contacts],
                        format_func=lambda x: x
                    )
                    
                    if st.button("Send Journey Status via SMS", key="send_journey_status"):
                        if selected_contacts:
                            # Calculate distance to destination
                            distance_to_dest = calculate_distance(
                                current_lat, current_lng,
                                journey["destination"]["latitude"], journey["destination"]["longitude"]
                            )
                            
                            # Create message
                            message = f"I'm currently on a journey. My current location is: {current_lat:.4f}, {current_lng:.4f}. I'm {distance_to_dest:.2f} km away from my destination. View my location: https://www.openstreetmap.org/?mlat={current_lat}&mlon={current_lng}#map=15/{current_lat}/{current_lng}"
                            
                            # Send SMS to each selected contact
                            sent_count = 0
                            for contact_name in selected_contacts:
                                # Find the contact in the list
                                contact = next((c for c in emergency_contacts if c["name"] == contact_name), None)
                                
                                if contact:
                                    # Send SMS
                                    result = sms_service.send_sms(contact["phone"], message)
                                    
                                    if result["status"] in ["sent", "simulated"]:
                                        sent_count += 1
                            
                            st.success(f"Journey status sent to {sent_count} contacts!")
                        else:
                            st.error("Please select at least one contact.")
                else:
                    st.warning("No emergency contacts found. Add contacts in the Emergency Contacts page.")
            
            if st.button("End Journey"):
                with st.spinner("Ending journey..."):
                    response = handlers["navigator_handler"].end_journey(journey["id"])
                
                if response["status"] == "success":
                    st.success("Journey ended successfully!")
                    st.session_state.active_journey = None
                    
                    # Stop location tracking if it was started for this journey
                    if st.session_state.location_tracking:
                        stop_location_tracking()
                    
                    st.rerun()
                else:
                    st.error("Failed to end journey. Please try again.")
        else:
            st.info("No active journey. Start a journey from the 'Start Journey' tab.")
    
    with tabs[2]:
        st.markdown("### Emergency Mode")
        st.markdown("Activate emergency mode to alert your contacts and authorities.")
        
        if st.session_state.active_journey:
            emergency_type = st.selectbox("Emergency Type", [
                "being_followed", "suspicious_person", "physical_threat", 
                "unsafe_environment", "medical_emergency", "other"
            ])
            
            emergency_description = st.text_area("Description", placeholder="Describe your emergency situation...")
            
            # Get current location button
            if st.button("Use My Current Location", key="emergency_use_current"):
                with st.spinner("Getting your location..."):
                    location_data = get_current_location()
                    if location_data:
                        st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                        st.rerun()
            
            # Get current location
            current_lat = st.session_state.user_location["latitude"]
            current_lng = st.session_state.user_location["longitude"]
            
            # Show location on map
            emergency_map = get_map(current_lat, current_lng, zoom=15)
            folium.Marker(
                location=[current_lat, current_lng],
                popup="Your Location",
                icon=folium.Icon(color="red", icon="exclamation")
            ).add_to(emergency_map)
            folium_static(emergency_map)
            
            if st.button("TRIGGER EMERGENCY", type="primary"):
                emergency_details = {
                    "type": emergency_type,
                    "description": emergency_description,
                    "latitude": current_lat,
                    "longitude": current_lng
                }
                
                with st.spinner("Activating emergency mode..."):
                    response = handlers["navigator_handler"].trigger_emergency(
                        st.session_state.active_journey["id"], 
                        emergency_details
                    )
                
                if response["status"] == "success":
                    st.success("Emergency mode activated!")
                    st.markdown(f"""
                    <div class='card'>
                        <h4 class='danger-area'>EMERGENCY ACTIVATED</h4>
                        <p>Emergency ID: {response["emergency_id"]}</p>
                        <p>Contacts Notified: {response["notified_contacts"]}</p>
                        <p>Authorities Alerted: {"Yes" if response["authorities_alerted"] else "No"}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show notification details
                    if "notification_results" in response:
                        st.markdown("### Notification Details")
                        for result in response["notification_results"]:
                            status_icon = "✅" if result["status"] in ["sent", "simulated"] else "❌"
                            st.markdown(f"{status_icon} **{result['contact_name']}**: {result['contact_phone']}")
                else:
                    st.error("Failed to activate emergency mode. Please try again.")
        else:
            st.warning("You need an active journey to trigger emergency mode.")
            
            # Quick emergency option
            st.markdown("### Quick Emergency")
            st.markdown("Use this option if you need immediate help without an active journey.")
            
            # Get current location button
            if st.button("Use My Current Location", key="quick_emergency_use_current"):
                with st.spinner("Getting your location..."):
                    location_data = get_current_location()
                    if location_data:
                        st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                        st.rerun()
            
            col1, col2 = st.columns(2)
            
            with col1:
                quick_lat = st.number_input("Your Latitude", value=st.session_state.user_location["latitude"], format="%.6f")
            with col2:
                quick_lng = st.number_input("Your Longitude", value=st.session_state.user_location["longitude"], format="%.6f")
            
            # Update user location in session state
            st.session_state.user_location = {"latitude": quick_lat, "longitude": quick_lng}
            
            quick_description = st.text_area("Emergency Description", placeholder="Describe your emergency situation...")
            
            # Show location on map
            quick_map = get_map(quick_lat, quick_lng, zoom=15)
            folium.Marker(
                location=[quick_lat, quick_lng],
                popup="Your Location",
                icon=folium.Icon(color="red", icon="exclamation")
            ).add_to(quick_map)
            folium_static(quick_map)
            
            if st.button("SEND EMERGENCY ALERT", type="primary"):
                # Create an emergency alert
                alert_data = {
                    "type": "emergency",
                    "description": quick_description,
                    "location": {"latitude": quick_lat, "longitude": quick_lng},
                    "severity": "high"
                }
                
                with st.spinner("Sending emergency alert..."):
                    response = handlers["alert_handler"].create_alert(st.session_state.user_id, alert_data)
                
                if response["status"] == "success":
                    st.success("Emergency alert sent successfully!")
                    st.markdown(f"""
                    <div class='card'>
                        <h4 class='danger-area'>EMERGENCY ALERT SENT</h4>
                        <p>Alert ID: {response["alert_id"]}</p>
                        <p>Authorities Notified: {response["authorities_notified"]}</p>
                        <p>Users Notified: {response["users_notified"]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Also send to emergency contacts
                    emergency_contacts = db.get_emergency_contacts(st.session_state.user_id)
                    
                    if emergency_contacts:
                        notification_results = sms_service.send_sos_notifications(
                            user_name="User",  # In a real app, get the user's name
                            location={"latitude": quick_lat, "longitude": quick_lng},
                            message=f"EMERGENCY! {quick_description}",
                            emergency_contacts=emergency_contacts
                        )
                        
                        st.success(f"Emergency alert also sent to {len(notification_results)} emergency contacts!")
                else:
                    st.error("Failed to send emergency alert. Please try again.")

# Anonymous Incident Reporting page
elif page == "📝 Anonymous Incident Reporting":
    st.markdown("<h2 class='sub-header'>Anonymous Incident Reporting</h2>", unsafe_allow_html=True)
    
    tabs = st.tabs(["Submit Report", "View Reports", "Get Support"])
    
    with tabs[0]:
        st.markdown("### Report an Incident")
        st.markdown("Submit an anonymous report about a safety concern or incident.")
        
        incident_description = st.text_area("Incident Description", placeholder="Describe what happened in detail...")
        
        # Location input with map
        st.markdown("### Incident Location")
        
        # Get current location button
        if st.button("Use My Current Location", key="incident_use_current"):
            with st.spinner("Getting your location..."):
                location_data = get_current_location()
                if location_data:
                    st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                    st.rerun()
        
        # Location search (simplified)
        incident_location_search = st.text_input("Search location", 
                                               key="incident_location_search",
                                               help="Enter a location to search")
        
        col1, col2 = st.columns(2)
        with col1:
            incident_lat = st.number_input("Incident Latitude", value=st.session_state.user_location["latitude"], format="%.6f")
        with col2:
            incident_lng = st.number_input("Incident Longitude", value=st.session_state.user_location["longitude"], format="%.6f")
        
        # Show location on map
        incident_map = get_map(incident_lat, incident_lng, zoom=15)
        folium.Marker(
            location=[incident_lat, incident_lng],
            popup="Incident Location",
            icon=folium.Icon(color="orange", icon="info-sign")
        ).add_to(incident_map)
        folium_static(incident_map)
        
        st.markdown("""
        <p class='info-text'>Your report will be anonymized to protect your identity. 
        Personal information like names, phone numbers, and email addresses will be removed.</p>
        """, unsafe_allow_html=True)
        
        if st.button("Submit Report", type="primary"):
            with st.spinner("Processing report..."):
                response = handlers["incident_handler"].submit_report(
                    st.session_state.user_id,
                    incident_description,
                    {"latitude": incident_lat, "longitude": incident_lng}
                )
            
            if "report_id" in response:
                st.success("Report submitted successfully!")
                
                # Store report in session state
                st.session_state.reports.append({
                    "id": response["report_id"],
                    "description": incident_description,
                    "location": {"latitude": incident_lat, "longitude": incident_lng},
                    "severity": response["severity"],
                    "categories": response["categories"],
                    "timestamp": datetime.now().isoformat()
                })
                
                # Display report details
                severity_class = "danger-area" if response["severity"] == "high" else "warning-area" if response["severity"] == "medium" else "safe-area"
                
                st.markdown(f"""
                <div class='card'>
                    <h4>Report Submitted</h4>
                    <p>Report ID: {response["report_id"]}</p>
                    <p>Severity: <span class='{severity_class}'>{response["severity"].upper()}</span></p>
                    <p>Categories: {", ".join(response["categories"])}</p>
                    <p>Immediate Action Required: {"Yes" if response["requires_immediate_action"] else "No"}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if response["requires_immediate_action"]:
                    st.warning("This report has been flagged for immediate action. Authorities have been notified.")
            else:
                st.error("Failed to submit report. Please try again.")
    
    with tabs[1]:
        st.markdown("### View Reports")
        st.markdown("View anonymized reports in your area to stay informed about safety concerns.")
        
        # Location input with map
        st.markdown("### Search Area")
        
        # Get current location button
        if st.button("Use My Current Location", key="view_report_use_current"):
            with st.spinner("Getting your location..."):
                location_data = get_current_location()
                if location_data:
                    st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                    st.rerun()
        
        # Location search (simplified)
        view_report_location_search = st.text_input("Search location", 
                                                  key="view_report_location_search",
                                                  help="Enter a location to search")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            view_report_lat = st.number_input("Latitude", value=st.session_state.user_location["latitude"], format="%.6f", key="view_report_lat")
        with col2:
            view_report_lng = st.number_input("Longitude", value=st.session_state.user_location["longitude"], format="%.6f", key="view_report_lng")
        with col3:
            report_radius = st.number_input("Radius (km)", value=5.0, min_value=0.1, max_value=50.0)
        
        if st.button("Get Reports"):
            with st.spinner("Fetching reports..."):
                reports = handlers["incident_handler"].get_reports_by_area(view_report_lat, view_report_lng, report_radius)
            
            if reports:
                # Create a map
                m = get_map(view_report_lat, view_report_lng, zoom=13)
                
                # Add user location marker
                folium.Marker(
                    location=[view_report_lat, view_report_lng],
                    popup="Your Location",
                    icon=folium.Icon(color="blue", icon="user")
                ).add_to(m)
                
                # Add circle for search radius
                folium.Circle(
                    location=[view_report_lat, view_report_lng],
                    radius=report_radius * 1000,  # Convert to meters
                    color='blue',
                    fill=False,
                    popup="Search Radius"
                ).add_to(m)
                
                # Add report markers
                for report in reports:
                    # Create a marker for each report
                    color = "red" if report["severity"] == "high" else "orange" if report["severity"] == "medium" else "green"
                    folium.Marker(
                        location=[report.get("latitude", 0), report.get("longitude", 0)],
                        popup=f"Categories: {', '.join(report['categories'])}",
                        tooltip=f"{report['severity'].upper()} - {', '.join(report['categories'])}",
                        icon=folium.Icon(color=color, icon="info-sign")
                    ).add_to(m)
                
                # Display the map
                folium_static(m)
                
                # Display reports in a table
                st.markdown("### Report Details")
                
                for report in reports:
                    severity_class = "danger-area" if report["severity"] == "high" else "warning-area" if report["severity"] == "medium" else "safe-area"
                    
                    st.markdown(f"""
                    <div class='card'>
                        <h4 class='{severity_class}'>{report['severity'].upper()} - {', '.join(report['categories'])}</h4>
                        <p class='info-text'>Reported: {report['timestamp']} • Distance: {report.get('distance_km', 'N/A')} km</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No reports found in this area.")
    
    with tabs[2]:
        st.markdown("### Get Community Support")
        st.markdown("Connect with verified community volunteers who can provide guidance and support.")
        
        # Display reports that can be verified or get support for
        if st.session_state.reports:
            for i, report in enumerate(st.session_state.reports):
                st.markdown(f"""
                <div class='card'>
                    <h4>Report ID: {report['id']}</h4>
                    <p>{report['description'][:100]}...</p>
                    <p class='info-text'>Categories: {', '.join(report['categories'])} • Reported: {report['timestamp']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Verify Report", key=f"verify_{i}"):
                        with st.spinner("Verifying report..."):
                            response = handlers["incident_handler"].verify_report(report["id"])
                        
                        if "status" in response and response["status"] == "success":
                            st.success(response["message"])
                        else:
                            st.error("Verification failed. Please try again.")
                
                with col2:
                    if st.button("Get Support", key=f"support_{i}"):
                        with st.spinner("Finding support..."):
                            response = handlers["incident_handler"].get_community_support(report["id"])
                        
                        if "status" in response and response["status"] == "success":
                            volunteers = response["volunteers"]
                            
                            if volunteers:
                                st.markdown("### Available Volunteers")
                                
                                for volunteer in volunteers:
                                    st.markdown(f"""
                                    <div class='card'>
                                        <h4>{volunteer['name']}</h4>
                                        <p>Expertise: {', '.join(volunteer['expertise'])}</p>
                                        <p><a href="#">Contact this volunteer</a></p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No volunteers are currently available for this report category.")
                        else:
                            st.error("Failed to get support. Please try again.")
        else:
            st.info("You haven't submitted any reports yet.")
            
            st.markdown("""
            <div class='card'>
                <h4>Community Support</h4>
                <p>Our community volunteers are trained to provide guidance and support for various situations:</p>
                <ul>
                    <li>Harassment incidents</li>
                    <li>Stalking concerns</li>
                    <li>Physical threats</li>
                    <li>Unsafe environment reports</li>
                    <li>General safety concerns</li>
                </ul>
                <p>Submit a report to get connected with appropriate volunteers.</p>
            </div>
            """, unsafe_allow_html=True)

# Emergency Contacts page
elif page == "👥 Emergency Contacts":
    st.markdown("<h2 class='sub-header'>Emergency Contacts</h2>", unsafe_allow_html=True)
    
    # Get emergency contacts from database
    emergency_contacts = db.get_emergency_contacts(st.session_state.user_id)
    
    # Add new contact form
    st.markdown("### Add Emergency Contact")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        contact_name = st.text_input("Name", placeholder="Enter contact name")
    with col2:
        contact_phone = st.text_input("Phone Number", placeholder="Enter phone number with country code")
    with col3:
        contact_relationship = st.text_input("Relationship", placeholder="E.g., Family, Friend")
    
    if st.button("Add Contact", type="primary"):
        if not contact_name or not contact_phone:
            st.error("Please enter both name and phone number.")
        else:
            # Add contact to database
            db.add_emergency_contact(
                user_id=st.session_state.user_id,
                name=contact_name,
                phone=contact_phone,
                relationship=contact_relationship
            )
            st.success(f"Added {contact_name} as an emergency contact!")
            st.rerun()
    
    # Display existing contacts
    st.markdown("### Your Emergency Contacts")
    
    if emergency_contacts:
        for i, contact in enumerate(emergency_contacts):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class='contact-card'>
                    <h4>{contact['name']}</h4>
                    <p>Phone: {contact['phone']}</p>
                    <p class='info-text'>Relationship: {contact['relationship'] or 'Not specified'}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    # Delete contact from database
                    db.delete_emergency_contact(contact['id'], st.session_state.user_id)
                    st.success(f"Removed {contact['name']} from emergency contacts.")
                    st.rerun()
    else:
        st.info("You haven't added any emergency contacts yet.")
    
    # SOS test
    st.markdown("### Test SOS Alert")
    st.markdown("Send a test message to your emergency contacts to ensure the system works correctly.")
    
    if emergency_contacts:
        test_message = st.text_input("Test Message", value="This is a TEST emergency alert. Please ignore.")
        
        if st.button("Send Test Alert"):
            # Get current location
            location_data = get_current_location()
            
            # Send test notifications
            notification_results = sms_service.send_sos_notifications(
                user_name="User",  # In a real app, get the user's name
                location=st.session_state.user_location,
                message=f"TEST ONLY: {test_message}",
                emergency_contacts=emergency_contacts
            )
            
            st.success(f"Test alert sent to {len(notification_results)} emergency contacts!")
            
            # Show notification details
            st.markdown("### Notification Details")
            for result in notification_results:
                status_icon = "✅" if result["status"] in ["sent", "simulated"] else "❌"
                st.markdown(f"{status_icon} **{result['contact_name']}**: {result['contact_phone']}")
    else:
        st.warning("Please add emergency contacts before testing the SOS alert.")

# Settings page
elif page == "⚙️ Settings":
    st.markdown("<h2 class='sub-header'>Settings</h2>", unsafe_allow_html=True)
    
    # User profile settings
    st.markdown("### User Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_name = st.text_input("Your Name", placeholder="Enter your name")
    with col2:
        user_email = st.text_input("Your Email", placeholder="Enter your email")
    
    if st.button("Update Profile"):
        # Update user in database
        db.create_user(st.session_state.user_id, user_name, user_email)
        st.success("Profile updated successfully!")
    
    # Location settings
    st.markdown("### Location Settings")
    
    # Get current location button
    if st.button("Get Current Location", key="settings_get_location"):
        with st.spinner("Getting your location..."):
            location_data = get_current_location()
            if location_data:
                st.success(f"Location updated: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}")
                st.rerun()
    
    # Location search (simplified)
    location_search = st.text_input("Search location", 
                                  key="settings_location_search",
                                  help="Enter a location to search")
    
    col1, col2 = st.columns(2)
    
    with col1:
        location_lat = st.number_input("Default Latitude", value=st.session_state.user_location["latitude"], format="%.6f")
    with col2:
        location_lng = st.number_input("Default Longitude", value=st.session_state.user_location["longitude"], format="%.6f")
    
    if st.button("Update Default Location"):
        st.session_state.user_location = {"latitude": location_lat, "longitude": location_lng}
        st.success("Default location updated successfully!")
    
    # Show location on map
    location_map = get_map(location_lat, location_lng, zoom=15)
    folium.Marker(
        location=[location_lat, location_lng],
        popup="Your Default Location",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(location_map)
    folium_static(location_map)
    
    # Location tracking settings
    st.markdown("### Location Tracking Settings")
    
    auto_track = st.checkbox("Automatically start location tracking when opening the app", value=False)
    high_accuracy = st.checkbox("Use high accuracy mode (uses more battery)", value=True)
    track_interval = st.slider("Location update interval (seconds)", min_value=5, max_value=60, value=15, step=5)
    
    if st.button("Save Tracking Settings"):
        # In a real app, this would save to a database
        st.success("Location tracking settings saved successfully!")
    
    # Notification settings
    st.markdown("### Notification Settings")
    
    receive_alerts = st.checkbox("Receive safety alerts for my area", value=True)
    alert_radius = st.slider("Alert radius (km)", min_value=1.0, max_value=20.0, value=5.0, step=0.5)
    
    alert_types = st.multiselect(
        "Alert types to receive",
        ["security", "safety", "emergency", "suspicious_person", "unsafe_area"],
        ["security", "safety", "emergency"]
    )
    
    if st.button("Save Notification Settings"):
        # In a real app, this would save to a database
        st.success("Notification settings saved successfully!")
    
    # App settings
    st.markdown("### App Settings")
    
    # Dark mode toggle
    dark_mode = st.checkbox("Dark Mode", value=False)
    
    # Language selection
    language = st.selectbox("Language", ["English", "Hindi", "Bengali", "Spanish", "French"])
    
    if st.button("Save App Settings"):
        # In a real app, this would save to a database
        st.success("App settings saved successfully!")
    
    # Reset app
    st.markdown("### Reset Application")
    
    if st.button("Reset All Data", type="primary"):
        # Clear session state
        for key in list(st.session_state.keys()):
            if key != "user_id":
                del st.session_state[key]
        
        st.success("Application data reset successfully!")
        st.rerun()

