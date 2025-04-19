# agents.py
import json
import re
from typing import Dict, List, Any, Optional

from prompts.prompt_templates import (
    DEMOGRAPHICS_PROMPT, INTERESTS_PROMPT, KEYWORDS_PROMPT,
    USAGE_BEHAVIOR_PROMPT, SATISFACTION_BEHAVIOR_PROMPT, PURCHASE_BEHAVIOR_PROMPT,
    PERSONALITY_PROMPT, LIFESTYLE_PROMPT, VALUES_PROMPT
)
from utils.llm import call_llm
from utils.parsing import extract_json, format_output
from utils.progress import progress
from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData


class BaseAgent:
    """Base class for all agents with common functionality"""
    def __init__(self, name: str, prompt_template: Optional[str], vector_db: VectorDB, csv_data: CSVData):
        self.name = name
        self.prompt_template = prompt_template
        self.vector_db = vector_db
        self.csv_data = csv_data
        
    def get_relevant_data(self, question: str, audience: str) -> List[str]:
        """Get data relevant to the question from both sources"""
        # Get vector DB results
        vector_results = self.vector_db.search(audience, limit=50)
        
        # Get CSV results
        csv_results = self.csv_data.search(audience)
        
        # Combine and deduplicate results
        combined_results = list(set(vector_results + csv_results))
        
        return combined_results[:100]  # Limit to 100 most relevant results


class SupervisorAgent(BaseAgent):
    """Routes questions to appropriate agents and adapts to unstructured inputs"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("supervisor", None, vector_db, csv_data)
        
        # Initialize all analysis agents
        self.agents = {
            "demographics": DemographicsAgent(vector_db, csv_data),
            "interests": InterestsAgent(vector_db, csv_data),
            "keywords": KeywordsAgent(vector_db, csv_data),
            "usage": UsageBehaviorAgent(vector_db, csv_data),
            "satisfaction": SatisfactionBehaviorAgent(vector_db, csv_data),
            "purchase": PurchaseBehaviorAgent(vector_db, csv_data),
            "personality": PersonalityAgent(vector_db, csv_data),
            "lifestyle": LifestyleAgent(vector_db, csv_data),
            "values": ValuesAgent(vector_db, csv_data)
        }
        
        # Initialize recommendation agent
        self.recommendation_agent = RecommendationAgent(vector_db, csv_data)
        
    def process_question(self, user_input: str) -> Dict[str, Any]:
        """Process any user input and determine how to respond"""
        # Start progress tracking
        progress.start()
        
        # Track progress
        progress.update_status("supervisor", None, "Analyzing user request")
        
        # 1. Extract the core question and audience
        question_info = self.extract_question_info(user_input)
        
        if not question_info["audience"]:
            # No audience detected - ask for clarification
            progress.stop()
            return {
                "status": "clarification_needed",
                "message": "I need to know what product or audience you're interested in learning about. Could you please clarify?"
            }
        
        # 2. Determine the analysis type
        agent_type = self.determine_analysis_type(question_info["question"])
        
        # 3. Process with the appropriate agent
        progress.update_status("supervisor", None, f"Routing to {agent_type} agent")
        agent = self.agents[agent_type]
        
        # Run analysis
        progress.update_status(agent_type, None, "Running analysis")
        analysis_result = agent.analyze(question_info["question"], question_info["audience"])
        
        # Enhance with recommendations
        progress.update_status("recommendation", None, "Adding recommendations")
        final_result = self.recommendation_agent.enhance(analysis_result, agent_type)
        
        progress.update_status("supervisor", None, "Complete")
        progress.stop()
        
        return final_result
    
    def extract_question_info(self, user_input: str) -> Dict[str, Any]:
        """Extract the core question and audience from any user input"""
        extraction_prompt = """
        From the following user input, extract:
        1. The main question or information request
        2. The product, audience, or subject they're asking about
        
        User input: "{user_input}"
        
        Respond in JSON format:
        {{
            "question": "The core question/request",
            "audience": "The product or audience being asked about (or null if unclear)"
        }}
        """
        
        formatted_prompt = extraction_prompt.format(user_input=user_input)
        response = call_llm(formatted_prompt)
        
        try:
            info = json.loads(response)
            if not info.get("audience"):
                # Try fallback extraction if LLM didn't find an audience
                info["audience"] = self.extract_audience_fallback(user_input)
            return info
        except:
            # Fallback extraction using regex patterns if LLM parsing fails
            audience = self.extract_audience_fallback(user_input)
            return {
                "question": user_input,
                "audience": audience
            }
    
    def extract_audience_fallback(self, text: str) -> Optional[str]:
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
    
    def determine_analysis_type(self, question: str) -> str:
        """Determine what type of analysis the user is requesting"""
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
        
        # Map to valid agent type
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
        
        return agent_mapping.get(category, "demographics")  # Default to demographics


class DemographicsAgent(BaseAgent):
    """Analyzes user demographics"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("demographics", DEMOGRAPHICS_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        """Run demographic analysis"""
        # Get relevant data
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        # Format prompt
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        # Call LLM
        progress.update_status(self.name, audience, "Analyzing demographics")
        response = call_llm(formatted_prompt, relevant_data)
        
        # Parse and format response
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "demographics",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class InterestsAgent(BaseAgent):
    """Analyzes user interests and preferences"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("interests", INTERESTS_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        """Run interests analysis"""
        # Get relevant data
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        # Format prompt
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        # Call LLM
        progress.update_status(self.name, audience, "Analyzing interests")
        response = call_llm(formatted_prompt, relevant_data)
        
        # Parse and format response
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "interests",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class KeywordsAgent(BaseAgent):
    """Analyzes keywords and phrases"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("keywords", KEYWORDS_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        # Implementation similar to other agents
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        progress.update_status(self.name, audience, "Analyzing keywords")
        response = call_llm(formatted_prompt, relevant_data)
        
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "keywords",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class UsageBehaviorAgent(BaseAgent):
    """Analyzes usage behavior patterns"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("usage", USAGE_BEHAVIOR_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        # Implementation similar to other agents
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        progress.update_status(self.name, audience, "Analyzing usage behaviors")
        response = call_llm(formatted_prompt, relevant_data)
        
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "usage",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class SatisfactionBehaviorAgent(BaseAgent):
    """Analyzes customer satisfaction"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("satisfaction", SATISFACTION_BEHAVIOR_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        # Implementation similar to other agents
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        progress.update_status(self.name, audience, "Analyzing satisfaction")
        response = call_llm(formatted_prompt, relevant_data)
        
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "satisfaction",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class PurchaseBehaviorAgent(BaseAgent):
    """Analyzes purchase behavior patterns"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("purchase", PURCHASE_BEHAVIOR_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        # Implementation similar to other agents
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        progress.update_status(self.name, audience, "Analyzing purchase patterns")
        response = call_llm(formatted_prompt, relevant_data)
        
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "purchase",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class PersonalityAgent(BaseAgent):
    """Analyzes personality traits"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("personality", PERSONALITY_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        # Implementation similar to other agents
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        progress.update_status(self.name, audience, "Analyzing personality traits")
        response = call_llm(formatted_prompt, relevant_data)
        
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "personality",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class LifestyleAgent(BaseAgent):
    """Analyzes lifestyle patterns"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("lifestyle", LIFESTYLE_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        # Implementation similar to other agents
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        progress.update_status(self.name, audience, "Analyzing lifestyle patterns")
        response = call_llm(formatted_prompt, relevant_data)
        
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "lifestyle",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class ValuesAgent(BaseAgent):
    """Analyzes core values and priorities"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("values", VALUES_PROMPT, vector_db, csv_data)
    
    def analyze(self, question: str, audience: str) -> Dict[str, Any]:
        # Implementation similar to other agents
        progress.update_status(self.name, audience, "Retrieving data")
        relevant_data = self.get_relevant_data(question, audience)
        
        formatted_prompt = self.prompt_template.format(audience=audience)
        
        progress.update_status(self.name, audience, "Analyzing core values")
        response = call_llm(formatted_prompt, relevant_data)
        
        progress.update_status(self.name, audience, "Formatting results")
        structured_data = extract_json(response)
        formatted_output = format_output(response)
        
        return {
            "agent_type": "values",
            "question": question,
            "audience": audience,
            "structured_data": structured_data,
            "formatted_output": formatted_output,
            "raw_response": response
        }


class RecommendationAgent(BaseAgent):
    """Enhances analysis results with targeted recommendations"""
    def __init__(self, vector_db: VectorDB, csv_data: CSVData):
        super().__init__("recommendation", None, vector_db, csv_data)
        
    def enhance(self, analysis_result: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """Add recommendations to the analysis result"""
        # Get the structured data
        data = analysis_result["structured_data"]
        audience = analysis_result["audience"]
        
        # Create the introduction based on agent type
        introduction = self.create_introduction(agent_type)
        
        # Generate recommendations based on agent type and data
        recommendations = self.generate_recommendations(data, agent_type, audience)
        
        # Add recommendations to the result
        enhanced_result = analysis_result.copy()
        enhanced_result["recommendations"] = {
            "introduction": introduction,
            "recommendations": recommendations
        }
        
        # Update the formatted output to include recommendations
        enhanced_result["formatted_output"] = self.update_output_format(
            analysis_result["formatted_output"], 
            introduction,
            recommendations
        )
        
        return enhanced_result
    
    def create_introduction(self, agent_type: str) -> str:
        """Create a contextually appropriate introduction based on agent type"""
        introductions = {
            "demographics": "I just got info from the demographic agent which means I will develop a recommendation that is based on these insights, concrete and actionable recommendations that can be used.",
            
            "interests": "I just got info from the interests agent which means I will develop a recommendation that is based on these insights, concrete and actionable recommendations that can be used.",
            
            "keywords": "I just got info from the keywords agent which means I will develop a recommendation that is based on these feature insights, concrete and actionable recommendations that can be used.",
            
            "usage": "I just got info from the usage behavior agent which means I will develop a recommendation that is based on these usage pattern insights, concrete and actionable recommendations that can be used.",
            
            "satisfaction": "I just got info from the satisfaction agent which means I will develop a recommendation that is based on these customer satisfaction insights, concrete and actionable recommendations that can be used.",
            
            "purchase": "I just got info from the purchase behavior agent which means I will develop a recommendation that is based on these purchasing pattern insights, concrete and actionable recommendations that can be used.",
            
            "personality": "I just got info from the personality agent which means I will develop a recommendation that is based on these personality trait insights, concrete and actionable recommendations that can be used.",
            
            "lifestyle": "I just got info from the lifestyle agent which means I will develop a recommendation that is based on these lifestyle pattern insights, concrete and actionable recommendations that can be used.",
            
            "values": "I just got info from the values agent which means I will develop a recommendation that is based on these core values insights, concrete and actionable recommendations that can be used."
        }
        
        return introductions.get(agent_type, "Based on these insights, I'll provide concrete and actionable recommendations that can be used.")
    
    def generate_recommendations(self, data: Dict[str, Any], agent_type: str, audience: str) -> List[str]:
        """Generate specific recommendations based on agent type and data"""
        # Create a prompt to generate targeted recommendations
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
    
    def update_output_format(self, original_output: str, introduction: str, recommendations: List[str]) -> str:
        """Add the recommendations to the formatted output"""
        # Add a recommendations section to the original output
        recommendation_section = "\n\n📋 **Recommendations**:\n"
        recommendation_section += introduction + "\n\n"
        
        for rec in recommendations:
            recommendation_section += rec + "\n"
        
        return original_output + recommendation_section