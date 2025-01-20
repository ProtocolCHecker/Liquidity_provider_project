import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from web3 import Web3
import requests
from bs4 import BeautifulSoup
import re



# Replace this URL with the raw URL of your JSON file on GitHub
url = 'https://raw.githubusercontent.com/ProtocolCHecker/Liquidity_provider_project/main/dataset_lending.json'

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    try:
        # Try to parse the JSON data
        assets_data = response.json()
        print("JSON data loaded successfully.")
    except json.JSONDecodeError:
        # If JSON decoding fails, print the response content
        print(f"Failed to decode JSON. Response content: {response.content}")
else:
    # If the request was not successful, print the status code and response content
    print(f"Failed to fetch data. Status code: {response.status_code}, Response content: {response.content}")

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


# Function to plot Sunburst charts with tables
def plot_sunburst_chart(holders_data, total_supply, asset, borrow_rate, lending_rate, utilization_rate, token_type):
    df = pd.DataFrame(holders_data)
    df['percentage_of_supply'] = df['percentage_of_supply'].round(2)
    labels = [f"{holder['address'][:6]}...{holder['address'][-4:]}" if not holder.get('is_contract', False) else "OTHER ACCOUNTS" for holder in holders_data]
    parents = [""] * len(holders_data)
    values = [holder['percentage_of_supply'] for holder in holders_data]
    hover_texts = [f"{holder['address']}<br>Percentage: {holder['percentage_of_supply']:.2f}%" for holder in holders_data]

    ranking_headers = ["Wallet", "Balance", "Percentage (%)"]

    fig = make_subplots(rows=2, cols=1, specs=[[{'type': 'sunburst'}], [{'type': 'table'}]],
                        vertical_spacing=0.1)
    fig.add_trace(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        text=hover_texts,
        textinfo='none',
        hoverinfo='text',
        marker=dict(
            colorscale='RdBu',
            line=dict(width=1, color='white')
        ),
        hovertemplate='%{text}<extra></extra>'
    ), row=1, col=1)
    fig.add_trace(go.Table(
        header=dict(values=ranking_headers),
        cells=dict(values=[[item["address"][:3] + "..." + item["address"][38:40] + item["address"][40:] for item in holders_data],
                           [item["current_balance"] for item in holders_data],
                           [item["percentage_of_supply"] for item in holders_data]])
    ), row=2, col=1)
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25),
        height=800,
        width=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def calculate_cumulative_percentages(holders_data):
    df = pd.DataFrame(holders_data, columns=['address', 'percentage_of_supply'])
    df['cumulative_percentage'] = df['percentage_of_supply'].cumsum()
    top_10 = df.iloc[9]['cumulative_percentage']
    top_25 = df.iloc[24]['cumulative_percentage']
    top_75 = df.iloc[74]['cumulative_percentage']
    top_100 = df.iloc[99]['cumulative_percentage']
    return top_10, top_25, top_75, top_100


def plot_bar_chart(holders_data, top_10, top_25, top_75, top_100, asset):
    df = pd.DataFrame(holders_data, columns=['address', 'percentage_of_supply'])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['address'].apply(lambda x: f"{x[:6]}...{x[-4:]}"),
        y=df['percentage_of_supply'],
        marker=dict(color='#007BFF')
    ))
    fig.update_layout(
        title=f"Top Wallets distribution for {asset}",
        xaxis_title='Wallet Address',
        yaxis_title='% of Token Supply Hold',
        margin=dict(t=50, l=25, r=25, b=25),
        height=600,
        width=800,
        legend=dict(
            #x=0.5,  # Center the legend horizontally
            #y=1.1,   # Position the legend above the plot
            xanchor='center',
            yanchor='top',
            font=dict(size=20),  # Increase the font size of the legend
            orientation="h"
        )
    )
    fig.add_annotation(
          # Position the annotation above the legend
        text=f"Top 10 holds: {top_10:.2f}%<br>Top 25 holds: {top_25:.2f}%<br>Top 75 holds: {top_75:.2f}%<br>Top 100 holds: {top_100:.2f}%",
        showarrow=False,
        font=dict(size=20, color='white'),
        align='center',
        bgcolor='rgba(0,0,0,0.8)',
        bordercolor='#c7c7c7',
        borderwidth=2,
        borderpad=4
    )
    st.plotly_chart(fig, use_container_width=True)


def get_token_holder_chart(chain, contract_address, range_value=100):
    # Define the base URLs for different chains
    base_urls = {
        'Ethereum': 'https://etherscan.io/token/tokenholderchart/',
        'Optimism': 'https://optimistic.etherscan.io/token/tokenholderchart/',
        'Polygon': 'https://polygonscan.com/token/tokenholderchart/',
        'Arbitrum': 'https://arbiscan.io/token/tokenholderchart/',
        'Base': 'https://basescan.org/token/tokenholderchart/'
    }

    # Validate the chain parameter
    if chain not in base_urls:
        raise ValueError(f"Unsupported chain: {chain}")

    # Construct the URL
    url = f"{base_urls[chain]}{contract_address}?range={range_value}"

    # Construct the headers
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-GB,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': url,
        'sec-ch-ua': '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-arch': '"arm"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version-list': '"Brave";v="131.0.0.0", "Chromium";v="131.0.0.0", "Not_A Brand";v="24.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"macOS"',
        'sec-ch-ua-platform-version': '"15.2.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    # Make the request
    response = requests.get(url, headers=headers)

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all script tags
    script_tags = soup.find_all('script')

    if chain == "Polygon" or chain == "Base" or chain == "Arbitrum":
        js_code = script_tags[-1].text

    else:
        js_code = script_tags[-2].text

    # Regular expression pattern to match Ethereum addresses with optional descriptions
    pattern = r"\['(0x[a-fA-F0-9]{40}(?: \([^)]+\))?)'"

    # Find all matches in the JavaScript code
    matches = re.findall(pattern, js_code)

    if len(matches)<100:
        pattern = r"'OTHER ACCOUNTS'"
        new_match  = re.findall(pattern, js_code)
        matches = matches + new_match
        

    # Find the table in the HTML
    table = soup.find('table')

    # Initialize a list to hold the extracted data
    data_list = []

    # Iterate through each row in the table body
    for row in table.tbody.find_all('tr'):

        # Extract relevant columns (adjust index based on your needs)
        balance_holder = row.find_all('td')[2].text.strip()  # Assuming token address is in the third column
        amount_str = row.find_all('td')[3].text.strip()  # Assuming amount is in the fourth column

        # Handle percentage conversion if applicable
        if amount_str.endswith('%'):
            amount = float(amount_str[:-1])  # Remove '%' and convert to float
        else:
            amount = float(amount_str.replace(',', ''))  # Convert to float after removing commas

        data_list.append([matches[table.tbody.find_all('tr').index(row)],balance_holder, amount])

    # Print the retrieved data
    return data_list


# Function to plot the lending and borrowing rate simulator
def plot_rate_simulator(base_rate, slope1, slope2, U_optimal, reserve_factor, current_utilization_rate, current_borrow_rate, current_lending_rate):
    utilization_rates = list(range(0, 101))
    borrow_rates = []
    lending_rates = []

    for utilization_rate in utilization_rates:
        b_rate, l_rate = borrowing_and_lending_rate(base_rate, slope1, slope2, U_optimal, reserve_factor, utilization_rate / 100)
        borrow_rates.append(b_rate * 100)
        lending_rates.append(l_rate * 100)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=utilization_rates,
        y=borrow_rates,
        mode='lines',
        name='Borrow Rate',
        line=dict(color='red')
    ))

    fig.add_trace(go.Scatter(
        x=utilization_rates,
        y=lending_rates,
        mode='lines',
        name='Lending Rate',
        line=dict(color='green')
    ))

    fig.add_trace(go.Scatter(
        x=[current_utilization_rate],
        y=[current_borrow_rate],
        mode='markers',
        name='Current Borrow Rate',
        marker=dict(color='red', size=10)
    ))

    fig.add_trace(go.Scatter(
        x=[current_utilization_rate],
        y=[current_lending_rate],
        mode='markers',
        name='Current Lending Rate',
        marker=dict(color='green', size=10)
    ))

    fig.update_layout(
        title='Lending and Borrowing Rate Simulator',
        xaxis_title='Utilization Rate (%)',
        yaxis_title='Rate (%)',
        margin=dict(t=50, l=25, r=25, b=25),
        height=600,
        width=800,
        legend=dict(
            x=0.5,
            y=1.1,
            xanchor='center',
            yanchor='top',
            orientation="h"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

abi = '''[{"inputs":[{"internalType":"contract IPool","name":"pool","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"BalanceTransfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"underlyingAsset","type":"address"},{"indexed":true,"internalType":"address","name":"pool","type":"address"},{"indexed":false,"internalType":"address","name":"treasury","type":"address"},{"indexed":false,"internalType":"address","name":"incentivesController","type":"address"},{"indexed":false,"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"indexed":false,"internalType":"string","name":"aTokenName","type":"string"},{"indexed":false,"internalType":"string","name":"aTokenSymbol","type":"string"},{"indexed":false,"internalType":"bytes","name":"params","type":"bytes"}],"name":"Initialized","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"onBehalfOf","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"ATOKEN_REVISION","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"EIP712_REVISION","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"POOL","outputs":[{"internalType":"contract IPool","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"RESERVE_TREASURY_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"UNDERLYING_ASSET_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"receiverOfUnderlying","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getIncentivesController","outputs":[{"internalType":"contract IAaveIncentivesController","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getPreviousIndex","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getScaledUserBalanceAndSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"handleRepayment","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IPool","name":"initializingPool","type":"address"},{"internalType":"address","name":"treasury","type":"address"},{"internalType":"address","name":"underlyingAsset","type":"address"},{"internalType":"contract IAaveIncentivesController","name":"incentivesController","type":"address"},{"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"internalType":"string","name":"aTokenName","type":"string"},{"internalType":"string","name":"aTokenSymbol","type":"string"},{"internalType":"bytes","name":"params","type":"bytes"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"caller","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mint","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mintToTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"scaledBalanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"scaledTotalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IAaveIncentivesController","name":"controller","type":"address"}],"name":"setIncentivesController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferOnLiquidation","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"target","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferUnderlyingTo","outputs":[],"stateMutability":"nonpayable","type":"function"}]'''  # Use the full ABI provided

# Streamlit app layout
st.set_page_config(page_title="Asset Borrowing and Lending Rates", layout="wide")



st.markdown("""
    <style>
    body {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stButton > button {
        background-color: #0056b3; /* Dark blue background */
        color: #FFFFFF;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
        position: relative;
        overflow: hidden;
    }
    .stButton > button::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 0;
        height: 100%;
        background: white;
        transition: width 0.3s;
        z-index: -1;
    }
    .stButton > button:hover::after {
        width: 100%;
    }
    .stButton > button:active {
        background-color: #007BFF; /* Lighter blue when active */
    }
    .stProgress > progress {
        width: 100%;
        height: 30px;
        background-color: #333333;
    }
    .stProgress > progress::-webkit-progress-bar {
        background-color: #333333;
    }
    .stProgress > progress::-webkit-progress-value {
        background-color: #007BFF;
    }
    .stProgress > progress::-moz-progress-bar {
        background-color: #007BFF;
    }
    .css-1d391kg {
        padding-top: 2rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 5rem;
    }
    .css-1lcbmhc {
        background-color: #282828;
        border: 1px solid #333333;
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .css-1v3fvcr {
        color: #FFFFFF;
    }
    .css-16idsys {
        color: #AAAAAA;
    }
    .container {
        background-color: #333333;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .container h3 {
        color: #007BFF;
    }
    </style>
""", unsafe_allow_html=True)


st.title('AAVE Pool Scan')

# Sidebar for user input
st.sidebar.header("Asset Selection")
user_input = st.sidebar.text_input('Enter the asset you are looking for:')

if user_input:
    matched_assets = match_assets(user_input)
    if matched_assets:
        st.sidebar.write('Matching assets:')
        for asset in matched_assets:
            unique_key = f"{asset['pool_name']} - {asset['chain']} - {asset['protocol']} {asset['version']}"
            if st.sidebar.button(f"Select {unique_key}"):

                a_token_address = asset[f'a{asset["pool_name"]}']
                debt_token_address = asset[f'debt{asset["pool_name"]}']
                chain = asset['chain']
                protocol = asset['protocol']
                version = asset['version']

                a_token_supply = get_token_total_supply(chain, a_token_address, abi)
                debt_token_supply = get_token_total_supply(chain, debt_token_address, abi)
                utilization_rate = debt_token_supply / a_token_supply if a_token_supply else 0
                utilization_rate_percent = utilization_rate * 100

                borrow_rate, lending_rate = borrowing_and_lending_rate(
                    asset['base_rate'], asset['s1'], asset['s2'], asset['Uopt'],
                    asset['Rf'], utilization_rate
                )
                borrow_rate = borrow_rate * 100
                lending_rate = lending_rate * 100

                #st.markdown(f"<h3 style='text-align: center;'>{asset['pool_name']} - {asset['chain']} - {asset['version']} - {asset['protocol']}</h3>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="background-color: #282828; border: 2px solid #007BFF; border-radius: 10px; padding: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); margin-bottom: 20px;">
                        <h3 style="text-align: center; color: #007BFF; font-size: 36px;">{asset['pool_name']} - {asset['chain']} - {asset['version']} - {asset['protocol']}</h3>
                    </div>
                """, unsafe_allow_html=True)


                # Display the borrow and lending rates
                #st.write(f"### Borrow Rate: {borrow_rate:.2f}% | Lending Rate: {lending_rate:.2f}%")

                st.markdown(f"""
                    <div class='container' style='padding: 10px; margin-bottom: 10px;'>
                        <div style='text-align: center;'>
                            <h3 style='color: white; margin-bottom: 5px;'>Utilization Rate: {utilization_rate_percent:.2f}%</h3>
                        </div>
                        <div style='width: 100%;'>
                            <progress value="{utilization_rate_percent}" max="100" style="width: 100%; height: 30px;"></progress>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                a_results, a_total_supply = get_token_holder_chart(chain, a_token_address), a_token_supply
                debt_results, debt_total_supply = get_token_holder_chart(chain, debt_token_address), debt_token_supply

                a_holders_data = []
                debt_holders_data = []

                for row in a_results[:100]:
                    address = row[0]
                    current_balance = float(row[1].strip("'").replace(",", ""))
                    percentage_of_supply = row[2]
                    a_holders_data.append({
                        'address': address,
                        'current_balance': current_balance,
                        'percentage_of_supply': percentage_of_supply
                    })
                for row in debt_results[:100]:
                    address = row[0]
                    current_balance = float(row[1].strip("'").replace(",", ""))
                    percentage_of_supply = row[2]
                    debt_holders_data.append({
                        'address': address,
                        'current_balance': current_balance,
                        'percentage_of_supply': percentage_of_supply
                    })
                #st.write(f"## {asset['pool_name']} - {asset['chain']} - {asset['protocol']} - {asset['version']}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"""
                        <div class='container' style='padding: 10px; margin-bottom: 10px;'>
                            <h3 style='text-align: center; color: white;'>Lending Pool Distribution - rate : {lending_rate:.2f}%</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    plot_sunburst_chart(a_holders_data, a_total_supply, asset, borrow_rate, lending_rate, utilization_rate, 'lending')

                with col2:
                    st.markdown(f"""
                        <div class='container' style='padding: 10px; margin-bottom: 10px;'>
                            <h3 style='text-align: center; color: white;'>Borrowing Pool Distribution - rate : {borrow_rate:.2f}%</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    plot_sunburst_chart(debt_holders_data, debt_total_supply, asset, borrow_rate, lending_rate, utilization_rate, 'borrowing')
                
                # Calculate cumulative percentages lending
                top_10, top_25, top_75, top_100 = calculate_cumulative_percentages(a_holders_data)

                # Plot the bar chart
                st.write("### Top Wallets by % of Lending Pool Supply")
                name = "a" + asset["pool_name"]
                plot_bar_chart(a_holders_data, top_10, top_25, top_75, top_100, name)

                # Calculate cumulative percentages borrowing
                top_10, top_25, top_75, top_100 = calculate_cumulative_percentages(debt_holders_data)

                # Plot the bar chart
                st.write("### Top Wallets by % of Borrowing Pool Supply")
                name = "debt" + asset["pool_name"]
                plot_bar_chart(debt_holders_data, top_10, top_25, top_75, top_100, name)

                # Add the simulator section
                st.markdown(f"""
                    <div class='container' style='padding: 10px; margin-bottom: 10px;'>
                        <h3 style='text-align: center; color: white;'>Lending and Borrowing Rate Simulator</h3>
                    </div>
                """, unsafe_allow_html=True)

                # Input fields for the user to enter the amount they want to borrow or lend
                amount_to_borrow = st.number_input('Amount to Borrow', min_value=0.0, format="%.2f")
                amount_to_lend = st.number_input('Amount to Lend', min_value=0.0, format="%.2f")

                print(asset)
                requete = asset["request"].strip('"')
                price_asset = requests.get(requete).json()[symbol]['usd']

                debt_token_supply = debt_token_supply * price
                a_token_supply = a_token_supply * price

                # Recalculate the utilization rate based on the user's input
                new_debt_token_supply = debt_token_supply + amount_to_borrow
                new_a_token_supply = a_token_supply + amount_to_lend
                new_utilization_rate = new_debt_token_supply / new_a_token_supply if new_a_token_supply else 0
                new_utilization_rate_percent = new_utilization_rate * 100

                # Calculate the new borrow and lending rates
                new_borrow_rate, new_lending_rate = borrowing_and_lending_rate(
                    asset['base_rate'], asset['s1'], asset['s2'], asset['Uopt'],
                    asset['Rf'], new_utilization_rate
                )
                new_borrow_rate = new_borrow_rate * 100
                new_lending_rate = new_lending_rate * 100

                # Plot the rate simulator
                plot_rate_simulator(
                    asset['base_rate'], asset['s1'], asset['s2'], asset['Uopt'],
                    asset['Rf'], utilization_rate_percent, borrow_rate, lending_rate
                )

                # Display the new rates
                st.markdown(f"""
                    <div class='container' style='padding: 10px; margin-bottom: 10px;'>
                        <h3 style='text-align: center; color: white;'>New Utilization Rate: {new_utilization_rate_percent:.2f}%</h3>
                        <h3 style='text-align: center; color: white;'>New Borrow Rate: {new_borrow_rate:.2f}%</h3>
                        <h3 style='text-align: center; color: white;'>New Lending Rate: {new_lending_rate:.2f}%</h3>
                    </div>
                """, unsafe_allow_html=True)

    else:
        st.sidebar.write('No matching assets found.')
