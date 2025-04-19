# data/csv_connector.py
import pandas as pd
from typing import List, Dict, Any, Optional

class CSVData:
    """Interface for CSV data source"""
    def __init__(self, file_path: str):
        """Initialize CSV data source"""
        self.file_path = file_path
        
        try:
            # Load the CSV file
            self.data = pd.read_csv("data.csv")
            print(f"Loaded CSV file with {len(self.data)} rows and {len(self.data.columns)} columns")
            
            # Log the first few column names to verify correct loading
            print(f"Columns: {', '.join(self.data.columns[:5])}...")
            
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            # Initialize with empty DataFrame
            self.data = pd.DataFrame()
    
    def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """Search the CSV data for relevant entries"""
        if self.data.empty:
            return []
        
        # Simple text search in all string columns
        results = []
        
        # Get all string columns
        string_cols = self.data.select_dtypes(include=['object']).columns.tolist()
        
        if not string_cols:
            return []
        
        # Search each string column for the query
        for col in string_cols:
            try:
                # Find rows where the column contains the query
                matches = self.data[self.data[col].str.contains(query, case=False, na=False)]
                
                # Add matching rows to results
                for _, row in matches.iterrows():
                    # Format the row as a string that resembles a review
                    result = self.format_row_as_review(row)
                    results.append(result)
            except Exception as e:
                print(f"Error searching column {col}: {e}")
        
        # Remove duplicates and limit results
        return list(set(results))[:100]
    
    def format_row_as_review(self, row: pd.Series) -> str:
        """Format a dataframe row as a review-like text"""
        # Customize this method based on your CSV structure
        review_parts = []
        
        # Try to extract reviewer name if available
        reviewer = None
        for name_field in ['reviewer', 'name', 'user', 'author']:
            if name_field in row and not pd.isna(row[name_field]):
                reviewer = row[name_field]
                break
        
        # Try to extract review text if available
        review_text = None
        for text_field in ['review', 'comment', 'feedback', 'text', 'description']:
            if text_field in row and not pd.isna(row[text_field]):
                review_text = row[text_field]
                break
        
        # Format the review
        if reviewer:
            review_parts.append(f"Reviewer: {reviewer}")
        
        if review_text:
            review_parts.append(f"Review: {review_text}")
        
        # Add other relevant fields
        for field, value in row.items():
            if not pd.isna(value) and field not in ['reviewer', 'name', 'user', 'author', 'review', 'comment', 'feedback', 'text', 'description']:
                review_parts.append(f"{field.replace('_', ' ').title()}: {value}")
        
        return " | ".join(review_parts)

