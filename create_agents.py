from aixplain.factories import ModelFactory
from aixplain.factories import AgentFactory, TeamAgentFactory
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_women_safety_agents():
    """
    Create the three AI agents for women's safety and combine them into a team agent
    using only ModelTools and LLMs
    
    Returns:
        Dict containing all created agents
    """
    # Get API key and model ID from environment variables
    api_key = os.getenv("AIXPLAIN_API_KEY")
    llm_model_id = os.getenv("AIXPLAIN_LLM_MODEL_ID")
    
    if not api_key:
        raise ValueError("AIXPLAIN_API_KEY environment variable is not set")
    if not llm_model_id:
        raise ValueError("AIXPLAIN_LLM_MODEL_ID environment variable is not set")
    
    # Set API key for aixplain
    os.environ["AIXPLAIN_API_KEY"] = api_key
    
    print("Creating AI agents for women's safety...")
    
    # Create the main LLM tool that will be used by all agents
    # main_llm_tool = ModelFactory.get(llm_model_id)
    
    # 1. Create the Anonymous Incident Reporting Agent
    incident_reporting_agent = AgentFactory.create(
        name="Anonymous Incident Reporting Agent",
        description="""
        A platform where individuals can anonymously report safety concerns, crimes, or distress situations.
        This agent can:
        1. Anonymize reports by removing personally identifiable information
        2. Categorize reports by severity and type
        3. Assess if immediate action is required
        4. Recommend appropriate community support
        """,
        # tools=[main_llm_tool],
        llm_id=llm_model_id
    )
    
    # 2. Create the Personalized Safety Navigator Agent
    safety_navigator_agent = AgentFactory.create(
        name="Personalized Safety Navigator",
        description="""
        AI-driven personal safety assistant that guides users in avoiding high-risk areas.
        This agent can:
        1. Analyze routes for safety concerns
        2. Provide real-time risk assessment
        3. Generate safety recommendations
        4. Monitor user location and alert about potential dangers
        5. Suggest safer alternative routes
        """,
        # tools=[main_llm_tool],
        llm_id=llm_model_id
    )
    
    # 3. Create the Emergency Alert System Agent
    emergency_alert_agent = AgentFactory.create(
        name="Emergency Alert System",
        description="""
        A real-time system that sends emergency alerts to individuals, communities, and authorities.
        This agent can:
        1. Process emergency alerts and determine severity
        2. Identify which authorities should be notified
        3. Generate appropriate alert messages
        4. Prioritize alerts based on urgency
        5. Verify alerts to prevent false alarms
        """,
        # tools=[main_llm_tool],
        llm_id=llm_model_id
    )
    
    # Create a Team Agent that combines all three agents
    women_safety_team = TeamAgentFactory.create(
        name="Women Safety AI Team",
        description="A comprehensive AI team for women's safety, combining incident reporting, safety navigation, and emergency alerts.",
        agents=[
            incident_reporting_agent,
            safety_navigator_agent,
            emergency_alert_agent
        ],
        llm_id=llm_model_id
    )
    
    print("AI agents created successfully!")
    
    return {
        "incident_reporting_agent": incident_reporting_agent,
        "safety_navigator_agent": safety_navigator_agent,
        "emergency_alert_agent": emergency_alert_agent,
        "women_safety_team": women_safety_team
    }

if __name__ == "__main__":
    # Create the agents
    agents = create_women_safety_agents()
    
    # Print agent information
    for name, agent in agents.items():
        print(f"\n{name}:")
        print(f"  ID: {agent.id}")
        print(f"  Name: {agent.name}")
        print(f"  Description: {agent.description}")