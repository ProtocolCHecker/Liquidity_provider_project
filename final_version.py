import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from web3 import Web3
import plotly.express as px

# Load the JSON data
with open('/Users/barguesflorian/Documents/LP_project/dataset_lending.json') as f:
    assets_data = json.load(f)

def borrowing_and_lending_rate(base_rate, slope1, slope2, U_optimal, reserve_factor, utilization_rate):
    if utilization_rate <= U_optimal:
        b_rate = base_rate + slope1 * utilization_rate
    else:
        b_rate = base_rate + slope1 * utilization_rate + ((utilization_rate - U_optimal) / (1 - U_optimal))
    l_rate = b_rate * (1 - reserve_factor)

    return b_rate, l_rate

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
    infura_urls = {
        'Ethereum': 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Arbitrum': 'https://arbitrum-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Optimism': 'https://optimism-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Base': 'https://base-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Polygon': 'https://polygon-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    }

    infura_url = infura_urls.get(chain, 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b')
    w3 = Web3(Web3.HTTPProvider(infura_url))

    checksum_address = w3.to_checksum_address(address)

    if not w3.is_address(checksum_address):
        return f"{address} is not a valid Ethereum address."

    code = w3.eth.get_code(checksum_address)
    if code == b'':
        return "EOA"
    else:
        return "Smart Contract"

# Function to fetch token total supply from blockchain
def get_token_total_supply(chain, token_address, abi):
    infura_urls = {
        'Ethereum': 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Arbitrum': 'https://arbitrum-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Optimism': 'https://optimism-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Base': 'https://base-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Polygon': 'https://polygon-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    }

    infura_url = infura_urls.get(chain, 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b')
    web3 = Web3(Web3.HTTPProvider(infura_url))

    if not web3.is_connected():
        print("Failed to connect to the Ethereum network.")
        return None

    contract = web3.eth.contract(address=token_address, abi=abi)

    try:
        total_supply = contract.functions.totalSupply().call()
    except Exception as e:
        print(f"Error while fetching total supply: {e}")
        return None

    return total_supply

# ABI for ERC20 contract (simplified version)
abi = '''[{"inputs":[{"internalType":"contract IPool","name":"pool","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"BalanceTransfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"underlyingAsset","type":"address"},{"indexed":true,"internalType":"address","name":"pool","type":"address"},{"indexed":false,"internalType":"address","name":"treasury","type":"address"},{"indexed":false,"internalType":"address","name":"incentivesController","type":"address"},{"indexed":false,"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"indexed":false,"internalType":"string","name":"aTokenName","type":"string"},{"indexed":false,"internalType":"string","name":"aTokenSymbol","type":"string"},{"indexed":false,"internalType":"bytes","name":"params","type":"bytes"}],"name":"Initialized","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"onBehalfOf","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"ATOKEN_REVISION","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"EIP712_REVISION","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"POOL","outputs":[{"internalType":"contract IPool","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"RESERVE_TREASURY_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"UNDERLYING_ASSET_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"receiverOfUnderlying","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getIncentivesController","outputs":[{"internalType":"contract IAaveIncentivesController","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getPreviousIndex","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getScaledUserBalanceAndSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"handleRepayment","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IPool","name":"initializingPool","type":"address"},{"internalType":"address","name":"treasury","type":"address"},{"internalType":"address","name":"underlyingAsset","type":"address"},{"internalType":"contract IAaveIncentivesController","name":"incentivesController","type":"address"},{"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"internalType":"string","name":"aTokenName","type":"string"},{"internalType":"string","name":"aTokenSymbol","type":"string"},{"internalType":"bytes","name":"params","type":"bytes"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"caller","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mint","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mintToTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"scaledBalanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"scaledTotalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IAaveIncentivesController","name":"controller","type":"address"}],"name":"setIncentivesController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferOnLiquidation","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"target","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferUnderlyingTo","outputs":[],"stateMutability":"nonpayable","type":"function"}]'''  # Use the full ABI provided

import plotly.graph_objects as go
import pandas as pd

def plot_liquidity_map(holders_data, total_supply, asset, borrow_rate, lending_rate, utilization_rate):
    # Prepare the data for the treemap
    df = pd.DataFrame(holders_data)
    
    # Add a column for the size of each LP's position relative to the total supply
    df['percentage_of_supply'] = df['percentage_of_supply'].round(2)
    
    # Add a column for the rank based on the balance
    df['rank'] = df['percentage_of_supply'].rank(ascending=False)
    
    # Labels for the treemap
    labels = [f"{holder['address'][:3]}...{holder['address'][-3:]}" for holder in holders_data]
    parents = [""] * len(holders_data)
    values = [holder['percentage_of_supply'] for holder in holders_data]
    texts = [f"{holder['percentage_of_supply']:.2f}%" for holder in holders_data]
    
    # Ranking data for the table
    ranking_data = [
        [f"#{i+1} - {holder['address'][:3]}...{holder['address'][-3:]}", f"{holder['percentage_of_supply']:.2f}%", holder['address']]
        for i, holder in enumerate(holders_data)
    ]
    ranking_headers = ["Wallet", "Percentage", "Address"]
    
    # Dynamically create the title with the borrowing, lending rates, and utilization rate
    title_text = (f"Top 100 Lending position on {asset['pool_name']} - {asset['protocol']} "
                  f"{asset['version']} on {asset['chain']}<br>"
                  f"Borrow Rate: {borrow_rate:.2f}% | Lending Rate: {lending_rate:.2f}% | "
                  f"Utilization Rate: {utilization_rate:.2f}%")

    # Create a figure with subplots for both treemap and ranking table
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'treemap'}, {'type': 'table'}]],
                        column_widths=[0.7, 0.3])

    # Add Treemap
    fig.add_trace(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        text=texts,
        textposition='middle center',
        marker=dict(
            colorscale='Blues',
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>%{label}</b><br>Percentage: %{value:.2f}%<extra></extra>'
    ), row=1, col=1)

    # Add Ranking Table
    fig.add_trace(go.Table(
        header=dict(values=ranking_headers),
        cells=dict(values=list(zip(*ranking_data)))
    ), row=1, col=2)

    # Update layout for title and margins
    fig.update_layout(
        title={
            'text': title_text,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=18, weight='bold')
        },
        margin=dict(t=50, l=25, r=25, b=25)
    )

    # Show the plot
    st.plotly_chart(fig)



# Streamlit app layout
st.title('Asset Borrowing and Lending Rates')

user_input = st.text_input('Enter the asset you are looking for:')

if user_input:
    matched_assets = match_assets(user_input)
    if matched_assets:
        st.write('Matching assets:')
        for asset in matched_assets:
            unique_key = f"{asset['pool_name']} - {asset['chain']} - {asset['protocol']} {asset['version']}"
            st.write(f"{asset['pool_name']} ({asset['chain']} - {asset['version']}) - {asset['protocol']}")
            
            if st.button(f"Select {unique_key}"):
                # Dynamically build the keys based on the asset name (e.g., aUSDC, debtUSDC)

                a_token_address = asset[f'a{asset["pool_name"]}']  # e.g., aUSDC
                debt_token_address = asset[f'debt{asset["pool_name"]}']  # e.g., debtUSDC
                chain = asset['chain']
                protocol = asset['protocol']
                version = asset['version']

                # Fetch total supply of "a" and "debt" tokens
                a_token_supply = get_token_total_supply(chain, a_token_address, abi)
                debt_token_supply = get_token_total_supply(chain, debt_token_address, abi)

                # Calculate utilization rate
                utilization_rate = debt_token_supply / a_token_supply  if a_token_supply else 0
                
                # Get the borrowing and lending rates
                borrow_rate, lending_rate = borrowing_and_lending_rate(
                    asset['base_rate'], asset['s1'], asset['s2'], asset['Uopt'], 
                    asset['Rf'], utilization_rate
                )

                borrow_rate = borrow_rate*100
                lending_rate = lending_rate*100
                utilization_rate = utilization_rate*100 

                # Prepare data for treemap
                query_id = asset['dune_a_id']
                results, total_supply = fetch_and_process_data(query_id)
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

                # Plot the treemap with the updated title including protocol and version
                title_text = (f"Top 100 Lending position on {asset['pool_name']} - {protocol} "
                              f"{version} on {chain}<br>"
                              f"Borrow Rate: {borrow_rate:.2f}% | Lending Rate: {lending_rate:.2f}% | "
                              f"Utilization Rate: {utilization_rate:.2f}%")
                
                plot_liquidity_map(holders_data, total_supply, asset, borrow_rate, lending_rate, utilization_rate)
    else:
        st.write('No matching assets found.')