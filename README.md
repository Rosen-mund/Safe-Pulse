# Women Safety AI System

## Overview
This project is an AI-driven system designed to enhance women's safety by providing:
- **Anonymous Incident Reporting**: Users can report safety concerns anonymously.
- **Personalized Safety Navigator**: Real-time safety recommendations based on location.
- **Emergency Alert System**: Alerts authorities and trusted contacts in emergencies.
- **Live Location Tracking**: Users can share real-time locations with trusted contacts.

The system leverages AI agents created on the Aixplain platform, uses Twilio for SMS notifications, and provides a web interface built with Streamlit.

## Features
✅ Anonymous reporting of safety incidents  
✅ AI-driven safety navigation  
✅ Emergency alerts to authorities and contacts  
✅ Location-based safety recommendations  
✅ Secure storage and management of user reports and alerts  

## Project Structure
``` bash
.
├── database.py           # Manages SQLite database interactions
├── create_agents.py      # Creates AI agents for the safety system
├── agent_handlers.py     # Handles interactions between AI agents and the database
├── sms_service.py        # Handles SMS alerts using Twilio API
├── Safe_pulse.py         # Streamlit-based web interface for the system
├── .env                  # Environment variables for API keys (not included)
└── README.md             # Documentation file
```

## Installation & Setup
### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Required libraries (`sqlite3`, `aixplain`, `twilio`, `streamlit`, `folium`, `dotenv`)

### Steps to Run
1. **Clone the repository**  
   ```sh
   git clone https://github.com/your-repo/women-safety-ai.git
   cd women-safety-ai
   ```
2. **Set up a virtual environment**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up environment variables in a ```.env``` file:**
   ```sh
   AIXPLAIN_API_KEY=your_api_key
   AIXPLAIN_LLM_MODEL_ID=your_model_id
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   ```
5. **Run the AI agent creation script**
   ```sh
   python create_agents.py
   ```
6. **Start the web interface**
  ```sh
  streamlit run Safe_pulse.py
  ```
## Usage
- **Anonymous Reporting**: Users can submit reports that will be analyzed and stored anonymously.
- **Safety Navigation**: The AI provides real-time guidance for safe travel.
- **Emergency Alerts**: The system alerts authorities and emergency contacts in distress situations.
- **Live Tracking**: Users can share their live location with trusted contacts.

## Technologies Used
- **Python**: Core backend logic
- **SQLite**: Database for storing reports and alerts
- **Aixplain**: AI agent deployment
- **Twilio**: SMS notifications for emergency alerts
- **Streamlit**: Web interface for user interaction
- **Folium**: Map-based safety visualization

