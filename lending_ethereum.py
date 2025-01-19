# import os
# import requests
# import json
# from datetime import datetime
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# from web3 import Web3

# def check_address_type(address):
#     # Connect to Infura using your project ID
#     infura_url = 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
#     w3 = Web3(Web3.HTTPProvider(infura_url))

#     # Convert address to checksum address
#     checksum_address = w3.to_checksum_address(address)

#     # Check if the address is valid
#     if not w3.is_address(checksum_address):
#         return f"{address} is not a valid Ethereum address."

#     # Check if the address is an EOA or a smart contract
#     code = w3.eth.get_code(checksum_address)
#     if code == b'':
#         return "EOA"
#     else:
#         return "Smart Contract"

# def oAuth_example():
#     # Step 1: Obtain the access token
#     url = "https://oauth2.bitquery.io/oauth2/token"
#     payload = 'grant_type=client_credentials&client_id=2ce4e182-5cc8-4d02-b47d-3f550afa6cdb&client_secret=BMzqn0VSq1Y-rN-33W5lLn1a02&scope=api'
#     headers = {'Content-Type': 'application/x-www-form-urlencoded'}

#     response = requests.post(url, headers=headers, data=payload)
#     resp = json.loads(response.text)

#     if response.status_code != 200:
#         raise Exception(f"OAuth Error: {response.status_code}, {response.text}")

#     access_token = response.json().get('access_token')
#     print("Access Token:", access_token)

#     # Step 2: Make the GraphQL query
#     url_graphql = "https://streaming.bitquery.io/graphql"
#     headers_graphql = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {access_token}'
#     }

#     smart_contract_address = "0x72E95b8931767C79bA4EeE721354d6E99a61D004"


#     graphql_query = f"""
#     {{
#         EVM(dataset: archive, network: eth) {{
#         TokenHolders(
#             date: "2025-05-01"
#             tokenSmartContract: "{smart_contract_address}"
#             limit: {{ count: 1000 }}
#             orderBy: {{ descending: Balance_Amount }}
#         ) {{
#             Holder {{
#             Address
#             }}
#             Balance {{
#             Amount
#             }}
#         }}
#         }}
#     }}
#     """

#     payload_graphql = json.dumps({'query': graphql_query})

#     # Step 3: Send the request to the GraphQL API
#     response_graphql = requests.post(url_graphql, headers=headers_graphql, data=payload_graphql)

#     if response_graphql.status_code != 200:
#         raise Exception(f"GraphQL request failed: {response_graphql.status_code} {response_graphql.text}")

#     data = response_graphql.json()
#     token_holders = data['data']['EVM']['TokenHolders']

#     # Calculate total supply
#     total_supply = sum(float(holder['Balance']['Amount']) for holder in token_holders)

#     holders_data = []

#     print(f"Total Supply: {total_supply}")

#     for holder in token_holders:
#         address = holder['Holder']['Address']
#         balance = float(holder['Balance']['Amount'])
#         percentage_of_supply = (balance / total_supply) * 100 if total_supply > 0 else 0
#         address_type = check_address_type(address)

#         holders_data.append({
#             'address': address,
#             'balance': balance,
#             'percentage': percentage_of_supply,
#             'type': address_type
#         })

#         print(f"{address:<42} {balance:<20} {percentage_of_supply:.2f}% {address_type}")

#     # Save to JSON file with additional metadata
#     with open('token_holders.json', 'w') as json_file:
#         json.dump({"timestamp": datetime.now().isoformat(), "data": holders_data}, json_file)

#     # Create the plot with rectangles
#     plot_liquidity_map(holders_data, total_supply)

#     return holders_data, total_supply


# def plot_liquidity_map(holders_data, total_supply):
#     labels = [f"{holder['address'][:3]}...{holder['address'][-3:]}" for holder in holders_data]
#     parents = [""] * len(holders_data)
#     values = [holder['percentage'] for holder in holders_data]
#     texts = [f"{holder['percentage']:.2f}%" for holder in holders_data]  # Show percentage on the treemap

#     # Create subplots
#     fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'treemap'}, {'type': 'table'}]],
#                         column_widths=[0.7, 0.3])

#     # Add treemap
#     fig.add_trace(go.Treemap(
#         labels=labels,
#         parents=parents,
#         values=values,
#         text=texts,  # Add percentage text on the treemap
#         textposition='middle center',  # Center the text
#         marker=dict(
#             colorscale='Blues',
#             line=dict(width=1, color='white')
#         ),
#         hovertemplate='<b>%{label}</b><br>Percentage: %{value:.2f}%<extra></extra>'
#     ), row=1, col=1)

#     # Add ranking table
#     ranking_data = [
#         [f"#{i+1} - {holder['address'][:3]}...{holder['address'][-3:]}", f"{holder['percentage']:.2f}%", holder['type']]
#         for i, holder in enumerate(holders_data)
#     ]
#     ranking_headers = ["Wallet", "Percentage", "Type"]

#     fig.add_trace(go.Table(
#         header=dict(values=ranking_headers),
#         cells=dict(values=list(zip(*ranking_data)))
#     ), row=1, col=2)

#     # Update layout
#     fig.update_layout(
#         title={
#             'text': 'Top 100 LPs position on USD0-USD0++ on Curve - Ethereum',
#             'x': 0.5,   # Center the title
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': dict(size=18, weight='bold')  # Make the title bold
#         },
#         margin=dict(t=50, l=25, r=25, b=25)
#     )

#     fig.show()

# # Call the function to execute the code
# oAuth_example()



import os
import requests
import json
from datetime import datetime
import plotly.express as px
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

def oAuth_example():
    # Step 1: Obtain the access token
    url = "https://oauth2.bitquery.io/oauth2/token"
    payload = 'grant_type=client_credentials&client_id=2ce4e182-5cc8-4d02-b47d-3f550afa6cdb&client_secret=BMzqn0VSq1Y-rN-33W5lLn1a02&scope=api'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(url, headers=headers, data=payload)
    resp = json.loads(response.text)

    if response.status_code != 200:
        raise Exception(f"OAuth Error: {response.status_code}, {response.text}")

    access_token = response.json().get('access_token')
    print("Access Token:", access_token)

    # Step 2: Make the GraphQL query
    url_graphql = "https://streaming.bitquery.io/graphql"
    headers_graphql = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    smart_contract_address = "0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c"

    graphql_query = f"""
    {{
        EVM(dataset: archive, network: eth) {{
        TokenHolders(
            date: "2025-01-15"
            tokenSmartContract: "{smart_contract_address}"
            limit: {{ count: 10000 }}
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

    print(f"Total Supply: {total_supply}")

    for holder in token_holders[0:100]:
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

        print(f"{address:<42} {balance:<20} {percentage_of_supply:.2f}% {address_type}")

    # Save to JSON file with additional metadata
    with open('token_holders.json', 'w') as json_file:
        json.dump({"timestamp": datetime.now().isoformat(), "data": holders_data}, json_file)

    # Limit to top 100 holders for the treemap
    #top_100_holders = sorted(holders_data, key=lambda x: x['percentage'], reverse=True)[:100]

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
            'text': 'Top 100 LPs position on USD0-USD0++ on Curve - Ethereum',
            'x': 0.5,   # Center the title
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=18, weight='bold')  # Make the title bold
        },
        margin=dict(t=50, l=25, r=25, b=25)
    )

    fig.show()

# Call the function to execute the code
oAuth_example()
