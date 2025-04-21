from typing import Dict, Any, Callable, List, Optional
from utils.llm import call_llm
from utils.parsing import extract_json, format_output
from utils.progress import progress

class AgentBuilder:
    """Builder pattern for creating audience analysis agents"""
    
    def __init__(self, name: str):
        """Initialize with agent name"""
        self.name = name
        self.prompt_template = None
        self.vector_db = None
        self.csv_data = None
        self.pre_process_func = None
        self.post_process_func = None
        
    def with_prompt(self, prompt_template: str) -> 'AgentBuilder':
        """Set the prompt template"""
        self.prompt_template = prompt_template
        return self
    
    def with_data_sources(self, vector_db, csv_data) -> 'AgentBuilder':
        """Set the data sources"""
        self.vector_db = vector_db
        self.csv_data = csv_data
        return self
    
    def with_pre_processor(self, func: Callable) -> 'AgentBuilder':
        """Add a pre-processing function"""
        self.pre_process_func = func
        return self
    
    def with_post_processor(self, func: Callable) -> 'AgentBuilder':
        """Add a post-processing function"""
        self.post_process_func = func
        return self
    
    def build(self) -> Callable:
        """Build and return the agent function"""
        
        def get_relevant_data(question: str, audience: str) -> List[str]:
            """Get data relevant to the question from both sources"""
            if not self.vector_db or not self.csv_data:
                return []
                
            # Get vector DB results
            vector_results = self.vector_db.search(audience, limit=50)
            
            # Get CSV results
            csv_results = self.csv_data.search(audience)
            
            # Combine and deduplicate results
            combined_results = list(set(vector_results + csv_results))
            
            return combined_results[:100]  # Limit to 100 most relevant results
        
        def agent_func(state: Dict[str, Any]) -> Dict[str, Any]:
            """The agent function that will process the state"""
            # Extract data from state
            question = state.get("question", "")
            audience = state.get("audience", "")
            
            # Pre-processing if defined
            if self.pre_process_func:
                state = self.pre_process_func(state)
                # Update in case pre-processor changed these
                question = state.get("question", "")
                audience = state.get("audience", "")
            
            # Get relevant data
            progress.update_status(self.name, audience, "Retrieving data")
            relevant_data = get_relevant_data(question, audience)
            
            # Format prompt
            if not self.prompt_template:
                raise ValueError(f"Agent {self.name} has no prompt template defined")
                
            formatted_prompt = self.prompt_template.format(audience=audience)
            
            # Call LLM
            progress.update_status(self.name, audience, f"Running {self.name} analysis")
            response = call_llm(formatted_prompt, relevant_data)
            
            # Parse and format response
            progress.update_status(self.name, audience, "Formatting results")
            structured_data = extract_json(response)
            formatted_output = format_output(response)
            
            # Create analysis results
            analysis_results = {
                "agent_type": self.name,
                "question": question,
                "audience": audience,
                "structured_data": structured_data,
                "formatted_output": formatted_output,
                "raw_response": response
            }
            
            # Update state with analysis results
            new_state = state.copy()
            new_state["analysis_results"] = analysis_results
            
            # Post-processing if defined
            if self.post_process_func:
                new_state = self.post_process_func(new_state)
            
            return new_state
        
        return agent_func

def create_agent_registry(prompt_templates: Dict[str, str], vector_db, csv_data) -> Dict[str, Callable]:
    """Create a registry of all analysis agents"""
    registry = {}
    
    for agent_type, prompt_template in prompt_templates.items():
        agent = (AgentBuilder(agent_type)
                .with_prompt(prompt_template)
                .with_data_sources(vector_db, csv_data)
                .build())
        
        registry[agent_type] = agent
    
    return registry
