# import streamlit as st
# import json
# import os

# # Load data from JSON file
# def load_data(file_path):
#     if os.path.exists(file_path):
#         with open(file_path, 'r') as file:
#             return json.load(file)
#     else:
#         st.error("File not found!")
#         return []

# # Function to perform actions when a pool is selected
# def action_one(address):
#     st.write(f"Action one executed for pool at address: {address}")

# def action_two(address):
#     st.write(f"Action two executed for pool at address: {address}")

# # Streamlit app layout
# st.set_page_config(page_title="Liquidity Pool Search", layout="wide")

# # Load data from the specified JSON file path
# data_file_path = '/Users/barguesflorian/Documents/LP_project/dataset_pool.json'
# data = load_data(data_file_path)

# # Banner at the top with search field inside
# st.markdown(
#     """
#     <div style="background-color: #4CAF50; height: 15vh; display: flex; justify-content: space-between; align-items: center; padding: 0 20px;">
#         <div>
#             <select id="blockchain-select" style="font-size: 16px;">
#                 <option value="Ethereum">Ethereum</option>
#                 <option value="Base">Base</option>
#             </select>
#         </div>
#         <div style="display: flex; align-items: center;">
#             <span style="color: white; font-size: 20px; margin-right: 10px;">Pool Verified ✔️</span>
#             <!-- Direct search input inside the banner -->
#             <form action="" style="display: inline-block;">
#                 <input id="search" type="text" placeholder="Search" style="padding: 10px; font-size: 16px;" />
#             </form>
#             <!-- Trigger search action -->
#             <button id="search-button" style="padding: 10px; font-size: 16px;" onclick="search()">Search</button>
#         </div>
#     </div>
#     """,
#     unsafe_allow_html=True
# )

# # Add custom CSS to adjust the width of Streamlit's `st.text_input` field
# st.markdown(
#     """
#     <style>
#         .streamlit-expanderHeader {
#             font-size: 1.2em;
#         }
#         .stTextInput>div>div>input {
#             width: 80%;  /* Adjust the width of the text input */
#         }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# # Capture search term using Streamlit's hidden input
# search_term = st.text_input("", placeholder="Enter pool name...", label_visibility="collapsed")

# # Button to trigger the search
# search_button = st.button("Search")

# if search_button:
#     # Filter pools based on the search term entered in the banner
#     if search_term:
#         filtered_pools = [pool for pool in data if search_term.lower() in pool["pool_name"].lower()]
#     else:
#         filtered_pools = []

#     # Display suggestions below the banner
#     if filtered_pools:
#         st.write("Suggestions:")
#         for pool in filtered_pools:
#             if st.button(f"Select Pool: {pool['pool_name']}"):
#                 action_one(pool["address"])
#                 action_two(pool["address"])
#     else:
#         st.write("No pools found.")

import streamlit as st
import subprocess
import json
import os
from PIL import Image
import requests

# Function to run the Bubblemap Python script and display the results
def run_bubblemap_script(pool_address):
    # Run the bubblemap_v4.py script and capture the output
    result = subprocess.run(
        ['python3', 'bubblemap_v4.py', pool_address],  # Use relative path for portability
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Check if the script executed successfully
    if result.returncode == 0:
        st.write("Bubble map generated successfully!")
        image_path = "path/to/save/plot.png"  # Replace this with the actual path where the image is saved
        if os.path.exists(image_path):
            img = Image.open(image_path)
            st.image(img)
        else:
            st.error("Plot image not found at the specified location.")
    else:
        st.error(f"Error running bubblemap_v4.py: {result.stderr.decode()}")

# Function to run the Token Holders Python script and display the results
def run_token_holder_script(pool_address):
    # Run the test_age_&_holders.py script and capture the output
    result = subprocess.run(
        ['python3', 'test_age_&_holders.py', pool_address],  # Use relative path for portability
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Check if the script executed successfully
    if result.returncode == 0:
        data = json.loads(result.stdout.decode())
        st.write("Token holders data:")
        st.json(data)  # Display the data in JSON format
    else:
        st.error(f"Error running test_age_&_holders.py: {result.stderr.decode()}")

# Function to load pool data (Assuming it's a local JSON file or API)
def load_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Banner Section: Search and pool selection
st.set_page_config(page_title="Liquidity Pool Analysis", layout="wide")

# Banner styling and layout
search_term = st.text_input("Search", placeholder="Search", key="search_term")

# Styling for the banner section using Streamlit's markdown (keep it simple and more consistent with Streamlit style)
st.markdown(
    f"""
    <div style="background-color: #4CAF50; height: 15vh; display: flex; justify-content: space-between; align-items: center; padding: 0 20px;">
        <div>
            <select id="blockchain-select" style="font-size: 16px;">
                <option value="Ethereum">Ethereum</option>
                <option value="Base">Base</option>
            </select>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="color: white; font-size: 20px; margin-right: 10px;">Pool Verified ✔️</span>
            <input type="text" placeholder="Search" value="{search_term}" style="margin-right: 10px; padding: 10px; font-size: 16px;" onkeypress="if(event.key === 'Enter'){{this.dispatchEvent(new Event('change'))}}">
            <button style="padding: 10px; font-size: 16px;">Log in</button>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Load pool data from JSON (example path, change as needed)
file_path = 'dataset_pool.json'  # Use relative path for portability
if os.path.exists(file_path):
    pools_data = load_data(file_path)
else:
    st.error(f"Pool data file not found at {file_path}")
    pools_data = []

# Filter pools based on the search term (if entered)
filtered_pools = [pool for pool in pools_data if search_term.lower() in pool["pool_name"].lower()] if search_term else []

# Display filtered pools with action buttons
if filtered_pools:
    st.write("Suggestions:")
    for pool in filtered_pools:
        if st.button(pool["pool_name"]):
            pool_address = pool["address"]
            st.write(f"Selected pool address: {pool_address}")
            run_bubblemap_script(pool_address)  # Run the bubblemap script
            run_token_holder_script(pool_address)  # Run the token holders script
else:
    if search_term:
        st.write("No pools found matching your search.")
    else:
        st.write("Please enter a search term.")
