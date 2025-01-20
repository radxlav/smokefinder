# import streamlit as st
# import client
# from client import RestClient
# import pandas as pd
# import time
# import streamlit_authenticator as stauth


# username = st.secrets['auth_username']
# email = st.secrets['email']
# name = st.secrets['auth_name']
# password = st.secrets['auth_password']

# # Creating the credentials dictionary
# credentials = {
#     'usernames': {
#         username: {
#             'email': email,
#             'name': name,
#             'password': password,
#             # 'logged_in' is not included as it will be managed automatically
#         }
#     }
# }

# # Your configuration for cookie and preauthorized users (replace with your actual values)
# cookie_config = {
#     'expiry_days': 30,
#     'key': 'smokefinder123',  # Replace with your actual key
#     'name': 'smokefinder'  # Replace with your actual cookie name
# }

# # Instantiate the authenticator
# authenticator = stauth.Authenticate(
#     credentials=credentials,
#     cookie_name=cookie_config['name'],
#     key=cookie_config['key'],
#     cookie_expiry_days=cookie_config['expiry_days'],
#     # Include preauthorized or validator if necessary
# )

# name, authentication_status, username = authenticator.login()

# if st.session_state["authentication_status"]:
#     authenticator.logout()
#     st.write(f'Welcome *{st.session_state["name"]}*')
#     st.title('Some content')

#     st.title("Smoke Finder💨")
#     txt = '''1. If You want to save data to Google Sheets, create a new spreadsheet  and share it with the service account email address: streamlit@mta-digital-bi.iam.gserviceaccount.com
#     2. You can change the suggested 'New worksheet name', but when fetching data back from sheets to the 'Summary' tab, the original name will be used.
#     3. When trying to save data to a new worksheet, make sure the worksheet name is unique.
#     4. If something doesn't work, :sob::sob::sob:
#     let him
#     :point_right::point_right::point_right: mateusz.bortnik@mta.digital :point_left::point_left::point_left:
#     know immediately.
#     '''
#     st.markdown(txt)

#     st.header("Roadmap")
#     st.markdown("1. Retreive reviews data from Yelp, Trustpilot, Google, Tripadvisor and Yelp and save them to Google Sheets")
#     st.markdown(":green[Done]")
#     st.markdown("2. Reconstruct reports similar to those in Ahrefs/Semrush")
#     st.markdown(":yellow[In progress]")
#     st.markdown("3. Build a summary page that will visualize the data from all sources and draw insights with GPT model")
#     st.markdown(":yellow[In progress]")

# elif st.session_state["authentication_status"] is False:
#     st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
