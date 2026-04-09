import streamlit as st
import pandas as pd
from agent import run_agent

def analyze_flood_risk(location, lat, lon):
    return run_agent(location, lat, lon)


st.set_page_config(page_title="Flash Flood Street Ranker", page_icon="🌊", layout="wide")

st.title("🌊 Flash Flood Street Ranker")
st.markdown("An AI Agent predicting which informal settlement streets to evacuate first based on live weather data and street topology.")

with st.sidebar:
    st.header("Target Location")
    with st.form("location_form"):
        location = st.text_input("Name", value="Chavakkad")
        lat = st.number_input("Latitude", value=10.53, format="%.4f")
        lon = st.number_input("Longitude", value=76.02, format="%.4f")
        submit_button = st.form_submit_button("Run Flood Analysis")

if submit_button:
    with st.spinner("Agent compiling data and analyzing... (or retrieving from cache instantly)"):
        result = analyze_flood_risk(location, lat, lon)
        
    if result.get("errors"):
        for err in result["errors"]:
            st.error(err)
            
    col1, col2 = st.columns(2)
    with col1:
        st.info("🌦️ Current Weather Data")
        weather = result.get("weather", {})
        st.metric("Current Precipitation", f"{weather.get('current_precipitation_mm', 0)} mm")
        st.metric("Expected 24h Precipitation", f"{weather.get('next_24h_precipitation_mm', 0)} mm")
        
    with col2:
        st.info("🗺️ Analyzed Roads")
        roads = result.get("roads", [])
        st.write(f"Analyzed {len(roads)} streets in the vicinity using Overpass API.")
        st.write(", ".join(roads[:10]) + ("..." if len(roads) > 10 else ""))
        
    st.subheader(f"🚨 Evacuation Priority Ranking for {location.title()}")
    rankings = result.get("rankings", [])
    
    if rankings:
        df = pd.DataFrame(rankings)
        # Apply strict styling
        st.dataframe(
            df,
            column_config={
                "street_name": "Street Name",
                "vulnerability_score": st.column_config.ProgressColumn(
                    "Vulnerability Score",
                    help="Risk of flooding (out of 100)",
                    format="%f",
                    min_value=0,
                    max_value=100,
                ),
                "reason": "AI Reason"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No rankings could be generated.")
