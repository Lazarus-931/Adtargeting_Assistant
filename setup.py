# setup.py
import os
import argparse
import pandas as pd
from tqdm import tqdm
from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData

def main():
    """Set up CSV and vector database for the segmentation system"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Setup CSV and vector database")
    parser.add_argument("--csv-path", type=str, required=True, help="Path to the CSV file")
    parser.add_argument("--vector-db-path", type=str, required=True, help="Path to the vector database directory")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild the vector database even if it exists")
    
    args = parser.parse_args()
    
    # 1. Initialize CSV connector
    print(f"Initializing CSV data from {args.csv_path}")
    csv_data = CSVData(args.csv_path)
    
    if csv_data.data.empty:
        print("Error: CSV data is empty or could not be loaded")
        return
    
    print(f"Successfully loaded CSV with {len(csv_data.data)} rows")
    
    # 2. Check if vector database exists and if we should rebuild it
    vector_db_exists = os.path.exists(os.path.join(args.vector_db_path, "faiss_index.bin")) and \
                      os.path.exists(os.path.join(args.vector_db_path, "data.pkl"))
    
    if vector_db_exists and not args.force_rebuild:
        print(f"Vector database already exists at {args.vector_db_path}")
        print("To rebuild, use the --force-rebuild flag")
        print("Setup complete!")
        return
    
    # 3. Initialize vector database
    print(f"{'Rebuilding' if vector_db_exists else 'Initializing'} vector database at {args.vector_db_path}")
    vector_db = VectorDB(args.vector_db_path)
    
    # 4. Get text data from CSV for embedding
    string_cols = csv_data.data.select_dtypes(include=['object']).columns.tolist()
    print(f"Found {len(string_cols)} text columns: {', '.join(string_cols)}")
    
    # 5. Prepare text data for embedding
    texts = []
    
    # Format each row as a review-like text
    print("Preparing text data for embedding...")
    for _, row in tqdm(csv_data.data.iterrows(), total=len(csv_data.data)):
        text = csv_data.format_row_as_review(row)
        if text:
            texts.append(text)
    
    print(f"Prepared {len(texts)} text entries for embedding")
    
    # 6. Add texts to vector database in batches
    batch_size = args.batch_size
    num_batches = (len(texts) + batch_size - 1) // batch_size
    
    print(f"Processing {len(texts)} texts in {num_batches} batches of size {batch_size}")
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        progress_pct = (i//batch_size + 1) / num_batches * 100
        print(f"Processing batch {i//batch_size + 1}/{num_batches} ({progress_pct:.1f}%)")
        vector_db.add_texts(batch)
    
    print("Setup complete!")
    print(f"CSV data loaded from: {args.csv_path}")
    print(f"Vector database created at: {args.vector_db_path}")
    print(f"You can now run the main system with:")
    print(f"python main.py --csv-path {args.csv_path} --vector-db-path {args.vector_db_path}")

if __name__ == "__main__":
    main()