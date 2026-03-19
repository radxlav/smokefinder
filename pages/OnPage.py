import streamlit as st
import client
from client import RestClient
import pandas as pd
import time
from random import Random
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
    
    # Add new data
    worksheet.insert_rows(df.values.tolist(), row=1)
    
    # Add header
    worksheet.insert_row(df.columns.tolist(), index=1)
    
    st.success(f"Data successfully saved to a new worksheet named '{worksheet_name}' in the Google Sheet.")

client = RestClient(st.secrets["email"], st.secrets["password"])
st.title("OnPage")
st.markdown('''Using this function, you can get the overall information on a website as well as drill down into exact on-page issues of a website that has been scanned. As a result, you will know what functions to use for receiving detailed data for each of the found issues.
            
Fields descriptions and more: https://docs.dataforseo.com/v3/on_page/summary/?python            ''')

target = st.text_input('Target', 'ashleystewart.com')
max_crawl_pages = st.text_input('Max crawl pages', '10')
sheet_url = st.text_input('Sheet url', "https://docs.google.com/spreadsheets/d/1pe-M1yQ4jPP8jlH7Hadw1Xkc9KZo2PRTKwaYTnrKxsI/edit#gid=0")
new_worksheet_name = st.text_input("New worksheet name", "OnPage data")


if st.button('Get data'):
    with st.status("Sending a POST request...") as status:
        rnd = Random()
        post_data = dict()

        post_data[rnd.randint(1, 30000000)] = dict(
            target=target,
            max_crawl_pages=max_crawl_pages
        )

        # POST /v3/on_page/task_post
        # the full list of possible parameters is available in documentation
        response = client.post("/v3/on_page/task_post", post_data)

        if response["status_code"] == 20000:
            st.write("POST response:", response)
            task_id = response["tasks"][0]["id"]
            # st.write("Task ID:", task_id)
        else:
            st.write(f"POST error. Code: {response['status_code']} Message: {response['status_message']}")
            st.stop()


    # GET request to fetch the results of the task
    with st.status("Waiting for the task") as status:
        WAIT_TIME = 10

        task_ready = False
        crawl_ready=False
        while not task_ready or not crawl_ready:
            # st.write(f"Retry count: {retry_count}")  # Debugging line
            response = client.get(f"/v3/on_page/summary/{task_id}")
            st.write("GET response:", response)

            if response['status_code'] == 20000:
                task_status = response['tasks'][0]['status_message']
                # st.write(f"Task status: {task_status}")  # Debugging line
                if task_status == "Task In Queue":
                    st.write(f"Attempt Task is still in queue. Retrying in {WAIT_TIME} seconds...")
                    
                    time.sleep(WAIT_TIME)
                elif task_status == "Ok.": # Only set task_ready = True when the task is actually complete
                    task_ready = True
                    # st.write("Task is ready.")  # Debugging line
                    # st.write("GET response:", response)
                    crawl_status = response['tasks'][0]['result'][0]['crawl_progress']
                    # st.write(crawl_status)
                    if crawl_status == "in_progress":
                            time.sleep(WAIT_TIME)
                    elif crawl_status == "finished":
                            crawl_ready = True
                            status.update(label="Task ready!", state="complete")
                            # st.write("crawl ready GET response:", response)
            else:
                st.write(f"GET error. Code: {response['status_code']} Message: {response['status_message']}")
                break



# EXTRACT
    with st.status("Extracting data...") as status:
        data = response["tasks"][0]

        # Recursive function to flatten nested dictionaries
        def flatten_dict(d, parent_key='', sep='_'):
            items = {}
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.update(flatten_dict(v, new_key, sep=sep))
                else:
                    items[new_key] = v
            return items

        # Apply the flatten_dict function to each item in the result list
        flattened_data = [flatten_dict(item) for item in data['result']]

        # Convert to DataFrame
        df = pd.DataFrame(flattened_data)
        df = df.melt(var_name='Attribute', value_name='Value')
        # Display the DataFrame
        print(df)


        st.success("Success!")

        csv = df.to_csv(index=False)  # Convert the dataframe to CSV string format
        st.write(df)
        status.update(label="Data extracted!", state="complete", expanded=True)

    st.download_button(
        label="Press to Download",
        data=csv,
        file_name="OnPage data.csv",
        mime="text/csv",
        key='download-csv'
    )
    save_to_new_worksheet(df, sheet_url, new_worksheet_name)





