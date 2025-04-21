# workflow/manager.py
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from utils.progress import progress
from utils.llm import call_llm
import json
import re

class WorkflowManager:
    """Manages the audience analysis workflow"""
    
    def __init__(self, agent_registry: Dict[str, Any], vector_db, csv_data):
        """Initialize with agent registry and data sources"""
        self.agent_registry = agent_registry
        self.vector_db = vector_db
        self.csv_data = csv_data
        self.workflow = self._create_workflow()
    
    def _extract_query_info(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the question and audience from the input"""
        question = state.get("question", "")
        
        # Use LLM to extract audience
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
                info["audience"] = self._extract_audience_fallback(question)
                
            # Update the state
            new_state = state.copy()
            new_state["question"] = info.get("question", question)
            new_state["audience"] = info.get("audience")
            
            return new_state
        except:
            # Fallback extraction using regex patterns
            audience = self._extract_audience_fallback(question)
            
            # Update the state
            new_state = state.copy()
            new_state["audience"] = audience
            
            return new_state
    
    def _extract_audience_fallback(self, text: str) -> Optional[str]:
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
    
    def _fetch_relevant_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data relevant to the question and audience"""
        question = state.get("question", "")
        audience = state.get("audience", "")
        
        # If no audience was extracted, return the state as is
        if not audience:
            new_state = state.copy()
            new_state["data"] = []
            return new_state
        
        # Get data from the vector database
        vector_results = self.vector_db.search(audience, limit=50)
        
        # Get data from the CSV database
        csv_results = self.csv_data.search(audience)
        
        # Combine results and remove duplicates
        combined_results = list(set(vector_results + csv_results))
        
        # Update the state
        new_state = state.copy()
        new_state["data"] = combined_results[:100]  # Limit to top 100 results
        
        return new_state
    
    def _determine_agent_type(self, state: Dict[str, Any]) -> str:
        """Route to the appropriate agent based on the question"""
        question = state.get("question", "")
        
        # Use LLM to classify the question
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
    
    def _generate_recommendations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on analysis results"""
        analysis_results = state.get("analysis_results", {})
        
        if not analysis_results:
            return state
        
        agent_type = analysis_results.get("agent_type", "")
        audience = analysis_results.get("audience", "")
        structured_data = analysis_results.get("structured_data", {})
        
        # Create introduction based on agent type
        introduction = self._create_introduction(agent_type)
        
        # Generate recommendations
        recommendations = self._generate_specific_recommendations(structured_data, agent_type, audience)
        
        # Add recommendations to the result
        new_analysis_results = analysis_results.copy()
        new_analysis_results["recommendations"] = {
            "introduction": introduction,
            "recommendations": recommendations
        }
        
        # Update the formatted output
        formatted_output = analysis_results.get("formatted_output", "")
        new_formatted_output = self._update_output_format(
            formatted_output,
            introduction,
            recommendations
        )
        new_analysis_results["formatted_output"] = new_formatted_output
        
        # Update the state
        new_state = state.copy()
        new_state["analysis_results"] = new_analysis_results
        
        return new_state
    
    def _create_introduction(self, agent_type: str) -> str:
        """Create a contextually appropriate introduction based on agent type"""
        introductions = {
            "demographics": "Based on demographic insights, here are targeted recommendations:",
            "interests": "Based on user interest analysis, consider these actionable recommendations:",
            "keywords": "Based on key feature insights, here are actionable recommendations:",
            "usage": "Based on usage pattern analysis, consider implementing these recommendations:",
            "satisfaction": "To improve customer satisfaction, consider these targeted recommendations:",
            "purchase": "To optimize purchase behavior, consider these strategic recommendations:",
            "personality": "Based on personality trait analysis, consider these tailored recommendations:",
            "lifestyle": "To better align with user lifestyles, consider these recommendations:",
            "values": "To better connect with user values, consider these recommendations:"
        }
        
        return introductions.get(agent_type, "Based on these insights, consider these recommendations:")
    
    def _generate_specific_recommendations(self, data: Dict[str, Any], agent_type: str, audience: str) -> List[str]:
        """Generate specific recommendations based on agent type and data"""
        # Create a prompt to generate recommendations
        recommendation_prompt = f"""
        Based on the following {agent_type} insights about {audience}, 
        provide 3-5 concrete, actionable recommendations.
        
        Each recommendation should:
        1. Be specific and practical
        2. Directly relate to the insights provided
        3. Be implementable without significant resources
        4. Include a brief explanation of expected outcomes
        
        Insights:
        {json.dumps(data, indent=2)}
        
        Format each recommendation as a bullet point starting with "•" followed by the recommendation.
        """
        
        recommendations_response = call_llm(recommendation_prompt)
        
        # Extract bullet points from the response
        bullet_points = []
        for line in recommendations_response.split("\n"):
            line = line.strip()
            if line.startswith("•") or line.startswith("-"):
                bullet_points.append(line)
        
        return bullet_points if bullet_points else ["• " + recommendations_response.strip()]
    
    def _update_output_format(self, original_output: str, introduction: str, recommendations: List[str]) -> str:
        """Add the recommendations to the formatted output"""
        # Add a recommendations section to the original output
        recommendation_section = "\n\n📋 **Recommendations**:\n"
        recommendation_section += introduction + "\n\n"
        
        for rec in recommendations:
            recommendation_section += rec + "\n"
        
        return original_output + recommendation_section
    
    def _format_final_output(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Format the final output for display"""
        analysis_results = state.get("analysis_results", {})
        
        if not analysis_results:
            new_state = state.copy()
            new_state["formatted_output"] = "Sorry, I couldn't analyze your question. Please try again with a clearer question about a specific audience."
            return new_state
        
        # The formatted output has already been updated in generate_recommendations
        formatted_output = analysis_results.get("formatted_output", "")
        
        # Update the state
        new_state = state.copy()
        new_state["formatted_output"] = formatted_output
        
        return new_state
    
    def _create_workflow(self):
        """Create the audience analysis workflow with LangGraph"""
        # Define the state class
        class AnalysisState(TypedDict):
            question: str
            audience: str
            data: List[str]
            analysis_results: Dict[str, Any]
            formatted_output: str
        
        # Create the workflow graph
        workflow = StateGraph(AnalysisState)
        
        # Add nodes for each step
        workflow.add_node("extract_query", self._extract_query_info)
        workflow.add_node("fetch_data", self._fetch_relevant_data)
        
        # Add analysis agent nodes
        for agent_key, agent_func in self.agent_registry.items():
            workflow.add_node(agent_key, agent_func)
        
        # Add recommendation node
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        
        # Add formatter node
        workflow.add_node("format_output", self._format_final_output)
        
        # Define the edges - sequential flow with conditional branching
        workflow.add_edge("extract_query", "fetch_data")
        workflow.add_edge("fetch_data", self._determine_agent_type)
        
        # Connect analysis agents
        for agent_key in self.agent_registry.keys():
            workflow.add_edge(self._determine_agent_type, agent_key)
            workflow.add_edge(agent_key, "generate_recommendations")
        
        workflow.add_edge("generate_recommendations", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile()
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """Process a question using the workflow"""
        # Start progress tracking
        progress.start()
        
        try:
            # Initialize the state
            initial_state = {
                "question": question,
                "audience": None,
                "data": [],
                "analysis_results": {},
                "formatted_output": ""
            }
            
            # Invoke the workflow
            result = self.workflow.invoke(initial_state)
            
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
