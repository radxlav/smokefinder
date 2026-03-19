import streamlit as st
import client
from client import RestClient
import pandas as pd
import time
from google.oauth2 import service_account
import gspread
import datetime
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
    try:
        # Replace NaN values with a placeholder string (you can also use df.fillna(0) to replace with zero)
        # df.fillna("NaN", inplace=True)

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

client = RestClient(st.secrets["email"], st.secrets["password"])
st.title("Google Trends")
st.markdown('''This endpoint will provide you with the keyword popularity data from the ‘Explore’ feature of Google Trends. You can check keyword trends for Google Search, Google News, Google Images, Google Shopping, and YouTube.
            
Fields descriptions and more: https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_post/?python
                            https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_get/?python            ''')

sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")
date_from = st.date_input('Date from', datetime.date(2019, 1, 1)).strftime('%Y-%m-%d')
date_to = st.date_input('Date to', datetime.date(2020, 1, 1)).strftime('%Y-%m-%d')
new_worksheet_name = st.text_input("New worksheet name", "Google trends")
location_name = st.text_input("Location name", "United States")
keyword1 = st.text_input("Keyword 1", "seo api", key=1)
keyword2 = st.text_input("Keyword 2", "seo api", key=2)
keyword3 = st.text_input("Keyword 3", "seo api", key=3)
keyword4 = st.text_input("Keyword 4", "seo api", key=4)
keyword5 = st.text_input("Keyword 5", "seo api", key=5)

keywords = [keyword1, keyword2, keyword3, keyword4, keyword5]

if st.button('Get data'):
    with st.status("Sending a POST request..."):
        post_data = dict()
        # simple way to set a task
        post_data[len(post_data)] = dict(
            location_name=location_name,
            date_from=date_from,
            date_to=date_to,
            keywords=keywords
        )

        response = client.post("/v3/keywords_data/google_trends/explore/task_post", post_data)

        if response["status_code"] == 20000:
            st.write("POST response:", response)
            task_id = response["tasks"][0]["id"]
            print("Task ID:", task_id)
        else:
            print(f"POST error. Code: {response['status_code']} Message: {response['status_message']}")
            st.stop()

            # Wait a few seconds before checking task status
        time.sleep(2)
    with st.status("Waiting for the task") as status:
        WAIT_TIME = 10
        task_ready = False
        # task_id='09271218-6487-0170-0000-bb7e2fe0ff5d'
        while not task_ready:
            # st.write(f"Retry count: {retry_count}")  # Debugging line
            response = client.get(f"/v3/keywords_data/google_trends/explore/task_get/{task_id}")
            st.write("GET response:", response)

            if response['status_code'] == 20000:
                task_status = response['tasks'][0]['status_message']
                st.write(f"Task status: {task_status}")  # Debugging line
                if task_status != "Ok.":
                    # st.write(f"Attempt {retry_count + 1}: Task is still in queue. Retrying in {WAIT_TIME} seconds...")
                    
                    time.sleep(WAIT_TIME)
                elif task_status == "Ok.":  # Only set task_ready = True when the task is actually complete
                    task_ready = True
                    st.write("Task is ready.")
                    status.update(label="Task ready!", state="complete")
            else:
                st.write(f"GET error. Code: {response['status_code']} Message: {response['status_message']}")
                break


    # EXTRACT
    def extract_product_details_from_response(response):
        all_products = []

        # Directly accessing the location of results based on the structure of your response
        items = response["tasks"][0]["result"][0]["items"][0]["data"]
        df_items = json_normalize(items)
        return df_items


    # # Usage
    products = extract_product_details_from_response(response)
    print(products)  # This should print the details of the first product

    # st.success("Success!")
    df = pd.DataFrame.from_dict(products)

    pd.to_numeric(df["values"], errors='coerce')
    df['value1'] = df['values'].apply(lambda x: x[0])
    df['value2'] = df['values'].apply(lambda x: x[0])
    # df['values'].fillna('N/A', inplace=True)
    # st.write(df["values"].apply(type))
    csv = df.to_csv(index=False)  # Convert the dataframe to CSV string format

    st.write(df)
    
    st.download_button(
        label="Press to Download",
        data=csv,
        file_name="google-trends.csv",
        mime="text/csv",
        key='download-csv'
    )

    save_to_new_worksheet(df, sheet_url, new_worksheet_name)
