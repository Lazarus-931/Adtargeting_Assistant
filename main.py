# main.py
import argparse
import sys
from typing import Dict, Any

from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData
from utils.progress import progress
from prompts.prompt_templates import PromptManager
from agents.improved_agent_factory import create_agent_registry
from workflow.manager import WorkflowManager
import config


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Audience Segmentation System")
    
    parser.add_argument("--csv-path", type=str, default=config.DEFAULT_CSV_PATH,
                      help="Path to the CSV file")
    
    parser.add_argument("--vector-db-path", type=str, default=config.DEFAULT_VECTOR_DB_PATH,
                      help="Path to the vector database")
    
    parser.add_argument("--model", type=str, default="gemma3:27b-it-qat",
                      help="LLM model to use")
    
    return parser.parse_args()


def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize data sources
    try:
        print("Initializing data sources...")
        csv_data = CSVData(args.csv_path)
        vector_db = VectorDB(args.vector_db_path)
    except Exception as e:
        print(f"Error initializing data sources: {e}")
        sys.exit(1)
    
    # Initialize prompt manager
    prompt_manager = PromptManager()
    
    # Create agent registry
    print("Initializing analysis agents...")
    agent_registry = create_agent_registry(prompt_manager.templates, vector_db, csv_data)
    
    # Create workflow manager
    print("Creating workflow...")
    workflow_manager = WorkflowManager(agent_registry, vector_db, csv_data)
    
    # Interactive mode
    print("\n=== Audience Segmentation System ===")
    print("Type 'exit' or 'quit' to exit")
    
    while True:
        # Get user question
        question = input("\nEnter your question: ")
        
        if question.lower() in ["exit", "quit"]:
            break
        
        # Process the question
        try:
            print("\nProcessing your question...")
            result = workflow_manager.process_question(question)
            print(f"\n{result['formatted_output']}")
        except Exception as e:
            print(f"Error processing question: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
