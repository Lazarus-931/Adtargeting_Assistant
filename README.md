# Running the AdTargeting Assistant Streamlit App

## Prerequisites
Make sure you have all dependencies installed:
```bash
pip install -r requirements.txt
```

Additionally, ensure you have the following packages installed for Streamlit:
```bash
pip install streamlit
```

## Setup Instructions

1. First, run the setup.py script to ensure your vector database is initialized:
```bash
python setup.py --csv-path data/data.csv --vector-db-path data/vector_db
```

2. Launch the Streamlit app with your data paths:
```bash
streamlit run streamlit_app.py
```

3. Alternatively, you can set environment variables before running:
```bash
export CSV_PATH=data/data.csv
export VECTOR_DB_PATH=data/vector_db
streamlit run streamlit_app.py
```

## Additional Options

### Running on a specific port
```bash
streamlit run streamlit_app.py --server.port 8501
```

### Running with server address
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0
```

### Creating a Streamlit Launch Script

You can create a simple bash script to make launching easier:

```bash
#!/bin/bash
# launch_app.sh

# Set environment variables for data paths
export CSV_PATH=data/data.csv
export VECTOR_DB_PATH=data/vector_db

# Run the Streamlit app
streamlit run streamlit_app.py
```

Make it executable:
```bash
chmod +x launch_app.sh
```

Then run it:
```bash
./launch_app.sh
```