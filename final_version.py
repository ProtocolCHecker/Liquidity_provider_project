import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from web3 import Web3
import requests
from bs4 import BeautifulSoup
import re
import numpy as np



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
    l_rate = b_rate * (1 - reserve_factor) * utilization_rate
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
def plot_rate_simulator(base_rate, slope1, slope2, U_optimal, reserve_factor, current_utilization_rate, current_borrow_rate, current_lending_rate, a_token_supply, debt_token_supply, max_supply, loan_to_value, price, decimal):
    # Initialize session state variables if they don't exist
    # if 'amount_to_borrow' not in st.session_state:
    #     st.session_state.amount_to_borrow = 0
    # if 'amount_to_lend' not in st.session_state:
    #     st.session_state.amount_to_lend = 0

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
        line=dict(color='#0056b3', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=utilization_rates,
        y=lending_rates,
        mode='lines',
        name='Lending Rate',
        line=dict(color='#ADD8E6', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=[current_utilization_rate],
        y=[current_borrow_rate],
        mode='markers',
        name='Current Borrow Rate',
        marker=dict(color='#0056b3', size=14)
    ))

    fig.add_trace(go.Scatter(
        x=[current_utilization_rate],
        y=[current_lending_rate],
        mode='markers',
        name='Current Lending Rate',
        marker=dict(color='#ADD8E6', size=14)
    ))

    # Add a vertical line for the optimal utilization rate
    fig.add_shape(
        type="line",
        x0=U_optimal * 100,
        y0=0,
        x1=U_optimal * 100,
        y1=max(borrow_rates + lending_rates),
        line=dict(color="red", width=2, dash="dash")
    )

    # Add a label for the optimal utilization rate
    fig.add_annotation(
        x=U_optimal * 100,
        y=max(borrow_rates + lending_rates),
        text=f"Optimal Utilization Rate: {U_optimal * 100:.2f}%",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-40,
        font=dict(size=14, color="red")
    )

    fig.update_layout(
        xaxis=dict(
            title='Utilization Rate (%)',
            titlefont=dict(size=18),  # Increased font size for x-axis label
            tickfont=dict(size=14)  # Increased font size for x-axis ticks
        ),
        yaxis=dict(
            title='Rate (%)',
            titlefont=dict(size=18),  # Increased font size for y-axis label
            tickfont=dict(size=14)  # Increased font size for y-axis ticks
        ),
        margin=dict(t=50, l=25, r=25, b=25),
        height=600,
        width=800,
        legend=dict(
            x=0.5,
            y=1.1,
            xanchor='center',
            yanchor='top',
            orientation="h",
            font=dict(size=19)  # Increased font size for legends
        )
    )

    max_supply = int(max_supply * price)
    max_borrow = int(loan_to_value * max_supply)
    # Sliders for the user to enter the amount they want to borrow or lend

    # # Sliders for the user to enter the amount they want to borrow or lend
    # amount_to_lend = st.slider('Amount to Lend (USD)', 0, max_supply)
    # amount_to_borrow = st.slider('Amount to Borrow (USD)', 0, max_borrow, st.session_state.amount_to_borrow)

    
    # #Update session state variables
    # st.session_state.amount_to_lend = amount_to_lend
    # st.session_state.amount_to_borrow = amount_to_borrow
    

    # print(st.session_state.amount_to_lend)

    # Create a form to group the sliders
    with st.form(key='my_form'):
        # Slider for Amount to Lend
        amount_to_lend = st.slider('Amount to Lend (USD)', 0, max_supply)
        print(amount_to_lend)
        # Slider for Amount to Borrow
        amount_to_borrow = st.slider('Amount to Borrow (USD)', 0, max_borrow)
        
        # Submit button for the form
        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        
        print(amount_to_lend)
        # Recalculate the utilization rate based on the user's input
        # new_debt_token_supply = debt_token_supply + st.session_state.amount_to_borrow
        new_debt_token_supply = debt_token_supply + amount_to_borrow * decimal
        new_a_token_supply = a_token_supply + amount_to_lend * decimal
        new_utilization_rate = new_debt_token_supply / new_a_token_supply if new_a_token_supply else 0
        new_utilization_rate_percent = new_utilization_rate * 100

        # Calculate the new borrow and lending rates
        new_borrow_rate, new_lending_rate = borrowing_and_lending_rate(
            base_rate, slope1, slope2, U_optimal, reserve_factor, new_utilization_rate
        )
        new_borrow_rate = new_borrow_rate * 100
        new_lending_rate = new_lending_rate * 100


        # Add markers for the new rates
        fig.add_trace(go.Scatter(
            x=[new_utilization_rate_percent],
            y=[new_borrow_rate],
            mode='markers',
            name='New Borrow Rate',
            marker=dict(color='#FFA500', size=14)  # Orange color for new rates
        ))

        fig.add_trace(go.Scatter(
            x=[new_utilization_rate_percent],
            y=[new_lending_rate],
            mode='markers',
            name='New Lending Rate',
            marker=dict(color='#FFD700', size=14)  # Gold color for new rates
        ))


        st.plotly_chart(fig, use_container_width=True)

def remove_and_replace_extreme_values(rates, method="median"):
    """
    Remove extreme values from a list of rates and replace them with a reasonable value (mean or median).
    :param rates: List of rates (borrowing or lending)
    :param method: The method to use for replacing extreme values ("mean" or "median")
    :return: List of rates with extreme values replaced
    """
    # Calculate the mean and standard deviation of the rates
    mean_rate = np.mean(rates)
    std_dev = np.std(rates)

    # Define the bounds for outliers (3 times the standard deviation)
    lower_bound = mean_rate - 3 * std_dev
    upper_bound = mean_rate + 3 * std_dev

    # Replace outliers with the chosen method (mean or median)
    if method == "median":
        replacement_value = np.median(rates)
    else:
        replacement_value = np.mean(rates)

    # Replace outliers
    cleaned_rates = [
        rate if lower_bound <= rate <= upper_bound else replacement_value
        for rate in rates
    ]
    
    return cleaned_rates

def fetch_data(url):
    response_request_url = requests.get(url)
    if response_request_url.status_code == 200:
        data_url = response_request_url.json()
        dates_url = []
        lending_rates = []
        borrowing_rates = []

        for entry in data_url:
            date_str = f"{entry['x']['year']}-{entry['x']['month'] + 1:02d}-{entry['x']['date']:02d}"
            dates_url.append(date_str)
            lending_rates.append(entry['liquidityRate_avg'] * 100)
            total_borrowing_rate = entry['variableBorrowRate_avg']
            borrowing_rates.append(total_borrowing_rate * 100)

        lending_rates = remove_and_replace_extreme_values(lending_rates, method="mean")
        borrowing_rates = remove_and_replace_extreme_values(borrowing_rates, method="mean")

        dates_url = pd.to_datetime(dates_url)
        return dates_url, lending_rates, borrowing_rates
    else:
        st.error("Failed to fetch data. Please check the URL and try again.")
        return None, None, None

def plot_lending_rate(dates, lending_rates):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=lending_rates,
        mode='lines',
        name='Lending Rate',
        marker=dict(color='#ADD8E6'),
        line=dict(color='#ADD8E6', width=1.5)
    ))
    fig.update_xaxes(title_text="Date", type='date')
    fig.update_yaxes(title_text="Lending Rate (%)")
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25),
        height=500,
        width=800,
        title=""
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_borrowing_rate(dates, borrowing_rates):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=borrowing_rates,
        mode='lines',
        name='Borrowing Rate',
        marker=dict(color='#0056b3'),
        line=dict(color='#0056b3', width=1.5)
    ))
    fig.update_xaxes(title_text="Date", type='date')
    fig.update_yaxes(title_text="Borrowing Rate (%)")
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25),
        height=500,
        width=800,
        title=""
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_utilization_rate(dates, lending_rates, borrowing_rates, res_fact, U_optimal):

    Utilization_rate = [(lending_rates[i] / (borrowing_rates[i] * (1 - res_fact))) * 100 for i in range(len(lending_rates))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=Utilization_rate,
        mode='lines',
        name='Utilization Rate',
        marker=dict(color='#FFFFFF'),
        line=dict(color='#FFFFFF', width=1.5)
    ))

    Uopt = U_optimal * 100
    ymax = np.max(Utilization_rate)

   # Update layout with shapes
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25),  # Padding around the plot
        height=500,  # Height of the plot
        width=800,   # Width of the plot

        title="",
        xaxis=dict(type='date'),  # Ensure x-axis is treated as dates
        shapes = [
        # First shape (below U_optimal)
            dict(
                type='rect',
                x0=0,  # Left side of the chart (0% of x-axis)
                x1=1,  # Right side of the chart (100% of x-axis)
                y0=0,  # Bottom of the chart (0% of y-axis)
                y1=Uopt,  # U_optimal level
                xref="paper",  # Use normalized coordinate for x-axis
                yref="y",  # Use y-axis value for the height
                line=dict(color='rgba(255,255,255,0)'),  # No border
                fillcolor="rgba(173, 216, 230, 0.3)",  # Light blue color with opacity
                layer="below"  # Place below the chart's data
            ),
            # Second shape (above U_optimal)
            dict(
                type='rect',
                x0=0,  # Left side of the chart (0% of x-axis)
                x1=1,  # Right side of the chart (100% of x-axis)
                y0=Uopt,  # Start at U_optimal
                y1=max(ymax,100),  # End at the top of the chart (100%)
                xref="paper",  # Use normalized coordinate for x-axis
                yref="y",  # Use y-axis value for the height
                line=dict(color='rgba(255,255,255,0)'),  # No border
                fillcolor="rgba(0, 86, 179, 0.3)",  # Dark blue color with opacity
                layer="below"  # Place below the chart's data
            )
        ]
    )

    # Add a horizontal line at the U_optimal level
    fig.add_trace(go.Scatter(
        x=dates,
        y=[Uopt] * len(dates),
        mode='lines',
        name=f'U_optimal = {U_optimal * 100}%',  # Add U_optimal value in the legend
        line=dict(color='red', dash='dash', width=2)  # Red dashed line for U_optimal
    ))

    fig.update_xaxes(title_text="Date", type='date')
    fig.update_yaxes(title_text="Utilization Rate (%)")

    st.plotly_chart(fig, use_container_width=True)

def plot_user_account_data(chain, contract_address, abi, user_address):
    infura_urls = {
        'Ethereum': 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Arbitrum': 'https://arbitrum-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Optimism': 'https://optimism-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Base': 'https://base-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b',
        'Polygon': 'https://polygon-mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    }
    infura_url = infura_urls.get(chain, 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b')

    # Initialize Web3 instance and connect to the network
    web3 = Web3(Web3.HTTPProvider(infura_url))

    # Check if connected
    if not web3.is_connected():
        st.error("Failed to connect to the network")
        return
        
    # Convert user address to checksum address
    user_address = web3.to_checksum_address(user_address)

    # Create contract instance
    contract = web3.eth.contract(address=contract_address, abi=abi)

    # Call the getUserAccountData function
    user_data_raw = contract.functions.getUserAccountData(user_address).call()

    # Process user data
    user_data = {
        "totalCollateralBase": user_data_raw[0] / 10**8,
        "totalDebtBase": user_data_raw[1] / 10**8,
        "availableBorrowsBase": user_data_raw[2] / 10**8,
        "currentLiquidationThreshold": user_data_raw[3] / 100,
        "ltv": user_data_raw[4] / 100,
        "healthFactor": round(user_data_raw[5] / 10**18 , 4)
    }

    # Calculate the ratio between totalDebtBase and totalCollateralBase
    debt_ratio = (user_data["totalDebtBase"] / user_data["totalCollateralBase"]) * 100 if user_data["totalCollateralBase"] else 0

    # Create subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'domain'}, {'type': 'table'}]],
                        column_widths=[0.5, 0.5])

    # # Sunburst chart
    # fig.add_trace(go.Sunburst(
    #     labels=["Collateral", "Debt"],
    #     parents=["", "Collateral"],
    #     values=[100 - debt_ratio, debt_ratio],
    #     marker=dict(colors=['#0056b3', '#ADD8E6']),  # Dark blue and light blue
    #     textinfo="label+percent entry"
    # ), row=1, col=1)

    # fig.update_layout(
    #     margin=dict(t=50, l=25, r=25, b=25),
    #     annotations=[
    #         dict(
    #             text="Debt Ratio",
    #             x=0.5,
    #             y=1.1,
    #             font=dict(size=20, color='white'),
    #             showarrow=False
    #         )
    #     ]
    # )

    # Circular loading bar
    fig.add_trace(go.Pie(
        values=[debt_ratio, 100 - debt_ratio],
        labels=["Debt", "Collateral"],
        hole=.7,  # Size of the hole in the center
        marker=dict(colors=['#ADD8E6', '#0056b3'], line=dict(color='#fff', width=2)),  # Light blue and dark blue
        textinfo='label+percent',
        showlegend=False
    ), row=1, col=1)

    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25),
        annotations=[
            dict(
                text=f"{debt_ratio:.2f}%",
                x=0.5,
                y=0.5,
                font=dict(size=20, color='white'),
                showarrow=False
            )
        ]
    )

    # Table
    health_factor = user_data["healthFactor"]
    if health_factor > 10000:
        health_factor_display = "Infinity"
    else:
        health_factor_display = f"{health_factor:.2f}"

    # Table
    table_data = [
        ["Total Collateral Base ($)", f"${user_data['totalCollateralBase']:.2f}"],
        ["Total Debt Base ($)", f"${user_data['totalDebtBase']:.2f}"],
        ["Debt Ratio (%)", f"{debt_ratio:.2f}%"],
        ["Liquidation Threshold (%)", f"{user_data['currentLiquidationThreshold']:.2f}%"],
        ["Health Factor", health_factor_display]
    ]

    fig.add_trace(go.Table(
        header=dict(values=["Metric", "Value"]),
        cells=dict(values=[[row[0] for row in table_data], [row[1] for row in table_data]])
    ), row=1, col=2)

    fig.update_layout(
        title="User Account Data",
        margin=dict(t=50, l=25, r=25, b=25),
        height=600,
        width=1200,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

abi = '''[{"inputs":[{"internalType":"contract IPool","name":"pool","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"BalanceTransfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"target","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"underlyingAsset","type":"address"},{"indexed":true,"internalType":"address","name":"pool","type":"address"},{"indexed":false,"internalType":"address","name":"treasury","type":"address"},{"indexed":false,"internalType":"address","name":"incentivesController","type":"address"},{"indexed":false,"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"indexed":false,"internalType":"string","name":"aTokenName","type":"string"},{"indexed":false,"internalType":"string","name":"aTokenSymbol","type":"string"},{"indexed":false,"internalType":"bytes","name":"params","type":"bytes"}],"name":"Initialized","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"caller","type":"address"},{"indexed":true,"internalType":"address","name":"onBehalfOf","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"balanceIncrease","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"index","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[],"name":"ATOKEN_REVISION","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"EIP712_REVISION","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"PERMIT_TYPEHASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"POOL","outputs":[{"internalType":"contract IPool","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"RESERVE_TREASURY_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"UNDERLYING_ASSET_ADDRESS","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"receiverOfUnderlying","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getIncentivesController","outputs":[{"internalType":"contract IAaveIncentivesController","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getPreviousIndex","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getScaledUserBalanceAndSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"handleRepayment","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"contract IPool","name":"initializingPool","type":"address"},{"internalType":"address","name":"treasury","type":"address"},{"internalType":"address","name":"underlyingAsset","type":"address"},{"internalType":"contract IAaveIncentivesController","name":"incentivesController","type":"address"},{"internalType":"uint8","name":"aTokenDecimals","type":"uint8"},{"internalType":"string","name":"aTokenName","type":"string"},{"internalType":"string","name":"aTokenSymbol","type":"string"},{"internalType":"bytes","name":"params","type":"bytes"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"caller","type":"address"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mint","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"mintToTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"nonces","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"scaledBalanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"scaledTotalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"contract IAaveIncentivesController","name":"controller","type":"address"}],"name":"setIncentivesController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"transferOnLiquidation","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"target","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferUnderlyingTo","outputs":[],"stateMutability":"nonpayable","type":"function"}]'''  # Use the full ABI provided

abi_aave_user = [
                {"inputs":[{"internalType":"contract IPoolAddressesProvider","name":"provider","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":True,"internalType":"address","name":"backer","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"fee","type":"uint256"}],"name":"BackUnbacked","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":False,"internalType":"address","name":"user","type":"address"},{"indexed":True,"internalType":"address","name":"onBehalfOf","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"enum DataTypes.InterestRateMode","name":"interestRateMode","type":"uint8"},{"indexed":False,"internalType":"uint256","name":"borrowRate","type":"uint256"},{"indexed":True,"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"Borrow","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"target","type":"address"},{"indexed":False,"internalType":"address","name":"initiator","type":"address"},{"indexed":True,"internalType":"address","name":"asset","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"enum DataTypes.InterestRateMode","name":"interestRateMode","type":"uint8"},{"indexed":False,"internalType":"uint256","name":"premium","type":"uint256"},{"indexed":True,"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"FlashLoan","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"asset","type":"address"},{"indexed":False,"internalType":"uint256","name":"totalDebt","type":"uint256"}],"name":"IsolationModeTotalDebtUpdated","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"collateralAsset","type":"address"},{"indexed":True,"internalType":"address","name":"debtAsset","type":"address"},{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":False,"internalType":"uint256","name":"debtToCover","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"liquidatedCollateralAmount","type":"uint256"},{"indexed":False,"internalType":"address","name":"liquidator","type":"address"},{"indexed":False,"internalType":"bool","name":"receiveAToken","type":"bool"}],"name":"LiquidationCall","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":False,"internalType":"address","name":"user","type":"address"},{"indexed":True,"internalType":"address","name":"onBehalfOf","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":True,"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"MintUnbacked","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":False,"internalType":"uint256","name":"amountMinted","type":"uint256"}],"name":"MintedToTreasury","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":True,"internalType":"address","name":"repayer","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":False,"internalType":"bool","name":"useATokens","type":"bool"}],"name":"Repay","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":False,"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"indexed":False,"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"}],"name":"ReserveDataUpdated","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":True,"internalType":"address","name":"user","type":"address"}],"name":"ReserveUsedAsCollateralDisabled","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":True,"internalType":"address","name":"user","type":"address"}],"name":"ReserveUsedAsCollateralEnabled","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":False,"internalType":"address","name":"user","type":"address"},{"indexed":True,"internalType":"address","name":"onBehalfOf","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"},{"indexed":True,"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"Supply","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":False,"internalType":"uint8","name":"categoryId","type":"uint8"}],"name":"UserEModeSet","type":"event"},
                {"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"reserve","type":"address"},{"indexed":True,"internalType":"address","name":"user","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"Withdraw","type":"event"},
                {"inputs":[],"name":"ADDRESSES_PROVIDER","outputs":[{"internalType":"contract IPoolAddressesProvider","name":"","type":"address"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"BRIDGE_PROTOCOL_FEE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"FLASHLOAN_PREMIUM_TOTAL","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"FLASHLOAN_PREMIUM_TO_PROTOCOL","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"MAX_NUMBER_RESERVES","outputs":[{"internalType":"uint16","name":"","type":"uint16"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"POOL_REVISION","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"fee","type":"uint256"}],"name":"backUnbacked","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"interestRateMode","type":"uint256"},{"internalType":"uint16","name":"referralCode","type":"uint16"},{"internalType":"address","name":"onBehalfOf","type":"address"}],"name":"borrow","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"}],"name":"borrow","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"},{"components":[{"internalType":"uint16","name":"ltv","type":"uint16"},{"internalType":"uint16","name":"liquidationThreshold","type":"uint16"},{"internalType":"uint16","name":"liquidationBonus","type":"uint16"},{"internalType":"string","name":"label","type":"string"}],"internalType":"struct DataTypes.EModeCategoryBaseConfiguration","name":"category","type":"tuple"}],"name":"configureEModeCategory","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"},{"internalType":"uint128","name":"borrowableBitmap","type":"uint128"}],"name":"configureEModeCategoryBorrowableBitmap","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"},{"internalType":"uint128","name":"collateralBitmap","type":"uint128"}],"name":"configureEModeCategoryCollateralBitmap","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"deposit","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"dropReserve","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"balanceFromBefore","type":"uint256"},{"internalType":"uint256","name":"balanceToBefore","type":"uint256"}],"name":"finalizeTransfer","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"receiverAddress","type":"address"},{"internalType":"address[]","name":"assets","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"},{"internalType":"uint256[]","name":"interestRateModes","type":"uint256[]"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"bytes","name":"params","type":"bytes"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"flashLoan","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"receiverAddress","type":"address"},{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes","name":"params","type":"bytes"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"flashLoanSimple","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[],"name":"getBorrowLogic","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
                {"inputs":[],"name":"getBridgeLogic","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getConfiguration","outputs":[{"components":[{"internalType":"uint256","name":"data","type":"uint256"}],"internalType":"struct DataTypes.ReserveConfigurationMap","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryBorrowableBitmap","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryCollateralBitmap","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryCollateralConfig","outputs":[{"components":[{"internalType":"uint16","name":"ltv","type":"uint16"},{"internalType":"uint16","name":"liquidationThreshold","type":"uint16"},{"internalType":"uint16","name":"liquidationBonus","type":"uint16"}],"internalType":"struct DataTypes.CollateralConfig","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryData","outputs":[{"components":[{"internalType":"uint16","name":"ltv","type":"uint16"},{"internalType":"uint16","name":"liquidationThreshold","type":"uint16"},{"internalType":"uint16","name":"liquidationBonus","type":"uint16"},{"internalType":"address","name":"priceSource","type":"address"},{"internalType":"string","name":"label","type":"string"}],"internalType":"struct DataTypes.EModeCategoryLegacy","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryLabel","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"getEModeLogic","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
                {"inputs":[],"name":"getFlashLoanLogic","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getLiquidationGracePeriod","outputs":[{"internalType":"uint40","name":"","type":"uint40"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[],"name":"getLiquidationLogic","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
                {"inputs":[],"name":"getPoolLogic","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
                {"inputs":[{"internalType":"uint16","name":"id","type":"uint16"}],"name":"getReserveAddressById","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"components":[{"internalType":"uint256","name":"data","type":"uint256"}],"internalType":"struct DataTypes.ReserveConfigurationMap","name":"configuration","type":"tuple"},{"internalType":"uint128","name":"liquidityIndex","type":"uint128"},{"internalType":"uint128","name":"currentLiquidityRate","type":"uint128"},{"internalType":"uint128","name":"variableBorrowIndex","type":"uint128"},{"internalType":"uint128","name":"currentVariableBorrowRate","type":"uint128"},{"internalType":"uint128","name":"currentStableBorrowRate","type":"uint128"},{"internalType":"uint40","name":"lastUpdateTimestamp","type":"uint40"},{"internalType":"uint16","name":"id","type":"uint16"},{"internalType":"address","name":"aTokenAddress","type":"address"},{"internalType":"address","name":"stableDebtTokenAddress","type":"address"},{"internalType":"address","name":"variableDebtTokenAddress","type":"address"},{"internalType":"address","name":"interestRateStrategyAddress","type":"address"},{"internalType":"uint128","name":"accruedToTreasury","type":"uint128"},{"internalType":"uint128","name":"unbacked","type":"uint128"},{"internalType":"uint128","name":"isolationModeTotalDebt","type":"uint128"}],"internalType":"struct DataTypes.ReserveDataLegacy","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveDataExtended","outputs":[{"components":[{"components":[{"internalType":"uint256","name":"data","type":"uint256"}],"internalType":"struct DataTypes.ReserveConfigurationMap","name":"configuration","type":"tuple"},{"internalType":"uint128","name":"liquidityIndex","type":"uint128"},{"internalType":"uint128","name":"currentLiquidityRate","type":"uint128"},{"internalType":"uint128","name":"variableBorrowIndex","type":"uint128"},{"internalType":"uint128","name":"currentVariableBorrowRate","type":"uint128"},{"internalType":"uint128","name":"__deprecatedStableBorrowRate","type":"uint128"},{"internalType":"uint40","name":"lastUpdateTimestamp","type":"uint40"},{"internalType":"uint16","name":"id","type":"uint16"},{"internalType":"uint40","name":"liquidationGracePeriodUntil","type":"uint40"},{"internalType":"address","name":"aTokenAddress","type":"address"},{"internalType":"address","name":"__deprecatedStableDebtTokenAddress","type":"address"},{"internalType":"address","name":"variableDebtTokenAddress","type":"address"},{"internalType":"address","name":"interestRateStrategyAddress","type":"address"},{"internalType":"uint128","name":"accruedToTreasury","type":"uint128"},{"internalType":"uint128","name":"unbacked","type":"uint128"},{"internalType":"uint128","name":"isolationModeTotalDebt","type":"uint128"},{"internalType":"uint128","name":"virtualUnderlyingBalance","type":"uint128"}],"internalType":"struct DataTypes.ReserveData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveNormalizedIncome","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveNormalizedVariableDebt","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"getReservesCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"getReservesList","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"getSupplyLogic","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"pure","type":"function"},
                {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserAccountData","outputs":[{"internalType":"uint256","name":"totalCollateralBase","type":"uint256"},{"internalType":"uint256","name":"totalDebtBase","type":"uint256"},{"internalType":"uint256","name":"availableBorrowsBase","type":"uint256"},{"internalType":"uint256","name":"currentLiquidationThreshold","type":"uint256"},{"internalType":"uint256","name":"ltv","type":"uint256"},{"internalType":"uint256","name":"healthFactor","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserConfiguration","outputs":[{"components":[{"internalType":"uint256","name":"data","type":"uint256"}],"internalType":"struct DataTypes.UserConfigurationMap","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserEMode","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getVirtualUnderlyingBalance","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"address","name":"aTokenAddress","type":"address"},{"internalType":"address","name":"variableDebtAddress","type":"address"},{"internalType":"address","name":"interestRateStrategyAddress","type":"address"}],"name":"initReserve","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"contract IPoolAddressesProvider","name":"provider","type":"address"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"collateralAsset","type":"address"},{"internalType":"address","name":"debtAsset","type":"address"},{"internalType":"address","name":"user","type":"address"},{"internalType":"uint256","name":"debtToCover","type":"uint256"},{"internalType":"bool","name":"receiveAToken","type":"bool"}],"name":"liquidationCall","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args1","type":"bytes32"},{"internalType":"bytes32","name":"args2","type":"bytes32"}],"name":"liquidationCall","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address[]","name":"assets","type":"address[]"}],"name":"mintToTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"mintUnbacked","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"}],"name":"repay","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"interestRateMode","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"}],"name":"repay","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"interestRateMode","type":"uint256"}],"name":"repayWithATokens","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"}],"name":"repayWithATokens","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"repayWithPermit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"interestRateMode","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"permitV","type":"uint8"},{"internalType":"bytes32","name":"permitR","type":"bytes32"},{"internalType":"bytes32","name":"permitS","type":"bytes32"}],"name":"repayWithPermit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"rescueTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"resetIsolationModeTotalDebt","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"components":[{"internalType":"uint256","name":"data","type":"uint256"}],"internalType":"struct DataTypes.ReserveConfigurationMap","name":"configuration","type":"tuple"}],"name":"setConfiguration","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint40","name":"until","type":"uint40"}],"name":"setLiquidationGracePeriod","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"address","name":"rateStrategyAddress","type":"address"}],"name":"setReserveInterestRateStrategyAddress","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"uint8","name":"categoryId","type":"uint8"}],"name":"setUserEMode","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"}],"name":"setUserUseReserveAsCollateral","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"bool","name":"useAsCollateral","type":"bool"}],"name":"setUserUseReserveAsCollateral","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint16","name":"referralCode","type":"uint16"}],"name":"supply","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"}],"name":"supply","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"onBehalfOf","type":"address"},{"internalType":"uint16","name":"referralCode","type":"uint16"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"permitV","type":"uint8"},{"internalType":"bytes32","name":"permitR","type":"bytes32"},{"internalType":"bytes32","name":"permitS","type":"bytes32"}],"name":"supplyWithPermit","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"supplyWithPermit","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"syncIndexesState","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"syncRatesState","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"uint256","name":"protocolFee","type":"uint256"}],"name":"updateBridgeProtocolFee","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"uint128","name":"flashLoanPremiumTotal","type":"uint128"},{"internalType":"uint128","name":"flashLoanPremiumToProtocol","type":"uint128"}],"name":"updateFlashloanPremiums","outputs":[],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"address","name":"asset","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"to","type":"address"}],"name":"withdraw","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"args","type":"bytes32"}],"name":"withdraw","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}
            ]

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
                st.session_state.selected_asset = asset

if 'selected_asset' in st.session_state:
    asset = st.session_state.selected_asset
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

    st.markdown(f"""
        <div style="background-color: #282828; border: 2px solid #007BFF; border-radius: 10px; padding: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); margin-bottom: 20px;">
            <h3 style="text-align: center; color: #007BFF; font-size: 36px;">{asset['pool_name']} - {asset['chain']} - {asset['version']} - {asset['protocol']}</h3>
        </div>
    """, unsafe_allow_html=True)

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

    top_10, top_25, top_75, top_100 = calculate_cumulative_percentages(a_holders_data)

    st.write("### Top Wallets by % of Lending Pool Supply")
    name = "a" + asset["pool_name"]
    plot_bar_chart(a_holders_data, top_10, top_25, top_75, top_100, name)

    top_10, top_25, top_75, top_100 = calculate_cumulative_percentages(debt_holders_data)

    st.write("### Top Wallets by % of Borrowing Pool Supply")
    name = "debt" + asset["pool_name"]
    plot_bar_chart(debt_holders_data, top_10, top_25, top_75, top_100, name)

    # Plot interest rates over time 
    request_url = asset["url"]
    reserve_factor = asset["Rf"]
    optimal_utilization = asset["Uopt"]
    
    date, lend_rate, borrow_rate = fetch_data(request_url)

    st.write("### Utilization rate in % over time")
    plot_utilization_rate(date, lend_rate, borrow_rate, reserve_factor, optimal_utilization)

    st.write("### Lending rate in % over time")
    plot_lending_rate(date, lend_rate)

    st.write("### Borrowing rate in % over time")
    plot_borrowing_rate(date, borrow_rate)

    st.write("### Situation of the top #1 wallet of this pool")
    blockchain = asset["chain"]
    sc_abi = asset["aave_smart_contract"]
    user = a_results[0][0][:42]
    plot_user_account_data(blockchain, sc_abi, abi_aave_user, user)

    # symbol = asset["symbol"]
    # price_asset = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd').json()[symbol]['usd']

    # debt_token_supply = debt_token_supply * price_asset
    # a_token_supply = a_token_supply * price_asset

    # LTV = asset["LTV"] * 100

    # st.markdown(f"""
    #     <div class='container' style='padding: 10px; margin-bottom: 10px;'>
    #         <h3 style='text-align: center; color: white;'>Lending and Borrowing Rate Simulator - LTV = {LTV:.2f} %</h3>
    #     </div>
    # """, unsafe_allow_html=True)

    # # Call the plot_rate_simulator function with the necessary parameters

    # maximum_supply = asset["max_supply"] - a_token_supply / (price_asset * asset["coef"])
    # LTV = LTV / 100
    # coef = asset["coef"]

    # plot_rate_simulator(
    #     asset['base_rate'], asset['s1'], asset['s2'], asset['Uopt'],
    #     asset['Rf'], utilization_rate_percent, borrow_rate, lending_rate,
    #     a_token_supply, debt_token_supply, maximum_supply, LTV, price_asset, coef
    # )

else:
    st.sidebar.write('')