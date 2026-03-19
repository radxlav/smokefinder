import streamlit as st
import client
from client import RestClient
import pandas as pd
import time
from google.oauth2 import service_account
import gspread
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
    try:
        # Replace NaN values with a placeholder string (you can also use df.fillna(0) to replace with zero)
        df.fillna("NaN", inplace=True)

        # Replace Inf and -Inf with placeholder strings
        df.replace([float('inf'), float('-inf')], ["Inf", "-Inf"], inplace=True)

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
        worksheet = sh.add_worksheet(title=worksheet_name, rows="1000", cols="50")

        # Clear existing data if any (should be empty since it's a new worksheet)
        worksheet.clear()

        # Add header
        worksheet.insert_row(df.columns.tolist(), index=1)

        # Add new data
        for i, value in enumerate(df.values.tolist()):
            worksheet.insert_row(value, index=i + 2)
        
        st.success(f"Data successfully saved to a new worksheet named '{worksheet_name}' in the Google Sheet.")
        
    except Exception as e:
        st.error(f"An error occurred: {e}")


st.title("Content Analysis")
st.markdown('''This endpoint will provide you with detailed citation data available for the target keyword.

            
Fields descriptions and more: https://docs.dataforseo.com/v3/content_analysis/search/live/?python          ''')
client = RestClient(st.secrets["email"], st.secrets["password"])

keyword = st.text_input('Keyword', 'Ashley Stewart')
sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")
new_worksheet_name = st.text_input("New worksheet name", "Content Analysis data")

if st.button('Get data'):
    with st.status("Sending a POST request...") as status:
        post_data = dict()
        # simple way to set a task
        post_data[len(post_data)] = dict(keyword=keyword)

        response = client.post("/v3/content_analysis/search/live", post_data)

        if response["status_code"] == 20000:
            # st.write("POST response:", response)
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
            items = response["tasks"][0]["result"][0]["items"]

            for item in items:
                product_info = {
                    "url": item["url"],
                    "fetch_time": item["fetch_time"],
                    "country": item["country"],
                    "score": item["score"],
                    "content_type": item["content_info"]["content_type"],
                    "title": item["content_info"]["title"],
                    "snippet": item["content_info"]["snippet"],
                    "anger": item["content_info"]["sentiment_connotations"]["anger"],
                    "happiness": item["content_info"]["sentiment_connotations"]["happiness"],
                    "love": item["content_info"]["sentiment_connotations"]["love"],
                    "sadness": item["content_info"]["sentiment_connotations"]["sadness"],
                    "share": item["content_info"]["sentiment_connotations"]["share"],
                    "fun": item["content_info"]["sentiment_connotations"]["fun"],
                    "positive": item["content_info"]["connotation_types"]["positive"],
                    "negative": item["content_info"]["connotation_types"]["negative"],
                    "neutral": item["content_info"]["connotation_types"]["neutral"],
                    "date_published": item["content_info"]["date_published"],
                    "content_quality_score": item["content_info"]["content_quality_score"]
                }
                all_products.append(product_info)

            return all_products

        # Usage
        products = extract_product_details_from_response(response)
        print(products)  # This should print the details of the first product
        df = pd.DataFrame.from_dict(products)
        st.dataframe(df)
        csv = df.to_csv(index=False)  # Convert the dataframe to CSV string format
        status.update(label="Data extracted!", state="complete", expanded=True)

    st.download_button(
        label="Press to Download",
        data=csv,
        file_name="content-analysis.csv",
        mime="text/csv",
        key='download-csv'
    )
    save_to_new_worksheet(df, sheet_url, new_worksheet_name)