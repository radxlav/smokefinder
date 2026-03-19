import streamlit as st
import client
from client import RestClient
import pandas as pd
import time
from google.oauth2 import service_account
import gspread
import plotly.express as px
import sys
sys.path.insert(0, '..')
from utils import check_secrets

st.set_page_config(page_title = 'Smoke Finder',
                    layout='wide',
                    initial_sidebar_state='collapsed')

st.title("Summary")

# Check if secrets are configured before proceeding
if not check_secrets():
    st.stop()

def fetch_all_data_from_worksheets(sheet_url):
    # Initialize the dictionary to hold DataFrames
    dfs = {}
    
    try:
        # Connect to Google Sheets
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
            ],
        )
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])

        # Open the Google Sheet
        sheet_id = sheet_url.split('/')[-2]
        sh = gc.open_by_key(sheet_id)
        
        # Get a list of all worksheets
        all_worksheets = sh.worksheets()
        
        # Get names of all worksheets
        worksheet_names = [ws.title for ws in all_worksheets]
        
        for worksheet_name in worksheet_names:
            # Open worksheet by name
            worksheet = sh.worksheet(worksheet_name)
            
            # Fetch all values
            values = worksheet.get_all_values()
            
            # Create a DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            
            # Store in the dictionary
            dfs[worksheet_name] = df
        
        st.success("Data successfully fetched from all worksheets in the Google Sheet.")
        
    except Exception as e:
        st.error(f"An error occurred while fetching data: {e}")
    
    return dfs


sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")



data_frames = fetch_all_data_from_worksheets(sheet_url)

trustpilot_reviews = data_frames.get('Trustpilot reviews', pd.DataFrame()).sort_values(by='timestamp', ascending=True)
trustpilot_reviews['cumulative_avg_rating'] = trustpilot_reviews['rating'].expanding().mean()
trustpilot_reviews['timestamp'] = pd.to_datetime(trustpilot_reviews['timestamp']).dt.date
trustpilot_reviews_fig = px.line(trustpilot_reviews, x='timestamp', y='cumulative_avg_rating', line_shape="spline")

yelp_reviews = data_frames.get('Yelp reviews', pd.DataFrame()).sort_values(by='timestamp', ascending=True)
yelp_reviews['cumulative_avg_rating'] = yelp_reviews['rating'].expanding().mean()
yelp_reviews['timestamp'] = pd.to_datetime(yelp_reviews['timestamp']).dt.date
yelp_reviews_fig = px.line(yelp_reviews, x='timestamp', y='cumulative_avg_rating', line_shape="spline")

google_reviews = data_frames.get('Google reviews', pd.DataFrame()).sort_values(by='timestamp', ascending=True)
google_reviews['cumulative_avg_rating'] = google_reviews['rating'].expanding().mean()
google_reviews['timestamp'] = pd.to_datetime(google_reviews['timestamp']).dt.date
google_reviews_fig = px.line(google_reviews, x='timestamp', y='cumulative_avg_rating', line_shape="spline")

tripadvisor_reviews = data_frames.get('Tripadvisor reviews', pd.DataFrame()).sort_values(by='timestamp', ascending=True)
tripadvisor_reviews['cumulative_avg_rating'] = tripadvisor_reviews['rating'].expanding().mean()
tripadvisor_reviews['timestamp'] = pd.to_datetime(tripadvisor_reviews['timestamp']).dt.date
tripadvisor_reviews_fig = px.line(tripadvisor_reviews, x='timestamp', y='cumulative_avg_rating', line_shape="spline")

onpage_data = data_frames.get('OnPage data', pd.DataFrame())

content_analysis_data = data_frames.get('Content Analysis data', pd.DataFrame())

google_trends = data_frames.get('Google trends', pd.DataFrame()).sort_values(by='date_from', ascending=True)
google_trends_fig = px.line(google_trends, x='date_from', y='values', line_shape="spline")


st.subheader('Trustpilot reviews')
col1, col2 = st.columns(2)
col1.dataframe(trustpilot_reviews)
col2.plotly_chart(trustpilot_reviews_fig)

st.subheader('Yelp reviews')
col1, col2 = st.columns(2)
col1.dataframe(yelp_reviews)
col2.plotly_chart(yelp_reviews_fig)

st.subheader('Google reviews')
col1, col2 = st.columns(2)
col1.dataframe(google_reviews)
col2.plotly_chart(google_reviews_fig)

st.subheader('Tripadvisor reviews')
col1, col2 = st.columns(2)
col1.dataframe(tripadvisor_reviews)
col2.plotly_chart(tripadvisor_reviews_fig)

st.subheader('Google trends')
col1, col2 = st.columns(2)
col1.dataframe(google_trends)
col2.plotly_chart(google_trends_fig)


st.subheader('OnPage data')
col1, col2 = st.columns(2)
col1.dataframe(onpage_data)

st.subheader('Content Analysis data')
col1, col2 = st.columns(2)
col1.dataframe(content_analysis_data)