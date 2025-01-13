from web3 import Web3

def check_address_type(address):
    # Connect to Infura using your project ID
    infura_url = 'https://mainnet.infura.io/v3/8c803623898743dc9747fe8e33694d5b'
    w3 = Web3(Web3.HTTPProvider(infura_url))

    # Check if the address is valid
    if not w3.is_address(address):
        return f"{address} is not a valid Ethereum address."

    # Check if the address is an EOA or a smart contract
    code = w3.eth.get_code(address)
    if code == b'':
        return f"{address} is an Externally Owned Account (EOA)."
    else:
        return f"{address} is a smart contract."

# Addresses to check
address = "0x2F64794216CB00837558fc91Efe7E07Cacb8de0A"

# Output results
print(check_address_type(address))
