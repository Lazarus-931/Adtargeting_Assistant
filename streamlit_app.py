import streamlit as st
from agents.agents import SupervisorAgent
from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData
import config
import os
import json

# Initialize data sources and agent (cache to avoid reloading on every rerun)
@st.cache_resource
def get_supervisor():
    # Check if paths exist and use defaults if not specified
    csv_path = os.getenv("CSV_PATH", config.DEFAULT_CSV_PATH)
    vector_db_path = os.getenv("VECTOR_DB_PATH", config.DEFAULT_VECTOR_DB_PATH)
    
    # Check if paths exist
    if not os.path.exists(csv_path):
        st.error(f"CSV file not found at {csv_path}. Please check your configuration.")
        st.stop()
    
    if not os.path.exists(vector_db_path):
        st.error(f"Vector database not found at {vector_db_path}. Please run setup.py first.")
        st.stop()
    
    try:
        csv_data = CSVData(csv_path)
        vector_db = VectorDB(vector_db_path)
        return SupervisorAgent(vector_db, csv_data)
    except Exception as e:
        st.error(f"Error initializing data sources: {e}")
        st.stop()

# App title and description
st.set_page_config(
    page_title="AdTargeting Assistant", 
    page_icon="🎯", 
    layout="wide"
)

st.title("🎯 AdTargeting Assistant")
st.markdown("""
This tool analyzes audiences and products to provide targeted insights and recommendations.
Simply enter a question about a specific audience or product to get started.
""")

# Sidebar with examples
with st.sidebar:
    st.header("Example Questions")
    st.markdown("""
    Try asking questions like:
    - What are the demographics of smartphone users?
    - What are the interests of fitness enthusiasts?
    - What keywords are associated with organic food?
    - How do people use streaming services?
    - What is the satisfaction level of electric car owners?
    - What are the purchase patterns for gaming consoles?
    - What personality traits do coffee drinkers have?
    - What lifestyle do luxury brand customers have?
    - What values do sustainable product buyers have?
    """)
    
    st.header("Settings")
    show_data = st.checkbox("Show structured data (JSON)", value=False)
    show_raw = st.checkbox("Show raw response", value=False, help="Display the unformatted LLM response for debugging")

# User input
question = st.text_input("Enter your question about a product or audience:", placeholder="e.g., What are the demographics of smartphone users?")

# Load the supervisor
supervisor = get_supervisor()

# Process question when submitted
if question:
    with st.spinner("Analyzing..."):
        result = supervisor.process_question(question)
    
    if result.get("status") == "clarification_needed":
        st.warning(result["message"])
    else:
        # Display the audience that was detected
        audience = result.get("audience", "")
        agent_type = result.get("agent_type", "")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.info(f"**Audience**: {audience}")
        with col2:
            st.info(f"**Analysis Type**: {agent_type}")
        
        # Display the formatted output
        st.markdown("## Analysis Results")
        
        # Split formatted output at the recommendations section if it exists
        formatted_output = result.get("formatted_output", "")
        
        if "📋 **Recommendations**:" in formatted_output:
            analysis, recommendations = formatted_output.split("📋 **Recommendations**:", 1)
            
            # Display analysis section
            st.markdown(analysis)
            
            # Display recommendations in a styled box
            st.markdown("## 📋 Recommendations")
            with st.container(border=True):
                for line in recommendations.strip().split('\n'):
                    if line.strip():
                        if line.strip().startswith('•') or line.strip().startswith('-'):
                            st.markdown(line)
                        else:
                            st.markdown(f"**{line}**")
        else:
            # If no recommendations section found, display the entire output
            st.markdown(formatted_output)
        
        # Show structured data if requested
        if show_data:
            st.markdown("## Structured Data")
            st.json(result.get("structured_data", {}))
        
        # Show raw response if requested
        if show_raw:
            st.markdown("## Raw Response")
            st.text_area("", result.get("raw_response", ""), height=300)