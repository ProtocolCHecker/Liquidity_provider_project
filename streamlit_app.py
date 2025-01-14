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



import os
import requests
import json
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from web3 import Web3


def check_address_type(address):
    # Connect to Infura using your project ID
    infura_url = 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    w3 = Web3(Web3.HTTPProvider(infura_url))

    # Convert address to checksum address
    checksum_address = w3.to_checksum_address(address)

    # Check if the address is valid
    if not w3.is_address(checksum_address):
        return f"{address} is not a valid Ethereum address."

    # Check if the address is an EOA or a smart contract
    code = w3.eth.get_code(checksum_address)
    if code == b'':
        return "EOA"
    else:
        return "Smart Contract"


def oAuth_example(smart_contract_address):
    # Step 1: Obtain the access token
    url = "https://oauth2.bitquery.io/oauth2/token"
    payload = 'grant_type=client_credentials&client_id=2ce4e182-5cc8-4d02-b47d-3f550afa6cdb&client_secret=BMzqn0VSq1Y-rN-33W5lLn1a02&scope=api'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(url, headers=headers, data=payload)
    resp = json.loads(response.text)

    if response.status_code != 200:
        raise Exception(f"OAuth Error: {response.status_code}, {response.text}")

    access_token = response.json().get('access_token')

    # Step 2: Make the GraphQL query
    url_graphql = "https://streaming.bitquery.io/graphql"
    headers_graphql = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    graphql_query = f"""
    {{
        EVM(dataset: archive, network: eth) {{
        TokenHolders(
            date: "2025-05-01"
            tokenSmartContract: "{smart_contract_address}"
            limit: {{ count: 100 }}
            orderBy: {{ descending: Balance_Amount }}
        ) {{
            Holder {{
            Address
            }}
            Balance {{
            Amount
            }}
        }}
        }}
    }}
    """

    payload_graphql = json.dumps({'query': graphql_query})

    # Step 3: Send the request to the GraphQL API
    response_graphql = requests.post(url_graphql, headers=headers_graphql, data=payload_graphql)

    if response_graphql.status_code != 200:
        raise Exception(f"GraphQL request failed: {response_graphql.status_code} {response_graphql.text}")

    data = response_graphql.json()
    token_holders = data['data']['EVM']['TokenHolders']

    # Calculate total supply
    total_supply = sum(float(holder['Balance']['Amount']) for holder in token_holders)

    holders_data = []

    for holder in token_holders:
        address = holder['Holder']['Address']
        balance = float(holder['Balance']['Amount'])
        percentage_of_supply = (balance / total_supply) * 100 if total_supply > 0 else 0
        address_type = check_address_type(address)

        holders_data.append({
            'address': address,
            'balance': balance,
            'percentage': percentage_of_supply,
            'type': address_type
        })

    # Save to JSON file with additional metadata
    with open('token_holders.json', 'w') as json_file:
        json.dump({"timestamp": datetime.now().isoformat(), "data": holders_data}, json_file)

    # Create the plot with rectangles
    plot_liquidity_map(holders_data, total_supply)

    return holders_data, total_supply


def plot_liquidity_map(holders_data, total_supply):
    labels = [f"{holder['address'][:3]}...{holder['address'][-3:]}" for holder in holders_data]
    parents = [""] * len(holders_data)
    values = [holder['percentage'] for holder in holders_data]
    texts = [f"{holder['percentage']:.2f}%" for holder in holders_data]  # Show percentage on the treemap

    # Create subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'treemap'}, {'type': 'table'}]],
                        column_widths=[0.7, 0.3])

    # Add treemap
    fig.add_trace(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        text=texts,  # Add percentage text on the treemap
        textposition='middle center',  # Center the text
        marker=dict(
            colorscale='Blues',
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>%{label}</b><br>Percentage: %{value:.2f}%<extra></extra>'
    ), row=1, col=1)

    # Add ranking table
    ranking_data = [
        [f"#{i+1} - {holder['address'][:3]}...{holder['address'][-3:]}", f"{holder['percentage']:.2f}%", holder['type']]
        for i, holder in enumerate(holders_data)
    ]
    ranking_headers = ["Wallet", "Percentage", "Type"]

    fig.add_trace(go.Table(
        header=dict(values=ranking_headers),
        cells=dict(values=list(zip(*ranking_data)))
    ), row=1, col=2)

    # Update layout
    fig.update_layout(
        title={
            'text': 'Top 100 Token Holders',
            'x': 0.5,   # Center the title
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=18, weight='bold')  # Make the title bold
        },
        margin=dict(t=50, l=25, r=25, b=25)
    )

    st.plotly_chart(fig)


# Streamlit UI
st.title('Ethereum Token Holders Analysis')

# Input field for smart contract address
smart_contract_address = st.text_input('Enter Smart Contract Address', '0x3041cbd36888becc7bbcbc0045e3b1f144466f5f')

if st.button('Fetch Token Holders Data'):
    # Use the existing check_address_type function to validate the address
    address_type = check_address_type(smart_contract_address)
    
    if "is not a valid Ethereum address" in address_type:
        st.error(f'Invalid Ethereum address entered: {smart_contract_address}')
    else:
        oAuth_example(smart_contract_address)
