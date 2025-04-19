# main.py
import argparse
import sys
from typing import Dict, Any

from agents.agents import SupervisorAgent
from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData
from utils.progress import progress
import config


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Audience Segmentation System")
    
    parser.add_argument("--csv-path", type=str, default=config.DEFAULT_CSV_PATH,
                      help="Path to the CSV file")
    
    parser.add_argument("--vector-db-path", type=str, default=config.DEFAULT_VECTOR_DB_PATH,
                      help="Path to the vector database")
    
    return parser.parse_args()


def process_question(question: str, supervisor: SupervisorAgent) -> Dict[str, Any]:
    """Process a single question with the supervisor agent"""
    return supervisor.process_question(question)


def main():
    """Main entry point for the segmentation system"""
    args = parse_args()
    
    # Initialize data sources
    try:
        csv_data = CSVData(args.csv_path)
        vector_db = VectorDB(args.vector_db_path)
    except Exception as e:
        print(f"Error initializing data sources: {e}")
        sys.exit(1)
    
    # Initialize supervisor agent
    supervisor = SupervisorAgent(vector_db, csv_data)
    
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
            result = process_question(question, supervisor)
            
            if result.get("status") == "clarification_needed":
                # Need more information from user
                print(f"\n{result['message']}")
            else:
                # Output the formatted result
                print(f"\n{result['formatted_output']}")
        except Exception as e:
            print(f"Error processing question: {e}")


if __name__ == "__main__":
    main()