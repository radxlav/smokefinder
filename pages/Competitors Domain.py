import streamlit as st
import client
from client import RestClient
import pandas as pd
import time
import re
from google.oauth2 import service_account
import gspread
from pandas import json_normalize
import sys
sys.path.insert(0, '..')
from utils import check_secrets

# Check if secrets are configured before proceeding
if not check_secrets():
    st.stop()

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)

def save_to_new_worksheet(df, sheet_url, worksheet_name):
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
    
    # Create a new worksheet with the given name
    worksheet = sh.add_worksheet(title=worksheet_name, rows="10000", cols="50")
    
    # Clear existing data if any (should be empty since it's a new worksheet)
    worksheet.clear()
    
    # Add new data

    worksheet.insert_rows(df.values.tolist(), row=1)
    
    # Add header
    worksheet.insert_row(df.columns.tolist(), index=1)
    
    st.success(f"Data successfully saved to a new worksheet named '{worksheet_name}' in the Google Sheet.")


st.title("Competitors Domain")
st.markdown('''This endpoint will provide you with a full overview of ranking and traffic data of the competitor domains from organic and paid search. In addition to that, you will get the metrics specific to the keywords both competitor domains and your domain rank for within the same SERP.
            
Fields descriptions and more: https://docs.dataforseo.com/v3/dataforseo_labs/google/competitors_domain/live/?python           ''')
client = RestClient(st.secrets["email"], st.secrets["password"])
target = st.text_input('Target domain', 'ashleystewart.com')
location_name = st.text_input('Location name', 'United States')
sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")
new_worksheet_name = st.text_input("New worksheet name", "Competitors Domain")
language_name = st.text_input('Language name', 'English')
if st.button('Get data'):
    with st.status("Sending a POST request...") as status:
        post_data = dict()
        # simple way to set a task
        post_data[len(post_data)] = dict(
            target=target,
            location_name=location_name,
            language_name=language_name
)

        response = client.post("/v3/dataforseo_labs/google/competitors_domain/live", post_data)

        if response["status_code"] == 20000:
            st.write("POST response:", response)
            task_id = response["tasks"][0]["id"]
            print("Task ID:", task_id)
            status.update(label="Task ready!", state="complete")
        else:
            st.error(f"POST error. Code: {response['status_code']} Message: {response['status_message']}")
            st.stop()

            # Wait a few seconds before checking task status
        time.sleep(2)

    with st.status("Extracting data...") as status:
    # EXTRACT
        def extract_product_details_from_response(response):
            # Initialize an empty DataFrame
            df_items = pd.DataFrame()

            # Safely access nested data using .get() and ensure it's a list before normalization
            items_data = response.get('tasks', [{}])[0].get('result', [{}])[0].get('items')
            
            if isinstance(items_data, list):
                df_items = pd.json_normalize(items_data)
            else:
                st.exception("Warning: 'items' is not a list or is missing. Returning an empty DataFrame.")

            return df_items
                        


            # Usage
        products = extract_product_details_from_response(response)


        st.success("Success!")
        df = pd.DataFrame.from_dict(products)
        csv = df.to_csv(index=False)  # Convert the dataframe to CSV string format
        st.write(df)
        status.update(label="Data extracted!", state="complete", expanded=True)

    st.download_button(
        label="Press to Download",
        data=csv,
        file_name="competitors-domain.csv",
        mime="text/csv",
        key='download-csv'
    )

    save_to_new_worksheet(df, sheet_url, new_worksheet_name)