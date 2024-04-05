import streamlit as st
import client
from client import RestClient
import pandas as pd
import time
import re
from google.oauth2 import service_account
from gsheetsdb import connect
import gspread

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)

def save_to_new_worksheet(df, sheet_url, worksheet_name):
    # Debugging: Print the data that will be inserted
    print("Debugging: Data to insert:", df.values.tolist())
    
    # Connect to Google Sheets
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )
    conn = connect(credentials=credentials)
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    
    try:
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
        
    except Exception as e:
        print(f"Debugging: An exception occurred: {e}")



st.title("Google Reviews")
st.markdown('''This endpoint provides results from the “Reviews” element of Google SERPs. The results are specific to the selected location and language parameters.
            
Fields descriptions and more: https://docs.dataforseo.com/v3/business_data/google/reviews/task_post/?python
                                https://docs.dataforseo.com/v3/business_data/google/reviews/task_get/?python            ''')
client = RestClient(st.secrets["email"], st.secrets["password"])

url = st.text_input('Google Maps url', 'https://www.google.com/maps/place/Ashley+Stewart/@39.8495135,-95.0893464,6z/data=!4m10!1m2!2m1!1sashley+stewart!3m6!1s0x886b523a1ab8c599:0x61c453a9079053a5!8m2!3d39.8495135!4d-86.1245027!15sCg5hc2hsZXkgc3Rld2FydCIDiAEBWhAiDmFzaGxleSBzdGV3YXJ0kgEVd29tZW5zX2Nsb3RoaW5nX3N0b3Jl4AEA!16s%2Fg%2F1txfpx89?authuser=0&entry=ttu')
sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")
new_worksheet_name = st.text_input("New worksheet name", "Google reviews")
language_name = st.text_input('Language name', 'English')
location_name = st.text_input('Location name', 'United States')
depth = st.number_input(min_value=0, max_value=4490, value=4490, label="Number of reviews to be extracted. Max is 4490.")
def extract_cid_from_url(url):
    # Split the URL by "0x"
    parts = url.split("0x")
    if len(parts) > 2:
        # Return the portion of the second occurrence up to the "!" delimiter
        return parts[2].split("!")[0]
    else:
        return None

cid_hex = extract_cid_from_url(url)
st.write(cid_hex) #debug

if cid_hex:
    cid = int(cid_hex, 16)  # Decoding the hex to int, as the CID is a number, not a UTF-8 encoded string
    st.write(cid)#debug
else:
    st.write("CID not found in the provided URL")



if st.button('Get data'):
    with st.status("Sending a POST request...") as status:

        post_data = dict()
        # simple way to set a task
        post_data[len(post_data)] = dict(
            cid=str(cid),
            depth=depth,
            language_name=language_name,
            location_name=location_name,
            sort_by="newest",
            tag="test",
            postback_url="https://us-central1-force-of-nature-325616.cloudfunctions.net/function-1?id=$id&tag=$tag"
        )

        response = client.post("/v3/business_data/google/reviews/task_post", post_data)

        if response["status_code"] == 20000:
            st.write("POST response:", response)
            task_id = response["tasks"][0]["id"]
            # print("Task ID:", task_id)
        else:
            print(f"POST error. Code: {response['status_code']} Message: {response['status_message']}")
            st.stop()

            # Wait a few seconds before checking task status
        time.sleep(2)

    with st.status("Waiting for the task") as status:
        # GET request to fetch the results of the task
        
        WAIT_TIME = 10
        task_ready = False

        while not task_ready:
            # st.write(f"Retry count: {retry_count}")  # Debugging line
            response = client.get(f"/v3/business_data/google/reviews/task_get/{task_id}")
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

    with st.status("Extracting data...") as status:
        # EXTRACT
        def extract_product_details_from_response(response):
            all_products = []

            # Safely accessing nested data with .get() and ensuring 'items' is a list
            items = response.get('tasks', [{}])[0].get('result', [{}])[0].get('items')

            if isinstance(items, list):
                for item in items:
                    # Using .get() with default values for nested data
                    rating_info = item.get('rating', {})
                    product_info = {
                        "rating": rating_info.get("value", "No rating"),
                        "timestamp": item.get("timestamp", "No timestamp"),
                        "review_text": item.get("review_text", "No review text")
                    }
                    all_products.append(product_info)
            else:
                st.exception("Warning: 'items' is not a list or is missing. Returning an empty list.")

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
        file_name="google-reviews.csv",
        mime="text/csv",
        key='download-csv'
    )

    save_to_new_worksheet(df, sheet_url, new_worksheet_name)
