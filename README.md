# BTC Minimal Wallet

A minimalistic Bitcoin wallet implementation in a single Python file, designed to interact with an [Electrum server](https://electrum.org/#servers) for transaction broadcast and balance retrieval. This wallet supports **Testnet** by default but can be configured for Mainnet with minimal changes.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Check Wallet Info](#check-wallet-info)
  - [Send BTC](#send-btc)
  - [Send All BTC](#send-all-btc)
  - [List UTXOs](#list-utxos)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [License](#license)

---

## Features

- **Single File**: Everything lives in `btc.py`.
- **Bech32 (Native SegWit) Support**: Automatically creates and handles bech32 (`bc1...` / `tb1...`) addresses.
- **Connects to Electrum Server**: Fetches balance, lists unspent outputs (UTXOs), and broadcasts transactions using Electrum JSON-RPC calls.
- **HDKey for Private Key Management**: Leverages [bitcoinlib](https://pypi.org/project/bitcoinlib/) for key handling and signing.
- **Supports Testnet** by default (easy to switch to Mainnet).

---

## Installation

1. **Clone the Repo**:

   ```bash
   git clone https://github.com/tomasvanagas/btc-minimal-wallet.git
   cd btc-minimal-wallet
   ```

2. **Install Dependencies**:

   ```bash
   pip3 install bitcoinlib bech32
   ```

   > _Note_: This wallet also uses Python's standard library modules (`ssl`, `socket`, `json`, `hashlib`, `sys`).  
   > If you face any issues, ensure you have Python 3.7+ installed.

3. **Run the Script**:

   ```bash
   python3 btc.py
   ```

   You will see wallet information if you have the correct configuration, or usage instructions otherwise.

---

## Configuration

Inside `btc.py`, you can edit the following variables in the `__main__` section (end of the file) to suit your needs:

```python
electrum_server = 'testnet4-electrumx.wakiyamap.dev:51002'
btc_network = 'testnet'
private_key_hex = '0000000000000000000000000000000000000000000000000000000000000001'
```

1. **`electrum_server`**: Change this to a reliable Electrum server (host:port).  
2. **`btc_network`**: Switch to `'mainnet'` if you want to interact with the main Bitcoin network.  
3. **`private_key_hex`**: Replace with your own private key in hex format.

> **IMPORTANT**: Protect your private key! Anyone with access to this hex string can spend your BTC.

---

## Usage

All interactions happen through the command line interface of `btc.py`.

### Check Wallet Info

```bash
python3 btc.py
```

This command (with no arguments) displays:

- Your Bitcoin address
- UTXO count
- Confirmed balance  
- Basic usage instructions

### Send BTC

```bash
python3 btc.py --send <to_address> <amount>
```

- `<to_address>`: The recipient’s Bitcoin address (bech32 preferred).  
- `<amount>`: The amount in BTC to send.  
- Example:

  ```bash
  python3 btc.py --send tb1qrecipientaddress 0.0001
  ```
  
  Returns a transaction ID if successful.

### Send All BTC

```bash
python3 btc.py --send-all <to_address>
```

- `<to_address>`: The recipient’s Bitcoin address (bech32 preferred).  
- Sends **all** available BTC in the wallet (minus the miner fee) to the specified address.  
- Example:

  ```bash
  python3 btc.py --send-all tb1qrecipientaddress
  ```

### List UTXOs

```bash
python3 btc.py --utxos
```

Shows all unspent transaction outputs (UTXOs) associated with your wallet’s address in a JSON format.

---

## How It Works

1. **Key & Address**:  
   - Uses `bitcoinlib.keys.HDKey` to handle a private key and derive its public key.  
   - Constructs a Native SegWit (Bech32) address from the public key hash.

2. **Electrum JSON-RPC**:  
   - The wallet opens a secure SSL socket to an Electrum server.  
   - Balance, UTXOs, and transaction broadcasting are managed with JSON-RPC calls.

3. **Transaction Creation & Signing**:  
   - Gathers UTXOs using `blockchain.scripthash.listunspent`.  
   - Uses `bitcoinlib.transactions.Transaction` to build a transaction with specified inputs/outputs.  
   - Signs with the private key.  
   - Broadcasts to the network via `blockchain.transaction.broadcast`.

4. **Fee Calculation**:  
   - Rough fee calculation based on a simple byte-size estimate.  
   - Default rate is 10 sat/byte (adjust as needed).

---

## License

This project is licensed under the [MIT License](LICENSE).  

Feel free to use, modify, and distribute as you see fit.

---

**Disclaimer**: This software is intended for educational and experimental purposes. Always exercise caution and test thoroughly (e.g., on Testnet) before transacting real BTC. 
