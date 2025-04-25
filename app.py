# app.py
import os
import sys
import argparse
from typing import Dict, Any, List, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData
from agents.agent_factory import create_analysis_agent
from utils.progress import progress
from utils.llm import call_llm
from utils.parsing import extract_json, format_output
import config
import re
import json

# Define the analysis agent types
ANALYSIS_AGENT_TYPES = [
    "demographics",
    "interests",
    "keywords",
    "usage",
    "satisfaction", 
    "purchase",
    "personality",
    "lifestyle",
    "values"
]

# Analysis agents dictionary
ANALYSIS_AGENTS = {}

def extract_query_info(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the question and audience from the input"""
    question = state.get("question", "")
    
    # Use a simple LLM call to extract audience
    extraction_prompt = """
    From the following user question, extract:
    1. The main question or information request
    2. The product, audience, or subject they're asking about
    
    User question: "{question}"
    
    Respond in JSON format:
    {{
        "question": "The core question/request",
        "audience": "The product or audience being asked about (or null if unclear)"
    }}
    """
    
    formatted_prompt = extraction_prompt.format(question=question)
    response = call_llm(formatted_prompt)
    
    try:
        # Parse the JSON response
        info = json.loads(response)
        
        # If no audience found, try fallback extraction
        if not info.get("audience"):
            info["audience"] = extract_audience_fallback(question)
            
        # Update the state
        new_state = state.copy()
        new_state["question"] = info.get("question", question)
        new_state["audience"] = info.get("audience")
        
        return new_state
    except:
        # Fallback extraction using regex patterns
        audience = extract_audience_fallback(question)
        
        # Update the state
        new_state = state.copy()
        new_state["audience"] = audience
        
        return new_state

def extract_audience_fallback(text: str) -> str:
    """Fallback method to extract audience/product using pattern matching"""
    # Try various patterns to catch different phrasings
    patterns = [
        r"(?:about|for|of|who (?:use|buy|purchase)|regarding) ([^?.,]+)",
        r"([^?.,]+) (?:users|customers|buyers|audience)",
        r"people (?:who|that) (?:use|buy|like) ([^?.,]+)"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Clean up the matched audience
            audience = matches[0].strip()
            # Remove common filler words
            audience = re.sub(r'\b(the|my|your|their|our)\b', '', audience, flags=re.IGNORECASE).strip()
            if audience:
                return audience
    
    return None

def fetch_relevant_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch data relevant to the question and audience"""
    question = state.get("question", "")
    audience = state.get("audience", "")
    
    # If no audience was extracted, return the state as is
    if not audience:
        new_state = state.copy()
        new_state["data"] = []
        return new_state
    
    # Get data from the vector database
    vector_results = state.get("vector_db").search(audience, limit=50)
    
    # Get data from the CSV database
    csv_results = state.get("csv_data").search(audience)
    
    # Combine results and remove duplicates
    combined_results = list(set(vector_results + csv_results))
    
    # Update the state
    new_state = state.copy()
    new_state["data"] = combined_results[:100]  # Limit to top 100 results
    
    return new_state

def conditional_router(state: Dict[str, Any]) -> str:
    """Route to the appropriate agent based on the question"""
    question = state.get("question", "")
    
    # Create a prompt to classify the question
    classification_prompt = """
    Classify the following question into exactly one of these categories:
    - demographics (questions about age, gender, location, income, education)
    - interests (questions about preferences, activities, pastimes)
    - keywords (questions about key phrases, features, aspects mentioned)
    - usage (questions about how customers use products, usage patterns)
    - satisfaction (questions about customer satisfaction, sentiment)
    - purchase (questions about buying patterns, purchase timing)
    - personality (questions about personality traits)
    - lifestyle (questions about lifestyle patterns)
    - values (questions about values, priorities)
    
    Question: "{question}"
    
    Respond with just one word - the category name.
    """
    
    formatted_prompt = classification_prompt.format(question=question)
    category = call_llm(formatted_prompt).strip().lower()
    
    # Map to valid agent type with fallback to demographics
    agent_mapping = {
        "demographics": "demographics",
        "interests": "interests",
        "keywords": "keywords",
        "usage": "usage",
        "satisfaction": "satisfaction",
        "purchase": "purchase",
        "personality": "personality",
        "lifestyle": "lifestyle",
        "values": "values"
    }
    
    # Return the agent key or default to demographics
    return agent_mapping.get(category, "demographics")

def format_output(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format the final output for display"""
    analysis_results = state.get("analysis_results", {})
    
    if not analysis_results:
        new_state = state.copy()
        new_state["formatted_output"] = "Sorry, I couldn't analyze your question. Please try again with a clearer question about a specific audience."
        return new_state
    
    # Get the formatted output from the analysis agent directly
    formatted_output = analysis_results.get("formatted_output", "")
    
    # Update the state
    new_state = state.copy()
    new_state["formatted_output"] = formatted_output
    
    return new_state

def create_agent_graph():
    """Create the audience analysis workflow with LangGraph"""
    # Define state for the workflow
    class AnalysisState(TypedDict):
        question: str
        audience: str
        data: List[str]
        vector_db: VectorDB
        csv_data: CSVData
        analysis_results: Dict[str, Any]
        messages: List[BaseMessage]
        formatted_output: str
    
    # Create the workflow graph
    workflow = StateGraph(AnalysisState)
    
    # Add nodes for each step
    workflow.add_node("extract_query", extract_query_info)
    workflow.add_node("fetch_data", fetch_relevant_data)
    
    # Add analysis agent nodes
    for agent_key, agent_func in ANALYSIS_AGENTS.items():
        workflow.add_node(agent_key, agent_func)
    
    # Add formatter node
    workflow.add_node("format_output", format_output)
    
    # Define the edges - sequential flow with conditional branching
    workflow.add_edge("extract_query", "fetch_data")
    workflow.add_edge("fetch_data", conditional_router)
    
    # Connect analysis agents directly to output formatter
    for agent_key in ANALYSIS_AGENTS.keys():
        workflow.add_edge(conditional_router, agent_key)
        workflow.add_edge(agent_key, "format_output")
    
    workflow.add_edge("format_output", END)
    
    return workflow.compile()

def initialize_agents(vector_db: VectorDB, csv_data: CSVData):
    """Initialize all analysis agents"""
    global ANALYSIS_AGENTS
    ANALYSIS_AGENTS = {}
    for agent_type in ANALYSIS_AGENT_TYPES:
        ANALYSIS_AGENTS[agent_type] = create_analysis_agent(agent_type, vector_db, csv_data)

def create_workflow(vector_db: VectorDB, csv_data: CSVData):
    """Create the analysis workflow"""
    # Initialize agents
    initialize_agents(vector_db, csv_data)
    
    # Create and return the workflow
    return create_agent_graph()

def process_question(question: str, workflow, vector_db: VectorDB, csv_data: CSVData) -> Dict[str, Any]:
    """Process a question using the workflow"""
    # Start progress tracking
    progress.start()
    
    try:
        # Initialize the state
        initial_state = {
            "question": question,
            "audience": None,
            "data": [],
            "vector_db": vector_db,
            "csv_data": csv_data,
            "analysis_results": {},
            "messages": [],
            "formatted_output": ""
        }
        
        # Invoke the workflow
        result = workflow.invoke(initial_state)
        
        # Create a simplified result
        simplified_result = {
            "formatted_output": result.get("formatted_output", ""),
            "audience": result.get("audience"),
            "agent_type": result.get("analysis_results", {}).get("agent_type"),
        }
        
        return simplified_result
    
    finally:
        # Stop progress tracking
        progress.stop()

def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize data sources
    try:
        csv_data = CSVData(args.csv_path)
        vector_db = VectorDB(args.vector_db_path)
    except Exception as e:
        print(f"Error initializing data sources: {e}")
        sys.exit(1)
    
    # Create the workflow
    workflow = create_workflow(vector_db, csv_data)
    
    # Interactive mode
    print("Audience Segmentation System")
    print("Type 'exit' or 'quit' to exit")
    
    while True:
        # Get user question
        question = input("\nEnter your question: ")
        
        if question.lower() in ["exit", "quit"]:
            break
        
        # Process the question
        try:
            result = process_question(question, workflow, vector_db, csv_data)
            print(f"\n{result['formatted_output']}")
        except Exception as e:
            print(f"Error processing question: {e}")
            import traceback
            traceback.print_exc()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Audience Segmentation System")
    
    parser.add_argument("--csv-path", type=str, default=config.DEFAULT_CSV_PATH,
                      help="Path to the CSV file")
    
    parser.add_argument("--vector-db-path", type=str, default=config.DEFAULT_VECTOR_DB_PATH,
                      help="Path to the vector database")
    
    return parser.parse_args()

if __name__ == "__main__":
    main()