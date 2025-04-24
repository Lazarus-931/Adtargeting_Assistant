# data/vector_db_connector.py
import os
import torch
import numpy as np
import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import pickle
import faiss

class VectorDB:
    """Interface for the Vector Database using PyTorch and FAISS"""
    def __init__(self, db_path: str):
        """Initialize connection to vector database"""
        self.db_path = db_path
        
        # Load the embedding model
        try:
            print(f"Loading embedding model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print(f"Embedding model loaded successfully")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            raise
        
        # Check if the vector database already exists
        self.index_path = os.path.join(db_path, "faiss_index.bin")
        self.data_path = os.path.join(db_path, "data.pkl")
        
        if os.path.exists(self.index_path) and os.path.exists(self.data_path):
            # Load existing database
            print(f"Loading existing vector database from {db_path}")
            self.load_database()
        else:
            # Create new database
            print(f"Creating new vector database at {db_path}")
            self.initialize_database()
    
    def initialize_database(self):
        """Initialize a new empty database"""
        # Create empty data store
        self.texts = []
        
        # Create empty FAISS index
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Load embeddings from data.pt if it exists
        data_pt_path = os.path.join(self.db_path, "data.pt")
        if os.path.exists(data_pt_path):
            embeddings = torch.load(data_pt_path)
            embeddings_np = embeddings.numpy().astype('float32')
            self.index.add(embeddings_np)
            print(f"Loaded embeddings from data.pt into FAISS index")
        
        # Load texts from texts.json if it exists
        texts_path = os.path.join(self.db_path, "texts.json")
        if os.path.exists(texts_path):
            with open(texts_path, "r") as f:
                self.texts = json.load(f)
            print(f"Loaded {len(self.texts)} texts from texts.json")
        
        # Save the empty database
        self.save_database()
        
        print(f"Initialized empty vector database with dimension {self.dimension}")
    
    def load_database(self):
        """Load the database from disk"""
        try:
            # Load the FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load the associated data
            with open(self.data_path, 'rb') as f:
                self.texts = pickle.load(f)
            
            print(f"Loaded vector database with {len(self.texts)} entries")
            
            # Get dimension from the index
            self.dimension = self.index.d
            
        except Exception as e:
            print(f"Error loading vector database: {e}")
            # Fall back to creating a new database
            self.initialize_database()
    
    def save_database(self):
        """Save the database to disk"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.db_path, exist_ok=True)
            
            # Save the FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save the associated data
            with open(self.data_path, 'wb') as f:
                pickle.dump(self.texts, f)
            
            print(f"Saved vector database with {len(self.texts)} entries")
            
        except Exception as e:
            print(f"Error saving vector database: {e}")
    
    def add_texts(self, texts: List[str]):
        """Add new texts to the database"""
        if not texts:
            return
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=True)
            
            # Convert to numpy array with correct dtype
            embeddings_np = np.array(embeddings).astype('float32')
            
            # Add to FAISS index
            self.index.add(embeddings_np)
            
            # Store the original texts
            self.texts.extend(texts)
            
            # Save the updated database
            self.save_database()
            
            print(f"Added {len(texts)} new texts to the database")
            
        except Exception as e:
            print(f"Error adding texts to vector database: {e}")
    
    def search(self, query: str, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """Search the vector database for relevant entries"""
        if not self.texts:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Reshape for FAISS
            query_embedding = np.array([query_embedding]).astype('float32')
            
            # Search the index
            distances, indices = self.index.search(query_embedding, min(limit, len(self.texts)))
            
            # Get the corresponding texts
            results = [self.texts[idx] for idx in indices[0] if idx < len(self.texts)]
            
            return results
            
        except Exception as e:
            print(f"Error searching vector database: {e}")
            return []
    
    def embed_text(self, text: str) -> List[float]:
        """Convert text to embedding vector"""
        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.dimension