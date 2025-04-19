# agents/agent_factory.py
from typing import Dict, Any, Callable
from prompts.prompt_templates import PromptManager
from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData
from utils.llm import call_llm
from utils.parsing import extract_json, format_output
from utils.progress import progress

# Create the prompt manager
prompt_manager = PromptManager()

def create_analysis_agent(
    agent_type: str,
    vector_db: VectorDB,
    csv_data: CSVData
) -> Callable:
    """Factory function to create an analysis agent"""
    
    def agent_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """The agent function that will be called in the workflow"""
        # Extract data from state
        question = state["question"]
        audience = state["audience"]
        relevant_data = state.get("data", [])
        
        # Update progress
        progress.update_status(agent_type, audience, f"Analyzing {agent_type}")
        
        # Format the prompt
        prompt = prompt_manager.get_prompt(agent_type, audience, relevant_data)
        
        # Call LLM
        progress.update_status(agent_type, audience, f"Processing with LLM")
        response = call_llm(prompt, relevant_data)
        
        # Parse and format
        progress.update_status(agent_type, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        # Update state
        new_state = state.copy()
        new_state["analysis_results"] = {
            "agent_type": agent_type,
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }
        
        return new_state
    
    return agent_func
