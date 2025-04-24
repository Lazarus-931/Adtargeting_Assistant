import streamlit as st
from agents.agents import SupervisorAgent
from data.vector_db_connector import VectorDB
from data.csv_connector import CSVData
import config

# Initialize data sources and agent (cache to avoid reloading on every rerun)
@st.cache_resource
def get_supervisor():
    csv_data = CSVData(config.DEFAULT_CSV_PATH)
    vector_db = VectorDB(config.DEFAULT_VECTOR_DB_PATH)
    return SupervisorAgent(vector_db, csv_data)

supervisor = get_supervisor()

st.title("AdTargeting Assistant")

question = st.text_input("Enter your question about a product or audience:")

if question:
    with st.spinner("Analyzing..."):
        result = supervisor.process_question(question)
    if result.get("status") == "clarification_needed":
        st.warning(result["message"])
    else:
        st.subheader("Analysis & Recommendations")
        # Show the formatted output up to the recommendations section
        formatted_output = result["formatted_output"]
        if "📋 **Recommendations**:" in formatted_output:
            main_output, rec_section = formatted_output.split("📋 **Recommendations**:", 1)
            st.markdown(main_output)
            st.markdown("**Recommendations:**")
            # Split recommendations by line and show as bullet points
            for line in rec_section.splitlines():
                line = line.strip()
                if line.startswith("•") or line.startswith("-"):
                    st.markdown(f"- {line[1:].strip()}")
        else:
            st.markdown(formatted_output)
       # st.subheader("Structured Data")
        #st.json(result["structured_data"])