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


st.title("Google Ads keywords for site")
st.markdown('''This endpoint will provide you with a list of keywords relevant to the specified domain along with their bids, search volumes for the last month, search volume trends for the last year (for estimating search volume dynamics), and competition levels.
            
Fields descriptions and more: https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/?bash            ''')
client = RestClient(st.secrets["email"], st.secrets["password"])
target = st.text_input('Target domain', 'ashleystewart.com')
location_name = st.text_input('Location name', 'United States')
sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")
new_worksheet_name = st.text_input("New worksheet name", "Keywords for site")

if st.button('Get data'):
    with st.status("Sending a POST request...") as status:
        post_data = dict()
        # simple way to set a task
        post_data[len(post_data)] = dict(
        location_name=location_name,
        target=target)

        response = client.post("/v3/keywords_data/google_ads/keywords_for_site/live", post_data)

        if response["status_code"] == 20000:
            st.write("POST response:", response)
            task_id = response["tasks"][0]["id"]
            print("Task ID:", task_id)
            status.update(label="Task ready!", state="complete")
        else:
            print(f"POST error. Code: {response['status_code']} Message: {response['status_message']}")
            st.stop()

            # Wait a few seconds before checking task status
        time.sleep(2)

    with st.status("Extracting data...") as status:
    # EXTRACT
        def extract_product_details_from_response(response):
            all_products = []

            # Directly accessing the location of results based on the structure of your response
            items = response["tasks"][0]["result"]
            print(items)

            for item in items:
                product_info = {
                    "keyword": item["keyword"],
                    "location_code": (item["location_code"]),
                    "language_code": (item["language_code"]),
                    "search_partners": item["search_partners"],
                    "competition": item["competition"],
                    "competition_index": str(item["competition_index"]),
                    "search_volume": item["search_volume"],
                    "low_top_of_page_bid": str(item["low_top_of_page_bid"]),
                    "high_top_of_page_bid": str(item["high_top_of_page_bid"]),
                    # "type": str(item["keyword_annotations"]["concepts"][0]["concept_group"]["type"])


                }


                all_products.append(product_info)
                

            return all_products

            # Usage
        products = extract_product_details_from_response(response)
        print(products)  # This should print the details of the first product

        st.success("Success!")
        df = pd.DataFrame.from_dict(products)
        csv = df.to_csv(index=False)  # Convert the dataframe to CSV string format
        st.write(df)
        status.update(label="Data extracted!", state="complete", expanded=True)

    st.download_button(
        label="Press to Download",
        data=csv,
        file_name="google-ads-keywords.csv",
        mime="text/csv",
        key='download-csv'
    )
    # st.write(df.values.tolist())
    save_to_new_worksheet(df, sheet_url, new_worksheet_name)