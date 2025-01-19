# from dune_client.types import QueryParameter
# from dune_client.client import DuneClient

# def borrowing_and_lending_rate(slope1, slope2, U_optimal, reserve_factor, base_rate, utilization_rate):
    
#     if utilization_rate <= U_optimal:
#         borrow_rate = base_rate + slope1 * utilization_rate
#     else:
#         br = base_rate + slope1 * utilization_rate + ((utilization_rate - U_optimal)/(1 - U_optimal))
#     lending_rate = borrow_rate * (1 - reserve_factor)

#     return borrow_rate, lending_rate

# # Initialize the Dune client with your API key
# dune = DuneClient(api_key='jilmiM2y76O5d0xm29P5YWig2pi3R9zq')

# # Query ID
# query_id = 4579566

# # Fetch the latest result of the query
# results_response = dune.get_latest_result(query_id)

# # Extract the results from the response
# results = results_response.result.rows

# # Calculate the total supply (divided by 1,000,000)
# total_supply = sum(row['current_balance'] for row in results) / 1000000

# # Print the results with the balance divided by 1,000,000 and the percentage of the total supply
# for row in results[:100]:
#     address = row['address']
#     current_balance = row['current_balance'] / 1000000
#     percentage_of_supply = (current_balance / total_supply) * 100
#     print(f"Address: {address}, Current Balance: {current_balance}, Percentage of Supply: {percentage_of_supply:.4f}%")



import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from web3 import Web3

# Load the JSON data
with open('/Users/barguesflorian/Documents/LP_project/dataset_lending.json') as f:
    assets_data = json.load(f)

def borrowing_and_lending_rate(base_rate, slope1, slope2, U_optimal, reserve_factor, utilization_rate):
    
    if utilization_rate <= U_optimal:
        borrow_rate = base_rate + slope1 * utilization_rate
    else:
        br = base_rate + slope1 * utilization_rate + ((utilization_rate - U_optimal)/(1 - U_optimal))
    lending_rate = borrow_rate * (1 - reserve_factor)

    return borrow_rate, lending_rate

# Function to match assets
def match_assets(user_input):
    matched_assets = [asset for asset in assets_data if user_input.lower() in asset['pool_name'].lower()]
    return matched_assets

# Function to fetch and process data
def fetch_and_process_data(query_id):
    dune = DuneClient(api_key='jilmiM2y76O5d0xm29P5YWig2pi3R9zq')
    results_response = dune.get_latest_result(query_id)
    results = results_response.result.rows
    total_supply = sum(row['current_balance'] for row in results) / 1000000
    return results, total_supply

# Function to check if the address is a smart contract or an EOA
def check_address_type(address, chain):
    # Map of chains to their respective Infura URLs
    infura_urls = {
        'Ethereum': 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Arbitrum': 'https://arbitrum-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Optimism': 'https://optimism-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Base': 'https://base-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Polygon': 'https://polygon-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    }

    # Select the appropriate Infura URL based on the chain
    infura_url = infura_urls.get(chain, 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b')
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

def get_token_total_supply(chain, token_address, abi, pool_name):
    # Define the Infura URLs
    infura_urls = {
        'Ethereum': 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Arbitrum': 'https://arbitrum-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Optimism': 'https://optimism-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Base': 'https://base-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Polygon': 'https://polygon-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    }

    # Select the appropriate Infura URL based on the chain
    infura_url = infura_urls.get(chain, 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b')

    # Connect to the Ethereum network using Web3
    web3 = Web3(Web3.HTTPProvider(infura_url))

    # Check if connected
    if not web3.is_connected():
        print("Failed to connect to the Ethereum network.")
        return None

    # Create the contract instance
    contract = web3.eth.contract(address=token_address, abi=abi)

    # Get the total supply
    try:
        total_supply = contract.functions.totalSupply().call()
    except Exception as e:
        print(f"Error while fetching total supply: {e}")
        return None

    # Get the coefficient (coef) for the given pool_name from the assets data
    asset_info = next((asset for asset in assets_data if asset['pool_name'] == pool_name), None)
    
    if not asset_info:
        print(f"No information found for pool {pool_name}.")
        return None

    coef = asset_info.get('coef', 1)  # Default to 1 if coef is not found

    # Adjust the total supply based on the coef
    adjusted_total_supply = total_supply / coef

    return adjusted_total_supply

    
abi = '''[{"inputs":[{"internalType":"contract IPool","name":"pool","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"BalanceTransfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"underlyingAsset","type":"address"},{"indexed":true,"internalType":"address","name":"pool","type":"address"},{"indexed":false,"internalType":"address","name":"treasury","type":"address"},{"indexed":false,"internalType":"address","name":"incentivesController","type":"address"},{"indexed":false,"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"indexed":false,"internalType":"string","name":"aTokenName","type":"string"},{"indexed":false,"internalType":"string","name":"aTokenSymbol","type":"string"},{"indexed":false,"internalType":"bytes","name":"params","type":"bytes"}],"name":"Initialized","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"onBehalfOf","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"ATOKEN_REVISION","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"EIP712_REVISION","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"POOL","outputs":[{"internalType":"contract IPool","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"RESERVE_TREASURY_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"UNDERLYING_ASSET_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"receiverOfUnderlying","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getIncentivesController","outputs":[{"internalType":"contract IAaveIncentivesController","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getPreviousIndex","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getScaledUserBalanceAndSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"handleRepayment","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IPool","name":"initializingPool","type":"address"},{"internalType":"address","name":"treasury","type":"address"},{"internalType":"address","name":"underlyingAsset","type":"address"},{"internalType":"contract IAaveIncentivesController","name":"incentivesController","type":"address"},{"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"internalType":"string","name":"aTokenName","type":"string"},{"internalType":"string","name":"aTokenSymbol","type":"string"},{"internalType":"bytes","name":"params","type":"bytes"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"caller","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mint","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mintToTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"scaledBalanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"scaledTotalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IAaveIncentivesController","name":"controller","type":"address"}],"name":"setIncentivesController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferOnLiquidation","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"target","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferUnderlyingTo","outputs":[],"stateMutability":"nonpayable","type":"function"}]'''  # Use the full ABI provided

# Function to plot the treemap
def plot_liquidity_map(holders_data, total_supply, asset_info):
    labels = [f"{holder['address'][:3]}...{holder['address'][-3:]}" for holder in holders_data]
    parents = [""] * len(holders_data)
    values = [holder['percentage_of_supply'] for holder in holders_data]
    texts = [f"{holder['percentage_of_supply']:.2f}%" for holder in holders_data]  # Show percentage on the treemap

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
        [f"#{i+1} - {holder['address'][:3]}...{holder['address'][-3:]}", f"{holder['percentage_of_supply']:.2f}%", check_address_type(holder['address'], asset_info['chain'])]
        for i, holder in enumerate(holders_data)
    ]
    ranking_headers = ["Wallet", "Percentage", "Type"]

    fig.add_trace(go.Table(
        header=dict(values=ranking_headers),
        cells=dict(values=list(zip(*ranking_data)))
    ), row=1, col=2)

    # Update layout with dynamic title
    title_text = f"Top 100 LPs position on {asset_info['pool_name']} - {asset_info['protocol']} {asset_info['version']} on {asset_info['chain']}"
    fig.update_layout(
        title={
            'text': title_text,
            'x': 0.5,   # Center the title
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=18, weight='bold')  # Make the title bold
        },
        margin=dict(t=50, l=25, r=25, b=25)
    )

    st.plotly_chart(fig)

# Streamlit app layout
st.title('Asset Borrowing and Lending Rates')

user_input = st.text_input('Enter the asset you are looking for:')

if user_input:
    matched_assets = match_assets(user_input)
    if matched_assets:
        st.write('Matching assets:')
        for asset in matched_assets:
            unique_key = f"{asset['pool_name']}-{asset['chain']}-{asset['version']}"
            st.write(f"{asset['pool_name']} ({asset['chain']} - {asset['version']})")
            if st.button(f"Select {asset['pool_name']}", key=unique_key):
                query_id = asset['dune_a_id']
                results, total_supply = fetch_and_process_data(query_id)

                # Prepare data for treemap
                holders_data = []
                for row in results[:100]:
                    address = row['address']
                    current_balance = row['current_balance'] / 1000000
                    percentage_of_supply = (current_balance / total_supply) * 100
                    holders_data.append({
                        'address': address,
                        'current_balance': current_balance,
                        'percentage_of_supply': percentage_of_supply
                    })

                # Plot the treemap with dynamic title
                plot_liquidity_map(holders_data, total_supply, asset)
    else:
        st.write('No matching assets found.')