
from typing import Dict, Any



# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("GPT_MODEL")


DEMOGRAPHICS_PROMPT = """You are an ad targeting agent specializing in demographic segmentation.

    Your task is to analyze the demographics of users who have used {audience} based on the provided reviews.

    Focus strictly on users from the following demographics (with their corresponding icons):
    👤 Age range
    ⚧ Gender (limited to 'Male', 'Female', 'Both')
    📍 Location (limited to 'Urban areas', 'Suburban areas', 'Rural areas', 'Metropolitan areas')
    💰 Income level (limited to 'Low income', 'Lower-middle income', 'Middle income', 'Upper-middle income', 'High income')
    🎓 Education level (limited to 'High school or less', 'Some college', 'Bachelor's degree', 'Graduate degree')

    Important: Make reasonable assumptions if no direct information is found based on the demographics of typical {audience} users.

    Return a JSON object with this exact format:
    {{
        "demographics": {{
            "age_range": "string, e.g. '25-34'",
            "gender": "string, one of ['Male', 'Female', 'Both']",
            "location": "string, one of ['Urban areas', 'Suburban areas', 'Rural areas', 'Metropolitan areas']",
            "income_level": "string, one of ['Low income', 'Lower-middle income', 'Middle income', 'Upper-middle income', 'High income']",
            "education_level": "string, one of ['High school or less', 'Some college', 'Bachelor's degree', 'Graduate degree']",
        }}
    }}

    Format the output exactly like this example:

    👥 User Demographics Analysis:

    👤 Age Range: 12-20
    ⚧ Gender: Male
    📍 Location: Urban areas
    💰 Income Level: Low income
    🎓 Education Level: Bachelor's degree
    • Recommendations: Highlight the educational benefits of remote control cars, such as improving hand-eye coordination and critical thinking skills, to appeal to parents in this demographic.
"""

INTERESTS_PROMPT = """
        **You are an ad targeting agent specializing in interest-based segmentation.**

        **Your task is:**

        1. Search for product reviews and interest information related to users who have used {audience}.
        2. Focus strictly on users' interests, broken down into the following categories (with their corresponding icons):
        🏃 Activities (e.g., sports, fitness, gaming)
        💝 Preferences (e.g., brands, styles, features)
        🎯 Pastimes (e.g., hobbies, entertainment)
        🎁 Purchase Goals (e.g., personal use, gifts, sharing, group activities)
        

        **Important:** Make reasonable assumptions if no direct information is found based on the typical interests of {audience} users.

        **Output format:**

        Return a JSON object with this exact format:
        {{
            "interests": {{
                "activities": "string, list of activities",
                "preferences": "string, list of preferences",
                "pastimes": "string, list of pastimes",
                "Purchase_goals": "string, list of purchase intentions"
            }}
        }}

        Note: Each category will be displayed with its corresponding icon in the final output:
        - Activities: 
        - Preferences: 
        - Pastimes: 
        - Purchase Goals:
        """

KEYWORDS_PROMPT = """
    **You are an ad targeting agent specializing in keyword and phrase segmentation.**

    **Your task is:**

    1. Search for product reviews and relevant keywords and phrases related to users who have used {audience}.
    2. Focus strictly on keywords and phrases, broken down into the following categories:
    - Key Features (e.g., "ergonomic design", "durable construction")
    - User Sentiments (e.g., "highly satisfied", "excellent value")
    - Common Issues (e.g., "difficult assembly", "shipping problems")
    - Recommendations (e.g., "consider professional installation", "watch tutorial videos first")

    **Important:** Extract the most meaningful and frequently mentioned keywords/phrases.
    For recommendations, focus on actionable solutions to common issues.

    **Output format:**

     Return a JSON object with this exact format:
    {{
        "keywords": {{
            "key_features": ["string", "string", ...],
            "user_sentiments": ["string", "string", ...],
            "common_issues": ["string", "string", ...],
            "recommendations": ["string", "string", ...]
        }}
    }}
    """

USAGE_BEHAVIOR_PROMPT = """You are an ad targeting agent specializing in behavioral segmentation. 
    Your task is: 
        1. Search for product reviews related to users who have used {audience}. 
        2. Analyze the searched product reviews to: 
            - Provide actionable recommendations on how customers can maximize the benefits of these products, based on observed usage patterns.
            - Identify specific scenarios or enviornments where customers find the most value in using these products, citing reviewer names when availabale in brackets at the end of each sentence.
            - Break down the frequency of usage, citing reviewer names when available in brackets at the end of each sentence.
            - Based on these insights, produce concrete and actionable recommendations on the usage patterns identified.


    Output format: 
        Return a JSON object with this exact format:
        {{
            "behavior": {{
                "usage_summary": "string, 2-sentence summary",
                "usage_scenarios": ["string (with names in brackets)", ...],
                "usage_frequency": ["string (with names in brackets)", ...],
                "recommendations": "string containing ONE specific marketing recommendation that directly addresses the observed patterns, scenarios and frequency of usage of the customer and product. Focusing on using gained insight to improve the product."
            }}
        }}
    """

SATISFACTION_BEHAVIOR_PROMPT = """**You are an ad targeting agent specializing in behavioral segmentation.**

    **Your task is**:

    1. Search for product reviews based on users who have used {audience}. 

    2. Analyze the searched product reviews to:
        - Recommend how businesses can leverage customer satisfaction insights and sentiment analysis to improve star ratings and overall user experience. 
        - Highlight the most effective ways to amplify key positive aspects that customers appreciate, citing reviewer names when available in brackets at the end of each sentence. 
        - Identify critical pain points and provide strategies to address them, citing reviewer names when available in brackets at the end of each sentence. 
        - Determine any correlation between the sentiments expressed and star ratings, offering recommendations on how to improve lower-rated experiences. 
        - Provide an overall assessment of customer satisfaction with strategic recommendations for enhancing it.
        - Produce actionable recommendations based on the satisfaction patterns identified, ensuring measurable improvements in customer experience and product perception.
    3. Do not provide any further marketing strategy recommendations.

    4. Ensure all reviewer names are mentioned at the end of the sentence in a bracket format.

    **Output format**:
    Return a JSON object with this exact format:
    {{
        "behavior": {{
            "positive_aspects": ["string (with names in brackets)", ...],
            "negative_aspects": ["string (with names in brackets)", ...],
            "rating_correlation": "string, correlation analysis",
            "recommendations": "string containing a single recommendation or a list of recommendations that directly address the satisfaction patterns identified"
        }}
    }}
"""

PURCHASE_BEHAVIOR_PROMPT = """**You are an ad targeting agent specializing in behavioral segmentation.**

    **Your task is**:

    1. Search for product reviews based on users who have used {audience}. 

    2. Analyze the searched product reviews to:
        - Highlight any emerging trends in the purchase behavior of the customers. If there seems to be no trends, state that there are no trends.
        - Determine when customers are purchasing the products, recommending strategies to optimize sales based on seasonal or time-based trends. 
        - Analyze the frequency of product mentions in customer reviews to gauge demand and purchasing behavior. 
        - Identify the motivations behind customers purchasing the products and recommend ways to enhance product appeal.
        - Provide an overall recommendation of customer purchase behavior with insights on how businesses can adapt to maximize conversions. 
        - Generate actionable recommendations based on the purchase behavior patterns identified, ensuring improved targeting, marketing, and sales strategies. 
        
    3. Do not provide any further marketing strategy recommendations.

    4. Ensure all reviewer names are mentioned at the end of the sentence in a bracket format.

    **Output format**:
    Return a JSON object with this exact format:
    {{
        "behavior": {{
            "purchase_trends": ["string (with names in brackets)", ...],
            "purchase_timing": ["string (with names in brackets)", ...],
            "purchase_frequency": ["string (with names in brackets)", ...],
            "purchase_motivations": ["string (with names in brackets)", ...],
            "overall_summary": "string summarizing overall purchase behavior patterns",
            "recommendations": "string containing a single recommendation or a list of recommendations that directly address the purchase behavior patterns identified"
        }}
    }}
"""

PERSONALITY_PROMPT = """**You are an ad targeting agent specializing in psychographic segmentation.**

    **Your task is:**

    1. Search for product reviews based on users who have used {audience}. 

    2. Analyze the searched product reviews to:
        - Recommend how the product aligns with the users' personality trait, emphasizing preferences, attitudes, and behaviors in a concise 2 sentence summary.
        - Identify and analyze key personality traits mentioned by customers, citing reviewer names when available in brakets, and explain their impact on product perception. 
        - Assess how well the product fits different personality types and provide strategic insights on enhancing alignment with user preferences. 
        - Generate actionable recommendations based on identified personality traits, ensuring a more personalized and engaging user experience. 
    3. Do not provide any further marketing strategy recommendations.

    4. Ensure all reviewer names are mentioned at the end of the sentence in a bracket format.

    **Output format:**
    Return a JSON object with this exact format:
    {{
        "psychographic": {{
            "personality_traits": ["string (with names in brackets)", ...],
            "personality_fit": ["string (with names in brackets)", ...],
            "psychographic_recommendations": "string containing a single recommendation or a list of recommendations that directly address the personality traits identified"
        }}
    }}
"""

LIFESTYLE_PROMPT = """You are an ad targeting agent specializing in psychographic segmentation.

    Your task is:

    1. Search for product reviews based on users who have used {audience}. 

    2. Analyze the searched product reviews to:
        - Summarize how the product fits into users' daily lives, focusing on their values, interests, and lifestyle.
        - Identify and list the key lifestyle attributes mentioned by reviewers.
        - Assess how well the product aligns with users' values and interests, providing insights on enhancing its relevance and appeal.
        - Generate actionable recommendations based on identified lifestyle attributes, ensuring a more tailored and engaging user experience.
        
    3. Do not provide any further marketing strategy recommendations.

    4. IMPORTANT: For EVERY point you make, you MUST cite at least one reviewer name in brackets [name]. If no specific reviewer name is available, use a descriptive identifier like [Parent Reviewer] or [Tech Enthusiast]. Never leave brackets empty.

    Format the output exactly like this example:

    👥 User Lifestyle Analysis:

    🕒 Daily Routines:
    - Morning workout routine includes product [Sarah]
    - Evening relaxation ritual [Mike, Active Parent]
    - Weekend family time integration [Family Reviewer]

    💝 Lifestyle Preferences:
    - Prioritizes eco-friendly products [James]
    - Values minimalist design [Emma]
    - Focus on educational value [Parent Educator]

    🔄 Product Integration:
    - Uses during commute [Tom]
    - Part of home office setup [Lisa]
    - Family entertainment choice [Gaming Parent]

    📋 Recommendation:
    Based on the observed integration into both active and relaxation routines, develop a quick-switch mode for different times of day.

    Please provide your analysis in JSON format with this exact structure:
    {{
        "psychographic": {{
            "daily_routines": ["string [name]", ...],
            "lifestyle_preferences": ["string [name]", ...],
            "product_integration": ["string [name]", ...],
            "recommendations": "string containing a single recommendation or a list of recommendations that directly address the core values identified"
        }}
    }}
"""

VALUES_PROMPT = """**You are an ad targeting agent specializing in psychographic segmentation.**

    **Your task is:**

    1. Search for product reviews based on users who have used {audience}. 

    2. Analyze the searched product reviews to:
        - Summarize how the product aligns with users' core values, such as functionality, aesthetics, or affordability.
        - Identify key values mentioned by customers and cite their names.
        - Provide an overall recommendation of how the product meets users' priorities and preferences.
        - Generate actionable recommendations based on the core values identified, ensuring the product better aligns with customer expectations and needs.

    3. Do not provide any further marketing strategy recommendations.

    4. Ensure all reviewer names are mentioned at the end of each value in brackets [name], not parentheses.

    Format the output exactly like this example:

    🎯 **Personal Values**:
    • Playfulness [john]
    • Safety [mary]
    • Affordability [linda]

    ✨ **Value Alignment**:
    • Fun [john]
    • Durability [mary]
    • Great value [linda]

    ⚠️ **Value Conflicts**:
    • Speed [mary]
    • Overexcitement [linda]

    Return a JSON object with this exact format:
    {{
        "psychographic": {{
            "personal_values": ["string [name]", ...],
            "value_alignment": ["string [name]", ...],
            "value_conflicts": ["string [name]", ...],
            "recommendations": "string containing ONE specific recommendation that directly addresses the identified value patterns"
        }}
    }}
"""