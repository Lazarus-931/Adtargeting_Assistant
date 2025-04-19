from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage, trim_messages
from langchain_core.tools import tool, ToolException, InjectedToolArg
from langchain_core.runnables import RunnableConfig
from langchain_community.utilities import ArxivAPIWrapper
from langchain_community.tools import ArxivQueryRun, HumanInputRun
from langgraph.graph import StateGraph,START,END, add_messages, MessagesState
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from typing import Annotated, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import wikipedia
import uuid
import operator
from IPython.display import Image, display
import os
from langchain_openai import ChatOpenAI
from pandas import DataFrame

import pandas as pd
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm
import math



class DemographicAnalysisResult(BaseModel):
    age_range: str
    gender: str
    location: str
    income_level: str
    education_level: str
    
def analyze_age(reviews: pd.DataFrame) -> str:
    """
    Analyze the age range of reviewers using OpenAI o4-mini LLM.
    Returns a string with emoji, e.g., '👤 Age range: 18 to 65'
    """
    # Convert a sample of the DataFrame to string for LLM context
    sample = reviews.head(10).to_string()
    prompt = (
        "Given the following product review data, estimate the most likely age range of the reviewers. "
        "Respond in the format: '👤 Age range: <range>'.\n"
        f"Data sample:\n{sample}"
    )
    # If you have a call_llm utility, use it; otherwise, use ChatOpenAI directly
    try:
        from utils.llm import call_llm
        response = call_llm(prompt, model="o4-mini")
    except ImportError:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="o4-mini")
        response = llm.invoke(prompt).content
    return response.strip()

def analyze_gender(reviews: pd.DataFrame) -> str:
    """
    Analyze the gender of reviewers based on review text or other patterns.
    Return just the gender, e.g., 'Male/Female/Both'
    """
    return "⚧ Gender: Male/Female/Both"

def analyze_location(reviews: pd.DataFrame) -> str:
    """
    Analyze the location of reviewers based on review text or other heuristics.
    Return just the location, e.g., 'Urban areas'
    """
    return "📍 Location: Urban areas"

def analyze_income(reviews: pd.DataFrame) -> str:
    """
    Analyze the income level of reviewers based on review text or other heuristics.
    Return just the income level, e.g., 'Middle income'
    """
    return "💰 Income level: Middle income"

def analyze_education(reviews: pd.DataFrame) -> str:
    """
    Analyze the education level of reviewers based on review text or other heuristics.
    Return just the education level, e.g., "Bachelor's degree"
    """
    return "🎓 Education level: Bachelor's degree"

def generate_demographic_output(state: dict) -> dict:
    """
    Analyzes data using demographic traits:
    1. Age range
    2. Gender
    3. Location
    4. Income level
    5. Education level
    Returns a dict with the analysis results.
    """
    data = state["data"]
    progress.update_status("demographic_agent", "Analyzing demographic traits...")
    age_range = analyze_age(data)

    progress.update_status("demographic_agent", "Analysing gender")
    gender = analyze_gender(data)

    progress.update_status("demographic_agent", "Analyzing location")
    location = analyze_location(data)

    progress.update_status("demographic_agent", "Analyzing income level")
    income_level = analyze_income(data)

    progress.update_status("demographic_agent", "Analyzing education level")
    education_level = analyze_education(data)

    analysis_results = DemographicAnalysisResult(
        age_range=age_range,
        gender=gender,
        location=location,
        income_level=income_level,
        education_level=education_level,
    )
    return analysis_results.dict()