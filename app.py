import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import json
import os

st.set_page_config(page_title="Crime Data Analysis Dashboard", layout="wide")
st.title("📊 Crime Data Analysis Dashboard")
st.markdown("This dashboard allows you to explore multiple crime datasets, inspect data, analyze trends, and visualize using graphs and maps dynamically based on the strict rules defined.")

# -------- LOAD GEOJSON --------
@st.cache_data
def load_geojson():
    geojson_path = "india_district.geojson"
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

geojson = load_geojson()

# -------- FILE DISCOVERY --------
csv_files = glob.glob("*.csv")
if not csv_files:
    st.warning("No CSV files found in the directory.")
    st.stop()

selected_file = st.sidebar.selectbox("Select File for Analysis", csv_files)

# -------- DATA PROCESSING (CLEANING) --------
@st.cache_data
def load_and_clean_data(file_name):
    df = pd.read_csv(file_name)
    
    # 1. Remove duplicates
    df = df.drop_duplicates()
    
    # Track column types
    num_cols = df.select_dtypes(include='number').columns
    cat_cols = df.select_dtypes(exclude='number').columns
    
    # 2. Handle missing values using existing data
    df[num_cols] = df[num_cols].fillna(0)
    df[cat_cols] = df[cat_cols].fillna("Unknown")
    
    # 3. Standardize formats (Title Case for regions to match GeoJSON properties natively)
    for col in ['state_name', 'district_name']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.title().str.strip()
            
    return df

if selected_file:
    df = load_and_clean_data(selected_file)
    
    st.header(f"Dataset: {selected_file}")
    
    # -------- STEP 1 & 2: PREVIEW & STATS --------
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Preview (Cleaned)")
        st.dataframe(df.head(10))
    with col2:
        st.subheader("Summary Statistics")
        st.write(df.describe())
        
    st.download_button(
        label="Download Cleaned Dataset",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"cleaned_{selected_file}",
        mime='text/csv',
    )
    
    # -------- COLUMN CATEGORIZATION --------
    exclude_metrics = ['id', 'year', 'state_code', 'district_code']
    num_cols = [c for c in df.select_dtypes(include='number').columns if c.lower() not in exclude_metrics]
    cat_cols = df.select_dtypes(exclude='number').columns.tolist()
    
    has_state = 'state_name' in df.columns
    has_district = 'district_name' in df.columns
    has_year = 'year' in df.columns
    
    st.markdown("---")
    
    # -------- STEP 4: ANALYSIS (TRENDS) --------
    if has_year and len(num_cols) > 0:
        st.subheader("📈 Trend Analysis over Time")
        trend_col = st.selectbox("Select metric for trend", num_cols, key='trend_sel')
        trend_df = df.groupby('year')[trend_col].sum().reset_index()
        # Ensuring year is treated as category for discrete plotting
        trend_df['year'] = trend_df['year'].astype(str)
        st.line_chart(data=trend_df.set_index('year'), y=trend_col)
    elif not has_year:
        st.info("No time-based column ('year') found. Skipping trend analysis.")

    # -------- STEP 4: ANALYSIS (COMPARISON) --------
    if has_state and len(num_cols) > 0:
        st.subheader("📊 Category Comparisons (State-wise Summary)")
        cat_metric = st.selectbox("Select metric for comparison", num_cols, key='cat_sel')
        state_df = df.groupby('state_name')[cat_metric].sum().reset_index().sort_values(by=cat_metric, ascending=False).head(20)
        st.bar_chart(state_df.set_index('state_name'))

    st.markdown("---")

    # -------- STEP 3 & 6: LOCATION & MAPS --------
    st.subheader("🗺️ Geographic Visualization")
    
    lat_col = next((c for c in df.columns if c.lower() in ['lat', 'latitude']), None)
    lon_col = next((c for c in df.columns if c.lower() in ['lon', 'long', 'longitude']), None)
    
    if lat_col and lon_col:
        st.success("Latitude/Longitude detected. Generating exact point-map.")
        map_data = df[[lat_col, lon_col]].copy()
        if len(num_cols) > 0:
            map_metric = st.selectbox("Metric for map visualization", num_cols, key='point_map')
        st.map(map_data)
        
    elif geojson and has_district and len(num_cols) > 0:
        st.success("No Coordinates found, but GeoJSON and Location columns are available. Generating Choropleth Map.")
        map_metric = st.selectbox("Select metric for mapping", num_cols, key='choro_map')
        
        # Aggregate by district
        dist_df = df.groupby('district_name')[map_metric].sum().reset_index()
        
        # Match using properties.NAME_2 from india_district.geojson
        try:
            fig = px.choropleth(
                dist_df,
                geojson=geojson,
                locations='district_name',
                featureidkey="properties.NAME_2",
                color=map_metric,
                color_continuous_scale="Reds",
                title=f"{map_metric.replace('_', ' ').title()} by District"
            )
            fig.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering choropleth map: {e}")
            st.info("Ensure district names perfectly match between CSV and GeoJSON properties.")
            
    else:
        st.info("Skipping map visualization: No exact coordinates exists AND no matching columns to pair with GeoJSON were found (Needs 'district_name').")