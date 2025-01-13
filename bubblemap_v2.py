# import requests
# import json
# import plotly.graph_objects as go
# from flask import Flask, render_template, jsonify
# from datetime import datetime
# import math
# import random

# app = Flask(__name__)

# def oAuth_example():
#     # Step 1: Obtain the access token
#     url = "https://oauth2.bitquery.io/oauth2/token"
#     payload = 'grant_type=client_credentials&client_id=2ce4e182-5cc8-4d02-b47d-3f550afa6cdb&client_secret=BMzqn0VSq1Y-rN-33W5lLn1a02&scope=api'
#     headers = {'Content-Type': 'application/x-www-form-urlencoded'}

#     response = requests.post(url, headers=headers, data=payload)
#     resp = json.loads(response.text)

#     if response.status_code == 200:
#         access_token = resp['access_token']
#         print("Access Token:", access_token)

#         # Step 2: Make the GraphQL query
#         url_graphql = "https://streaming.bitquery.io/graphql"
#         headers_graphql = {
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {access_token}'
#         }

#         graphql_query = """
#         {
#           EVM(dataset: archive, network: eth) {
#             TokenHolders(
#               date: "2025-05-01"
#               tokenSmartContract: "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f"
#               limit: { count: 100 }
#               orderBy: { descending: Balance_Amount }
#             ) {
#               Holder {
#                 Address
#               }
#               Balance {
#                 Amount
#               }
#             }
#           }
#         }
#         """

#         payload_graphql = json.dumps({'query': graphql_query})

#         # Step 3: Send the request to the GraphQL API
#         response_graphql = requests.post(url_graphql, headers=headers_graphql, data=payload_graphql)

#         # Print the response
#         if response_graphql.status_code == 200:
#             data = response_graphql.json()
#             token_holders = data['data']['EVM']['TokenHolders']

#             # Calculate total supply
#             total_supply = sum(float(holder['Balance']['Amount']) for holder in token_holders)
#             holders_data = []

#             print(f"Total Supply: {total_supply}")
#             print(f"{'Address':<42} {'Balance':<20} {'% of Total Supply':<20}")
#             print("=" * 82)

#             for holder in token_holders:
#                 address = holder['Holder']['Address']
#                 balance = float(holder['Balance']['Amount'])
#                 percentage_of_supply = (balance / total_supply) * 100 if total_supply > 0 else 0

#                 holders_data.append({
#                     'address': address,
#                     'balance': balance,
#                     'percentage': percentage_of_supply
#                 })

#                 print(f"{address:<42} {balance:<20} {percentage_of_supply:.2f}%")

#             # Save to JSON file
#             with open('token_holders.json', 'w') as json_file:
#                 json.dump(holders_data, json_file)

#             print(f"Total Supply: {total_supply}")

#             return holders_data, total_supply
#         else:
#             print(f"GraphQL Error: {response_graphql.status_code}, {response_graphql.text}")
#     else:
#         print(f"OAuth Error: {response.status_code}, {resp}")

#     return [], 0

# @app.route('/')
# def index():
#     token_holders, total_supply = oAuth_example()

#     # If no data found
#     if not token_holders:
#         return render_template('error.html', message="No data found for token holders")

#     # Create figure for the pool area
#     fig = go.Figure()

#     # Create a large rectangle to represent the pool
#     fig.add_shape(
#         type='rect',
#         x0=0, y0=0,
#         x1=1, y1=1,
#         line=dict(color="rgba(0, 0, 255, 0.3)", width=2),
#         fillcolor='rgba(173, 216, 230, 0.5)',  # Light blue for pool
#         layer='below'
#     )

#     # Sort holders by percentage of supply (largest first)
#     token_holders_sorted = sorted(token_holders, key=lambda x: x['percentage'], reverse=True)

#     # Calculate positions and sizes for each rectangle
#     x_pos = 0  # Starting X position for the first rectangle
#     y_pos = 0  # Starting Y position for the first rectangle
#     pool_width = 1  # Full width of the pool (horizontal)
#     pool_height = 1  # Full height of the pool (vertical)
#     margin = 0.02  # Small margin between rectangles
#     remaining_width = pool_width  # Initially, all the width is available for rectangles

#     def place_rectangle(x, y, width, height, holder):
#         address = holder['address']
#         percentage = holder['percentage']
#         balance = holder['balance']

#         # Define the color using a gradient from light to dark blue based on percentage
#         color = f'rgba({173 + int(percentage * 0.4)}, {216 - int(percentage * 0.2)}, {230 - int(percentage * 0.3)}, 0.8)'

#         # Add the rectangle to the figure
#         fig.add_shape(
#             type='rect',
#             x0=x, y0=y,
#             x1=x + width, y1=y + height,
#             line=dict(color=color, width=1),
#             fillcolor=color,
#             opacity=0.8,
#             layer='above'
#         )

#         # Add hover information for the rectangle
#         fig.add_trace(go.Scatter(
#             x=[(x + x + width) / 2],  # Center of the rectangle horizontally
#             y=[y + height / 2],  # Center of the rectangle vertically
#             mode='text',
#             text=[f"{address[:6]}...{address[-4:]}\n{percentage:.2f}%"],
#             showlegend=False,
#             hoverinfo='text',
#             marker=dict(color='white', opacity=0)
#         ))

#     def treemap_layout(holders, x, y, width, height):
#         if not holders:
#             return

#         holder = holders[0]
#         percentage = holder['percentage']
#         balance = holder['balance']

#         # Calculate the width and height of the rectangle based on the holder's percentage of supply
#         rect_width = percentage / 100 * width
#         rect_height = height

#         # Place the rectangle
#         place_rectangle(x, y, rect_width, rect_height, holder)

#         # Recursively place the remaining holders
#         remaining_holders = holders[1:]
#         if remaining_holders:
#             treemap_layout(remaining_holders, x + rect_width, y, width - rect_width, height)

#     # Start the treemap layout from the top-left corner
#     treemap_layout(token_holders_sorted, x_pos, y_pos, pool_width, pool_height)

#     # Set layout options to remove axis and set the title
#     fig.update_layout(
#         title='Liquidity Providers in the Liquidity Pool',
#         title_x=0.5,  # Center the title
#         title_font=dict(size=24, color='black'),
#         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#         showlegend=False,
#         height=800,
#         hovermode='closest',  # Enable hover on rectangles
#         shapes=[dict(
#             type="rect", x0=0, y0=0, x1=1, y1=1,
#             line=dict(color="rgba(0,0,0,0)"), fillcolor="rgba(173, 216, 230, 0.5)"
#         )],
#         annotations=[dict(
#             x=0.5,
#             y=1.05,
#             xref="paper",
#             yref="paper",
#             text="Liquidity Providers",
#             showarrow=False,
#             font=dict(size=16, color="black"),
#             align="center"
#         )]
#     )

#     # Convert the figure to HTML for embedding
#     bubble_map = fig.to_html(full_html=False)

#     # Create a ranking list with addresses and percentages
#     ranking_list = [(f"{holder['address'][:3]}...{holder['address'][-3:]}", round(holder['percentage'],2)) for holder in token_holders_sorted]
#     ranking_list.sort(key=lambda x: x[1], reverse=True)

#     # Get current date
#     current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#     return render_template('index.html', bubble_map=bubble_map, ranking_list=ranking_list, current_date=current_date)

# if __name__ == '__main__':
#     app.run(debug=True)



import os
import requests
import json
import plotly.graph_objects as go
from flask import Flask, render_template, jsonify
from datetime import datetime
import squarify

app = Flask(__name__)

def oAuth_example():
    # Step 1: Obtain the access token securely from environment variables
    url = "https://oauth2.bitquery.io/oauth2/token"
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    if not client_id or not client_secret:
        raise Exception("Client ID or Client Secret is not set in environment variables.")

    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'api'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(url, headers=headers, data=payload)
    
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

    graphql_query = """
    {
      EVM(dataset: archive, network: eth) {
        TokenHolders(
          date: "2025-05-01"
          tokenSmartContract: "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f"
          limit: { count: 100 }
          orderBy: { descending: Balance_Amount }
        ) {
          Holder {
            Address
          }
          Balance {
            Amount
          }
        }
      }
    }
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
    
    for holder in token_holders:
        address = holder['Holder']['Address']
        balance = float(holder['Balance']['Amount'])
        percentage_of_supply = (balance / total_supply) * 100 if total_supply > 0 else 0

        holders_data.append({
            'address': address,
            'balance': balance,
            'percentage': percentage_of_supply
        })

        print(f"{address:<42} {balance:<20} {percentage_of_supply:.2f}%")

    # Save to JSON file with additional metadata
    with open('token_holders.json', 'w') as json_file:
        json.dump({"timestamp": datetime.now().isoformat(), "data": holders_data}, json_file)

    return holders_data, total_supply

@app.route('/')
def index():
    try:
        token_holders, total_supply = oAuth_example()

        # If no data found
        if not token_holders:
            return render_template('error.html', message="No data found for token holders")

        # Create figure for the pool area
        fig = go.Figure()

        # Sort holders by percentage of supply (largest first)
        token_holders_sorted = sorted(token_holders, key=lambda x: x['percentage'], reverse=True)

        # Prepare data for squarify
        sizes = [holder['percentage'] for holder in token_holders_sorted]
        labels = [holder['address'] for holder in token_holders_sorted]

        # Generate treemap layout
        rects = squarify.squarify(sizes, 0, 0, 1, 1)

        # Add rectangles to the figure
        for rect, label in zip(rects, labels):
            x, y, dx, dy = rect['x'], rect['y'], rect['dx'], rect['dy']
            color_value = int(rect["value"] * 255)  # Adjust color value based on size
            color = f'rgba({color_value}, {200 - color_value // 2}, {230 - color_value // 3}, 0.8)'

            fig.add_shape(
                type='rect',
                x0=x, y0=y,
                x1=x + dx, y1=y + dy,
                line=dict(color=color, width=1),
                fillcolor=color,
                opacity=0.8,
                layer='above'
            )

            # Add hover information for the rectangle
            fig.add_trace(go.Scatter(
                x=[(x + x + dx) / 2],  # Center of the rectangle horizontally
                y=[y + dy / 2],  # Center of the rectangle vertically
                mode='text',
                text=[f"{label[:6]}...{label[-4:]}\n{rect['value']:.2f}%"],
                showlegend=False,
                hoverinfo='text',
                marker=dict(color='white', opacity=0)
            ))

        # Set layout options to remove axis and set the title
        fig.update_layout(
            title='Liquidity Providers in the Liquidity Pool',
            title_x=0.5,
            title_font=dict(size=24, color='black'),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            showlegend=False,
            height=800,
            hovermode='closest',
            shapes=[dict(
                type="rect", x0=0, y0=0, x1=1, y1=1,
                line=dict(color="rgba(0,0,0,0)"), fillcolor="rgba(173, 216, 230, 0.5)"
            )],
            annotations=[dict(
                x=0.5,
                y=1.05,
                xref="paper",
                yref="paper",
                text="Liquidity Providers",
                showarrow=False,
                font=dict(size=16, color="black"),
                align="center"
            )]
        )

        # Convert the figure to HTML for embedding
        bubble_map = fig.to_html(full_html=False)

        # Create a ranking list with addresses and percentages
        ranking_list = [(f"{holder['address'][:3]}...{holder['address'][-3:]}", round(holder['percentage'], 2)) for holder in token_holders_sorted]
        
        return render_template('index.html', bubble_map=bubble_map, ranking_list=ranking_list)

    except Exception as e:
        return render_template('error.html', message=str(e))

if __name__ == '__main__':
    app.run(debug=True)
