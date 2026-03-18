import streamlit as st
import client
from client import RestClient
import pandas as pd
import time
from google.oauth2 import service_account
from gsheetsdb import connect
import gspread
from flatten_json import flatten
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
conn = connect(credentials=credentials)




def save_to_new_worksheet(df, sheet_url, worksheet_name):
    # Connect to Google Sheets
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )
    conn = connect(credentials=credentials)
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    
    # Open the Google Sheet
    sheet_id = sheet_url.split('/')[-2]
    sh = gc.open_by_key(sheet_id)
    
    # Create a new worksheet with the given name
    worksheet = sh.add_worksheet(title=worksheet_name, rows="1000", cols="50")
    
    # Clear existing data if any (should be empty since it's a new worksheet)
    worksheet.clear()
    
    # Add new data
    worksheet.insert_rows(df.values.tolist(), row=1)
    
    # Add header
    worksheet.insert_row(df.columns.tolist(), index=1)
    
    st.success(f"Data successfully saved to a new worksheet named '{worksheet_name}' in the Google Sheet.")

client = RestClient(st.secrets["email"], st.secrets["password"])

st.title("Trustpilot reviews")

st.markdown('''This endpoint provides reviews published on the Trustpilot platform for the local establishment specified in the domain field.
            
Fields descriptions and more: https://docs.dataforseo.com/v3/business_data/trustpilot/reviews/task_post/?python
                            https://docs.dataforseo.com/v3/business_data/trustpilot/reviews/task_get/?python   ''')

domain = st.text_input('Domain', 'www.ashleystewart.com')
sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")
new_worksheet_name = st.text_input("New worksheet name", "Trustpilot reviews")
depth = st.number_input(min_value=0, max_value=25000, value=25000, label="Number of reviews to be extracted. Max is 25000.")

if st.button('Get data'):
    with st.status("Waiting for the task") as status:
        # POST request to enqueue a task
        post_data = dict()
        post_data[len(post_data)] = dict(domain=domain,depth=depth,sort_by="recency")
        response = client.post("/v3/business_data/trustpilot/reviews/task_post", post_data)
        
        if response["status_code"] == 20000:
            st.write("POST response:", response)
            task_id = response["tasks"][0]["id"]
            # st.write("Task ID:", task_id)
        else:
            st.write(f"POST error. Code: {response['status_code']} Message: {response['status_message']}")
            st.stop()

    # Wait a few seconds before checking task status
    time.sleep(2)
    with st.status("Waiting for the task") as status:
        # GET request to fetch the results of the task

        WAIT_TIME = 10
        retry_count = 0
        task_ready = False

        while not task_ready:
            # st.write(f"Retry count: {retry_count}")  # Debugging line
            response = client.get(f"/v3/business_data/trustpilot/reviews/task_get/{task_id}")
            st.write("GET response:", response)

            if response['status_code'] == 20000:
                task_status = response['tasks'][0]['status_message']
                # st.write(f"Task status: {task_status}")  # Debugging line
                if task_status == "Task In Queue":
                    # st.write(f"Attempt {retry_count + 1}: Task is still in queue. Retrying in {WAIT_TIME} seconds...")

                    time.sleep(WAIT_TIME)
                elif task_status == "Ok.":  # Only set task_ready = True when the task is actually complete
                    task_ready = True
                    status.update(label="Task ready!", state="complete")
                    # st.write("Task is ready.")  # Debugging line
            else:
                st.write(f"GET error. Code: {response['status_code']} Message: {response['status_message']}")
                break


            



    # EXTRACT
    def extract_product_details_from_response(response):
        all_products = []

        # Directly accessing the location of results based on the structure of your response
        items = response["tasks"][0]["result"][0]["items"]

        if items is not None:
            for item in items:
                product_info = {
                    "rating": item.get("rating", {}).get("value", "No rating"),  # Added .get() for safe access
                    "timestamp": item.get("timestamp", "No timestamp"),  # Use .get() with default values
                    "review_text": item.get("review_text", "No review text")
                }
                all_products.append(product_info)

        return all_products

    # Usage
    products = extract_product_details_from_response(response)
    print(products)  # This should print the details of the first product
      
    # products = [flatten(item) for item in response["tasks"]]     



    st.success("Success!")
    df = pd.DataFrame.from_dict(products)
    csv = df.to_csv(index=False)  # Convert the dataframe to CSV string format
    st.write(df)

    st.download_button(
        label="Press to Download",
        data=csv,
        file_name="trustpilot-reviews.csv",
        mime="text/csv",
        key='download-csv'
    )


    
    save_to_new_worksheet(df, sheet_url, new_worksheet_name)