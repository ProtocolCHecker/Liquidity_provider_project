import os
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from web3 import Web3
import streamlit as st

# Function to check the address type
def check_address_type(address):
    infura_url = 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    w3 = Web3(Web3.HTTPProvider(infura_url))
    checksum_address = w3.to_checksum_address(address)
    if not w3.is_address(checksum_address):
        return f"{address} is not a valid Ethereum address."
    code = w3.eth.get_code(checksum_address)
    if code == b'':
        return "EOA"
    else:
        return "Smart Contract"

# Function to perform OAuth and GraphQL query
def oAuth_example(smart_contract_address):
    url = "https://oauth2.bitquery.io/oauth2/token"
    payload = 'grant_type=client_credentials&client_id=2ce4e182-5cc8-4d02-b47d-3f550afa6cdb&client_secret=BMzqn0VSq1Y-rN-33W5lLn1a02&scope=api'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(url, headers=headers, data=payload)
    resp = json.loads(response.text)

    if response.status_code != 200:
        raise Exception(f"OAuth Error: {response.status_code}, {response.text}")

    access_token = response.json().get('access_token')

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
    response_graphql = requests.post(url_graphql, headers=headers_graphql, data=payload_graphql)

    if response_graphql.status_code != 200:
        raise Exception(f"GraphQL request failed: {response_graphql.status_code} {response_graphql.text}")

    data = response_graphql.json()
    token_holders = data['data']['EVM']['TokenHolders']
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

    return holders_data, total_supply

def plot_liquidity_map(holders_data, pool_name, protocol, version, chain):
    labels = [f"{holder['address'][:3]}...{holder['address'][-3:]}" if holder['address'] else "No Address" for holder in holders_data]
    parents = [""] * len(holders_data)
    values = [holder['percentage'] for holder in holders_data]
    texts = [f"{holder['percentage']:.2f}%" for holder in holders_data]

    # Create the treemap with non-empty labels
    treemap_fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        text=texts,
        textposition='middle center',
        textfont=dict(size=[max(10, value * 1.5) for value in values]),
        marker=dict(
            colorscale='Blues',
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>%{label}</b><br>Percentage: %{value:.2f}%<extra></extra>',
        labelvisibility='hidden'  # Hide labels if necessary
    ))

    treemap_fig.update_layout(
        title={
            'text': f'Top 100 LPs position on {pool_name} ({protocol} - {version} - {chain})',
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, weight='bold')
        },
        margin=dict(t=50, l=25, r=25, b=25),
        height=600
    )

    # Display the treemap
    st.plotly_chart(treemap_fig, use_container_width=True)


# Load the pool dataset
with open("/Users/barguesflorian/Documents/LP_project/dataset_pool.json") as f:
    pool_data = json.load(f)

# Streamlit app
st.title("Pool Information App")
st.sidebar.header("Pool Selection")

# User input for pool selection
pool_name = st.sidebar.text_input("Enter the pool you are looking for:")

if pool_name:
    matching_pools = [pool for pool in pool_data if 'pool_name' in pool and pool_name.lower() in pool['pool_name'].lower()]

    if matching_pools:
        st.sidebar.subheader("Select a pool:")
        pool_options = [f"{pool['pool_name']} ({pool['protocol']} - {pool['version']} - {pool['chain']})" for pool in matching_pools]
        selected_pool_option = st.sidebar.selectbox("", pool_options)

        if selected_pool_option:
            selected_pool_data = next(pool for pool in matching_pools if f"{pool['pool_name']} ({pool['protocol']} - {pool['version']} - {pool['chain']})" == selected_pool_option)
            smart_contract_address = selected_pool_data.get('address')

            if st.sidebar.button("Run Analysis"):
                if smart_contract_address:
                    holders_data, total_supply = oAuth_example(smart_contract_address)
                    plot_liquidity_map(holders_data, selected_pool_data['pool_name'], selected_pool_data['protocol'], selected_pool_data['version'], selected_pool_data['chain'])
                else:
                    st.sidebar.error("Smart contract address not found for the selected pool.")
    else:
        st.sidebar.warning("No matching pools found.")
