import ssl
import socket
import json
import hashlib
from bitcoinlib.keys import HDKey
import base58
import os

# Function to compute hash160 (RIPEMD160(SHA256(pubkey))))
def hash160(data):
    sha256_hash = hashlib.sha256(data).digest()
    return hashlib.new('ripemd160', sha256_hash).digest()

# Function to create a legacy P2PKH address
def create_legacy_address(pubkey_hash, network_prefix=b'\x6f'):
    # Add the network prefix (0x00 for mainnet, 0x6f for testnet)
    prefixed_hash = network_prefix + pubkey_hash
    # Compute the checksum (SHA256 twice, take the first 4 bytes)
    checksum = hashlib.sha256(hashlib.sha256(prefixed_hash).digest()).digest()[:4]
    # Append the checksum to the prefixed hash
    binary_address = prefixed_hash + checksum
    # Convert to base58
    return base58.b58encode(binary_address).decode()

# Function to convert a P2PKH address to a script hash (for querying balance)
def p2pkh_address_to_scripthash(address):
    address_bytes = base58.b58decode_check(address)
    # Extract the hash160 (20 bytes, excluding the version byte)
    hash160 = address_bytes[1:]
    # Create the P2PKH script (OP_DUP OP_HASH160 <hash160> OP_EQUALVERIFY OP_CHECKSIG)
    script = b'\x76\xa9\x14' + hash160 + b'\x88\xac'
    # Hash the script (SHA256 and reverse the result)
    scripthash = hashlib.sha256(script).digest()[::-1].hex()
    return scripthash

# Electrum testnet server connection details
electrum_host = "testnet.aranguren.org"
electrum_port = 51002  # Standard SSL port for Electrum testnet

# Establish raw socket connection with SSL, disabling certificate verification
sock = socket.create_connection((electrum_host, electrum_port))
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
ssock = context.wrap_socket(sock, server_hostname=electrum_host)

# Function to send a request to the Electrum server and get the response
def send_request(request):
    ssock.sendall((json.dumps(request) + "\n").encode("utf-8"))
    
    # Receive the response
    response = ssock.recv(4096)
    response_json = json.loads(response.decode('utf-8'))
    
    # Debugging: Print the entire response
    print("Server Response:", response_json)
    
    return response_json

# Generate a random 32-byte private key (for demonstration purposes)
private_key_bytes = bytes.fromhex('2000000000000000000000000000000000000000000000000000000000000000')
# private_key_bytes = bytes.fromhex('64f14a61ddb7a27a2c0bacca858bafd198d1d621c9df28cb0b901f30af267631')

# WIF for p2pkh (legacy)
version_byte = b'\xef'  # 0xef for testnet private key
compressed_flag = b'\x01'  # Always use compressed public keys for Electrum
extended_key = version_byte + private_key_bytes + compressed_flag
checksum = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()[:4]
private_key_wif = base58.b58encode(extended_key + checksum).decode('ascii')

print(f"Private Key (hex): {private_key_bytes.hex()}")
print(f"Private Key in WIF format (importable to Electrum): {private_key_wif}")

# Convert the private key to an HDKey
key = HDKey(import_key=private_key_bytes.hex(), network='testnet')

# Derive the public key and generate the legacy P2PKH address
pubkey = key.public_byte  # Use the raw public key bytes
pubkey_hash = hash160(pubkey)
btc_address = create_legacy_address(pubkey_hash, network_prefix=b'\x6f')  # 0xef for testnet P2PKH
print(f"Bitcoin Testnet Legacy Address (m/n): {btc_address}")

# Convert the Bitcoin legacy address to a script hash
scripthash = p2pkh_address_to_scripthash(btc_address)
print(f"Script Hash: {scripthash}")  # Debugging: Print the script hash

# Prepare and send the balance request
balance_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "blockchain.scripthash.get_balance",
    "params": [scripthash]
}

# Fetch and display the balance
response = send_request(balance_request)

# Check if 'result' exists in the response
if "result" in response:
    balance = response["result"]["confirmed"] / 1e8
    print(f"Testnet Balance: {balance} BTC")
else:
    print("Unexpected response or error:", response)

# Close the socket connection
ssock.close()
