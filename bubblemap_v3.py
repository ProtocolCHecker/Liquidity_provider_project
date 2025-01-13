# import os
# import requests
# import json
# from datetime import datetime
# import matplotlib.pyplot as plt
# import matplotlib.patches as patches

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

#     graphql_query = """
#     {
#       EVM(dataset: archive, network: eth) {
#         TokenHolders(
#           date: "2025-05-01"
#           tokenSmartContract: "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f"
#           limit: { count: 100 }
#           orderBy: { descending: Balance_Amount }
#         ) {
#           Holder {
#             Address
#           }
#           Balance {
#             Amount
#           }
#         }
#       }
#     }
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

#         holders_data.append({
#             'address': address,
#             'balance': balance,
#             'percentage': percentage_of_supply
#         })

#         print(f"{address:<42} {balance:<20} {percentage_of_supply:.2f}%")

#     # Save to JSON file with additional metadata
#     with open('token_holders.json', 'w') as json_file:
#         json.dump({"timestamp": datetime.now().isoformat(), "data": holders_data}, json_file)

#     # Create the plot with rectangles
#     plot_liquidity_map(holders_data, total_supply)

#     return holders_data, total_supply


# def plot_liquidity_map(holders_data, total_supply):
#     fig, ax = plt.subplots(figsize=(10, 8))
#     ax.set_aspect('equal')
    
#     # Set the title
#     ax.set_title("Liquidity Providers in the Liquidity Pool", fontsize=16)

#     # Create a large rectangle that will serve as the pool
#     pool_rect = patches.Rectangle((0, 0), 1, 1, linewidth=1, edgecolor='blue', facecolor='lightblue', zorder=0)
#     ax.add_patch(pool_rect)
    
#     # Variables to arrange the rectangles
#     num_providers = len(holders_data)
#     rows = 10  # number of rows
#     cols = (num_providers // rows) + (num_providers % rows)
#     rect_width = 1 / cols
#     rect_height = 1 / rows

#     # Loop over each liquidity provider to draw their rectangle and add the data
#     for i, holder in enumerate(holders_data):
#         row = i // cols
#         col = i % cols
#         rect_x = col * rect_width
#         rect_y = row * rect_height
#         percentage = holder['percentage']
        
#         # Color rectangles in shades of blue based on percentage of liquidity
#         color_intensity = min(0.4 + (percentage / 100), 1.0)  # Make sure color intensity stays within range
#         rect_color = (0.0, 0.0, color_intensity)  # RGB color (blue hues)

#         # Draw the rectangle for each liquidity provider
#         rect = patches.Rectangle(
#             (rect_x, rect_y), rect_width, rect_height,
#             linewidth=0, edgecolor='none', facecolor=rect_color, zorder=1
#         )
#         ax.add_patch(rect)

#         # Annotate with provider's address and percentage
#         ax.text(
#             rect_x + rect_width / 2, rect_y + rect_height / 2,
#             f"{holder['address'][:10]}...{holder['address'][-4:]}: {holder['percentage']:.2f}%",
#             ha="center", va="center", color="white", fontsize=8, zorder=2
#         )

#     # Remove x and y axis ticks and labels
#     ax.set_xticks([])
#     ax.set_yticks([])

#     # Add the table for the liquidity providers on the right
#     table_data = []
#     for holder in holders_data:
#         table_data.append([f"{holder['address'][:10]}...{holder['address'][-4:]}", f"{holder['percentage']:.2f}%"])

#     table = ax.table(cellText=table_data, colLabels=["Address", "% Supply"], loc='center right', cellLoc='center', colLoc='center')
#     table.auto_set_font_size(False)
#     table.set_fontsize(8)
#     table.scale(1, 1.5)

#     plt.show()

# # Call the function to execute the code
# oAuth_example()



import os
import requests
import json
from datetime import datetime
import matplotlib.pyplot as plt
import squarify
import matplotlib.patches as patches

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

    # Create the plot with rectangles
    plot_liquidity_map(holders_data, total_supply)

    return holders_data, total_supply

def plot_liquidity_map(holders_data, total_supply):
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_title("Liquidity Providers in the Liquidity Pool", fontsize=16)

    # Prepare data for squarify
    sizes = [holder['percentage'] for holder in holders_data]
    labels = [f"{holder['address'][:3]}...{holder['address'][-3:]}\n{holder['percentage']:.2f}%" for holder in holders_data]
    colors = [(0.0, 0.6, min(0.8 + (holder['percentage'] / 100), 1.0)) for holder in holders_data]  # Swimming pool blue

    # Create the treemap
    squarify.plot(sizes=sizes, label=labels, alpha=0.8, color=colors, ax=ax)

    # Remove x and y axis ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])

    # Add borders to the rectangles
    for rect in ax.patches:
        rect.set_linewidth(1)
        rect.set_edgecolor('white')

    # Add interactive labels
    annotations = []
    for rect, label in zip(ax.patches, labels):
        annot = ax.annotate(label, xy=(rect.get_x() + rect.get_width() / 2, rect.get_y() + rect.get_height() / 2),
                            xycoords='data', ha='center', va='center', color='white', fontsize=8, visible=False)
        rect.set_picker(True)
        annotations.append(annot)

        def on_pick(event):
            for annot in annotations:
                annot.set_visible(False)
            if event.artist in ax.patches:
                annot.set_visible(True)
                plt.draw()

        fig.canvas.mpl_connect('pick_event', on_pick)

    # Add the table for the top liquidity providers on the right
    # top_holders = sorted(holders_data, key=lambda x: x['percentage'], reverse=True)[:10]
    # table_data = []
    # for holder in top_holders:
    #     table_data.append([f"{holder['address'][:3]}...{holder['address'][-3:]}", f"{holder['percentage']:.2f}%"])

    # table_ax = plt.subplot(121)
    # table_ax.axis('off')
    # table_ax.axis('tight')
    # table = table_ax.table(cellText=table_data, colLabels=["Address", "% Supply"], cellLoc='right', colLoc='right', loc='right')
    # table.auto_set_font_size(False)
    # table.set_fontsize(10)
    # table.scale(1, 1.5)

    plt.show()

# Call the function to execute the code
oAuth_example()
