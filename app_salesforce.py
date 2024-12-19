import streamlit as st
from streamlit_oauth import OAuth2Component
import requests
import os
import base64
import json

# Load environment variables from .env file
from dotenv import dotenv_values
env = dotenv_values(".env")


# Set environment variables
CLIENT_ID = env["CLIENT_ID"]
CLIENT_SECRET = env["CLIENT_SECRET"]
AUTHORIZE_URL = env["AUTHORIZE_URL"]
TOKEN_URL = env["TOKEN_URL"]
REVOKE_TOKEN_URL = env["REVOKE_TOKEN_URL"]
REDIRECT_URI=env["REDIRECT_URI"]

# import logging
# logging.basicConfig(level=logging.INFO)

st.title("Salesforce IDP Example")
st.write("This example shows how to use the raw OAuth2 component to authenticate with a Salesforce OAuth2 and get the user attributes from id_token.")
st.write("The access_token is used to send to the Customer API which is secured by the SnapLogig APIM solution")
st.write("The API is secured by the Callout Authenticator policy which sends the received access token to the Salesforce token introspection endpoint.")
st.write("In case the introspection endpoint returns that the access token is valid, the API is executed and the result is returned to the consumer.")


if "id_token" not in st.session_state:
    # create a button to start the OAuth2 flow
    oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_TOKEN_URL)
    result = oauth2.authorize_button(
        name="Login with Salesforce",
        icon="https://www.salesforce.com/etc/designs/sfdc-www/en_us/favicon.ico",
        redirect_uri=REDIRECT_URI, #"http://localhost:8501"
        scope="full",
        use_container_width=True
    )
    
    if result:
        print(result)
        st.write(result)
        #decode the id_token jwt and get the user's email address
        id_token = result["token"]["id_token"]
        access_token = result["token"]["access_token"]
        # verify the signature is an optional step for security
        payload = id_token.split(".")[1]
        # add padding to the payload if needed
        payload += "=" * (-len(payload) % 4)
        payload = json.loads(base64.b64decode(payload))
        email = payload["email"]
        username = payload["name"]
        st.session_state["user"] = username
        st.session_state["auth"] = email
        st.session_state["access_token"]=access_token
        st.session_state["id_token"]=id_token
        #st.session_state["auth"] = result["token"]
        st.rerun()
else:
    st.write(f"Congrats **{st.session_state.user}**, you are logged in now!")
    
    # Button to call the API
    if st.button("Call Customer API"):
        try:
            # Perform API call
            response = requests.get("https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/run/task/ConnectFasterInc/Markus/FLAM/CustomerAPI")

            headers = {
                    'sl-token': st.session_state["access_token"]
                    }
            # Call the SnapLogic Pinecone Namespace API
            response = requests.get(
                    url="https://prodeu-connectfasterinc-cloud-fm.emea.snaplogic.io/api/1/rest/feed/run/task/ConnectFasterInc/Markus/FLAM/CustomerAPI",
                    headers=headers,
                    verify=False
                    )
            result = response.json()

            # Check if the request was successful
            if response.status_code == 200:
                # Parse and display the API response
                st.success("API call was successful!")
                st.json(response.json())  # Display JSON response
            else:
                # Display an error if the API call fails
                st.error(f"API call failed with status code {response.status_code}")
                st.write(response.text)  # Display the error response from the API

        except requests.exceptions.RequestException as e:
            # Handle any exceptions during the API call
            st.error(f"An error occurred: {e}")
        
    #st.write(st.session_state["auth"])
    #st.write(st.session_state["id_token"])
    if st.button("Logout"):
        #del st.session_state["auth"]
        del st.session_state["id_token"]
        del st.session_state["user"]
        del st.session_state["auth"]
        del st.session_state["access_token"]