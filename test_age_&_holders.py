import requests
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

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

    # Step 2: Loop through each day of the previous 30 days
    current_date = datetime.now()
    start_date = current_date - timedelta(days=30)
    end_date = current_date

    supply_data = {}
    top_10_addresses = []  # To store the top 10 holders' addresses from the first day

    while start_date <= end_date:
        date_str = start_date.strftime("%Y-%m-%d")

        url_graphql = "https://streaming.bitquery.io/graphql"
        headers_graphql = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        smart_contract_address = "0x1d08E7adC263CfC70b1BaBe6dC5Bb339c16Eec52"
        #smart_contract_address = "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f"

        graphql_query = f"""
        {{
          EVM(dataset: archive, network: eth) {{
            TokenHolders(
              date: "{date_str}"
              tokenSmartContract: "{smart_contract_address}"
              limit: {{ count: 20 }}
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

        response_graphql = requests.post(url_graphql, headers=headers_graphql, json={'query': graphql_query})

        if response_graphql.status_code == 200:
            try:
                response_data = response_graphql.json()
                if isinstance(response_data, dict):
                    if 'errors' in response_data:
                        print(f"{date_str}: Query failed - {response_data['errors']}")
                    else:
                        holders_info = response_data['data']['EVM']['TokenHolders']
                        total_supply = sum(float(holder['Balance']['Amount']) for holder in holders_info)

                        # Calculate percentage of supply for each holder
                        percentages = {}
                        for holder in holders_info:
                            address = holder['Holder']['Address']
                            amount = float(holder['Balance']['Amount'])
                            percentage = (amount / total_supply) * 100 if total_supply > 0 else 0
                            percentages[address] = percentage

                        # If it's the first day, capture the top 10 addresses
                        if start_date == current_date - timedelta(days=30):
                            sorted_holders = sorted(percentages.items(), key=lambda x: x[1], reverse=True)[:10]
                            top_10_addresses = [address for address, _ in sorted_holders]

                        # Track the evolution of the top 10 holders' percentages over time
                        supply_data[date_str] = {}
                        for address in top_10_addresses:
                            if address in percentages:
                                supply_data[date_str][address] = percentages[address]
                            else:
                                supply_data[date_str][address] = 0

            except json.JSONDecodeError:
                print(f"{date_str}: Response is not valid JSON")
        else:
            print(f"{date_str}: HTTP Error - {response_graphql.status_code}")

        # Move to the next day
        start_date += timedelta(days=1)

    return supply_data, top_10_addresses

def plot_top_holders(supply_data, top_10_addresses):
    # Prepare data for plotting
    for address in top_10_addresses:
        dates = []
        values = []

        for date, holders in sorted(supply_data.items()):
            if address in holders:
                dates.append(date)
                values.append(holders[address])
            else:
                # If the holder wasn't in the top 10 that day, add 0% for that day
                dates.append(date)
                values.append(0)

        # Format the address in the legend to show only the first 3 and last 3 characters
        legend_label = f"{address[:3]}...{address[-3:]}"
        plt.plot(dates, values, label=legend_label, marker='o')

    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Percentage of Supply (%)")
    plt.title("Historical Variation of % Supply Held by each Top 10 Holders")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), title="Top 10 Holders")
    plt.tight_layout()
    plt.show()

# Execute the function and plot results
supply_data, top_10_addresses = oAuth_example()
plot_top_holders(supply_data, top_10_addresses)


# import requests
# import json
# from datetime import datetime, timedelta
# import matplotlib.pyplot as plt
# import os
# import streamlit as st
# from PIL import Image

# def get_supply_data(smart_contract_address):
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

#     # Step 2: Loop through each day of the previous 30 days
#     current_date = datetime.now()
#     start_date = current_date - timedelta(days=30)
#     end_date = current_date

#     supply_data = {}
#     top_10_addresses = []  # To store the top 10 holders' addresses from the first day

#     while start_date <= end_date:
#         date_str = start_date.strftime("%Y-%m-%d")

#         url_graphql = "https://streaming.bitquery.io/graphql"
#         headers_graphql = {
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {access_token}'
#         }

#         graphql_query = f"""
#         {{
#           EVM(dataset: archive, network: eth) {{
#             TokenHolders(
#               date: "{date_str}"
#               tokenSmartContract: "{smart_contract_address}"
#               limit: {{ count: 20 }}
#               orderBy: {{ descending: Balance_Amount }}
#             ) {{
#               Holder {{
#                 Address
#               }}
#               Balance {{
#                 Amount
#               }}
#             }}
#           }}
#         }}
#         """

#         response_graphql = requests.post(url_graphql, headers=headers_graphql, json={'query': graphql_query})

#         if response_graphql.status_code == 200:
#             try:
#                 response_data = response_graphql.json()
#                 if isinstance(response_data, dict):
#                     if 'errors' in response_data:
#                         print(f"{date_str}: Query failed - {response_data['errors']}")
#                     else:
#                         holders_info = response_data['data']['EVM']['TokenHolders']
#                         total_supply = sum(float(holder['Balance']['Amount']) for holder in holders_info)

#                         # Calculate percentage of supply for each holder
#                         percentages = {}
#                         for holder in holders_info:
#                             address = holder['Holder']['Address']
#                             amount = float(holder['Balance']['Amount'])
#                             percentage = (amount / total_supply) * 100 if total_supply > 0 else 0
#                             percentages[address] = percentage

#                         # If it's the first day, capture the top 10 addresses
#                         if start_date == current_date - timedelta(days=30):
#                             sorted_holders = sorted(percentages.items(), key=lambda x: x[1], reverse=True)[:10]
#                             top_10_addresses = [address for address, _ in sorted_holders]

#                         # Track the evolution of the top 10 holders' percentages over time
#                         supply_data[date_str] = {}
#                         for address in top_10_addresses:
#                             if address in percentages:
#                                 supply_data[date_str][address] = percentages[address]
#                             else:
#                                 supply_data[date_str][address] = 0

#             except json.JSONDecodeError:
#                 print(f"{date_str}: Response is not valid JSON")
#         else:
#             print(f"{date_str}: HTTP Error - {response_graphql.status_code}")

#         # Move to the next day
#         start_date += timedelta(days=1)

#     return supply_data, top_10_addresses

# def plot_top_holders(supply_data, top_10_addresses, plot_file_path):
#     # Prepare data for plotting
#     for address in top_10_addresses:
#         dates = []
#         values = []

#         for date, holders in sorted(supply_data.items()):
#             if address in holders:
#                 dates.append(date)
#                 values.append(holders[address])
#             else:
#                 # If the holder wasn't in the top 10 that day, add 0% for that day
#                 dates.append(date)
#                 values.append(0)

#         # Format the address in the legend to show only the first 3 and last 3 characters
#         legend_label = f"{address[:3]}...{address[-3:]}"
#         plt.plot(dates, values, label=legend_label, marker='o')

#     plt.xticks(rotation=45)
#     plt.xlabel("Date")
#     plt.ylabel("Percentage of Supply (%)")
#     plt.title("Historical Variation of % Supply Held by each Top 10 Holders")
#     plt.legend(loc='upper left', bbox_to_anchor=(1, 1), title="Top 10 Holders")
#     plt.tight_layout()

#     # Save the plot to the specified file path
#     plt.savefig(plot_file_path)
#     plt.close()  # Close the plot to free memory

# def main(pool_address):
#     plot_file_path = "/Users/barguesflorian/Documents/LP_project/holders_plot.png"  # Specify your desired path here
#     supply_data, top_10_addresses = get_supply_data(pool_address)
#     plot_top_holders(supply_data, top_10_addresses, plot_file_path)
#     return supply_data, plot_file_path


# # Streamlit Interface
# st.title("Token Holders Analysis")

# # Input field for pool address
# pool_address = st.text_input("Enter the Pool Address:")

# if pool_address:
#     st.write(f"Fetching data for pool address: {pool_address}")
#     supply_data, plot_file_path = main(pool_address)
    
#     # Display the data
#     st.write("Supply data (Top 10 holders over the past 30 days):")
#     st.json(supply_data)
    
#     # Display the generated plot
#     img = Image.open(plot_file_path)
#     st.image(img, caption="Top 10 Holders Over Time")
