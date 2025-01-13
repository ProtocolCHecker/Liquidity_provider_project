# import requests
# import json
# import plotly.graph_objects as go
# from flask import Flask, Response
# from datetime import datetime

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

#     # Create bubble map
#     fig = go.Figure()

#     for holder in token_holders:
#         shortened_address = f"{holder['address'][:3]}...{holder['address'][-3:]}"
#         fig.add_trace(go.Scatter(
#             x=[shortened_address],
#             y=[holder['balance']],
#             mode='markers+text',
#             text=[shortened_address],
#             textposition="top center",
#             marker=dict(size=holder['balance'] * 1e8, color='blue'),  # Adjust size multiplier as needed
#             name=holder['address']
#         ))

#     fig.update_layout(
#         title='Token Holders Bubble Map',
#         xaxis_title='Address',
#         yaxis_title='Balance',
#         showlegend=False
#     )

#     bubble_map = fig.to_html(full_html=True)

#     # Create ranking list
#     ranking_list = [(f"{holder['address'][:3]}...{holder['address'][-3:]}", holder['percentage']) for holder in token_holders]
#     ranking_list.sort(key=lambda x: x[1], reverse=True)

#     # Get current date
#     current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#     # Create HTML content
#     html_content = f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Token Holders</title>
#     </head>
#     <body>
#         <h1>Token Holders Bubble Map</h1>
#         <div>{bubble_map}</div>
#         <h2>Ranking List</h2>
#         <ul>
#     """

#     for address, percentage in ranking_list:
#         html_content += f"<li>{address}: {percentage:.2f}%</li>"

#     html_content += f"""
#         </ul>
#         <p>Current Date: {current_date}</p>
#     </body>
#     </html>
#     """

#     return Response(html_content, mimetype='text/html')

# if __name__ == '__main__':
#     app.run(debug=True)


import requests
import json
import plotly.graph_objects as go
from flask import Flask, Response
from datetime import datetime

app = Flask(__name__)

def oAuth_example():
    # Step 1: Obtain the access token
    url = "https://oauth2.bitquery.io/oauth2/token"
    payload = 'grant_type=client_credentials&client_id=2ce4e182-5cc8-4d02-b47d-3f550afa6cdb&client_secret=BMzqn0VSq1Y-rN-33W5lLn1a02&scope=api'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(url, headers=headers, data=payload)
    resp = json.loads(response.text)

    if response.status_code == 200:
        access_token = resp['access_token']
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

        # Print the response
        if response_graphql.status_code == 200:
            data = response_graphql.json()
            token_holders = data['data']['EVM']['TokenHolders']

            # Calculate total supply
            total_supply = sum(float(holder['Balance']['Amount']) for holder in token_holders)
            holders_data = []

            print(f"Total Supply: {total_supply}")
            print(f"{'Address':<42} {'Balance':<20} {'% of Total Supply':<20}")
            print("=" * 82)

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

            # Save to JSON file
            with open('token_holders.json', 'w') as json_file:
                json.dump(holders_data, json_file)

            print(f"Total Supply: {total_supply}")

            return holders_data, total_supply
        else:
            print(f"GraphQL Error: {response_graphql.status_code}, {response_graphql.text}")
    else:
        print(f"OAuth Error: {response.status_code}, {resp}")

    return [], 0

@app.route('/')
def index():
    token_holders, total_supply = oAuth_example()

    # Create bubble map
    fig = go.Figure()

    for holder in token_holders:
        shortened_address = f"{holder['address'][:6]}...{holder['address'][-4:]}"
        fig.add_trace(go.Scatter(
            x=[shortened_address],
            y=[holder['percentage']],  # Use percentage of total supply
            mode='markers+text',
            text=[f"{shortened_address}: {holder['percentage']:.2f}%"],
            textposition="top center",
            marker=dict(size=holder['percentage'] * 10, color='blue'),  # Adjust size multiplier as needed
            name=holder['address']
        ))

    fig.update_layout(
        title='Token Holders Bubble Map (Percentage of Total Supply)',
        xaxis_title='Address',
        yaxis_title='% of Total Supply',
        showlegend=False,
        yaxis=dict(range=[0, 100])  # Set y-axis range to 0-100%
    )

    bubble_map = fig.to_html(full_html=True)

    # Create ranking list
    ranking_list = [(f"{holder['address'][:6]}...{holder['address'][-4:]}", holder['percentage']) for holder in token_holders]
    ranking_list.sort(key=lambda x: x[1], reverse=True)

    # Get current date
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Token Holders</title>
    </head>
    <body>
        <h1>Token Holders Bubble Map</h1>
        <div>{bubble_map}</div>
        <h2>Ranking List</h2>
        <ul>
    """

    for address, percentage in ranking_list:
        html_content += f"<li>{address}: {percentage:.2f}%</li>"

    html_content += f"""
        </ul>
        <p>Current Date: {current_date}</p>
    </body>
    </html>
    """

    return Response(html_content, mimetype='text/html')

if __name__ == '__main__':
    app.run(debug=True)
