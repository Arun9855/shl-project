import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/recommend"

st.set_page_config(page_title="SHL Assessment Recommender", page_icon="🎯", layout="wide")

st.title("🎯 SHL Assessment Recommender")
st.markdown("Enter a natural language query or a Job Description to get the top tailored SHL assessments.")

query = st.text_area("Input your query or JD here:", height=150, placeholder="e.g. Need a Java developer who is good in collaborating with external teams and stakeholders.")

if st.button("Get Recommendations"):
    if not query.strip():
        st.warning("Please enter a query first.")
    else:
        with st.spinner("Analyzing requirements and matching assessments..."):
            try:
                response = requests.post(API_URL, json={"query": query})
                if response.status_code == 200:
                    data = response.json()
                    assessments = data.get("recommended_assessments", [])
                    
                    if not assessments:
                        st.info("No relevant assessments found.")
                    else:
                        st.success(f"Found {len(assessments)} Recommended Assessments!")
                        
                        for idx, test in enumerate(assessments, 1):
                            with st.expander(f"#{idx} - {test['name']} ({', '.join(test['test_type'])})", expanded=(idx<=3)):
                                st.markdown(f"**Description:** {test.get('description', 'N/A')}")
                                st.markdown(f"**Test Type:** {', '.join(test['test_type'])}")
                                st.markdown(f"**URL:** [link]({test['url']})")
                                cols = st.columns(3)
                                cols[0].metric("Duration (mins)", test.get('duration', 'N/A'))
                                cols[1].metric("Adaptive", test.get('adaptive_support', 'N/A'))
                                cols[2].metric("Remote", test.get('remote_support', 'N/A'))
                else:
                    st.error(f"API Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to API: {e}")
