import ssl
import socket
import json
import hashlib
from bitcoinlib.keys import HDKey
import bech32
from bitcoinlib.transactions import Transaction, Output, Input

import sys


class BTCMinimalWallet:

    def __init__(self, private_key_hex, network='testnet', electrum_server='testnet4-electrumx.wakiyamap.dev:51002'):
        self.network = network
        self.key = HDKey(import_key=private_key_hex, network=network)
        self.pubkey = self.key.public_byte
        self.pubkey_hash = self._hash160(self.pubkey)
        self.address = self._create_bech32_address(self.pubkey_hash)
        self.scripthash = self._bech32_address_to_scripthash(self.address)
        # self.electrum_host = "testnet.aranguren.org"
        self.electrum_host = electrum_server.split(":")[0]
        self.electrum_port = int(electrum_server.split(":")[1])
        self.ssock = None


    def _hash160(self, data):
        sha256_hash = hashlib.sha256(data).digest()
        return hashlib.new('ripemd160', sha256_hash).digest()


    def _create_bech32_address(self, pubkey_hash):
        hrp = 'tb'
        converted = bech32.convertbits(pubkey_hash, 8, 5)
        return bech32.bech32_encode(hrp, [0] + converted)


    def _bech32_address_to_scripthash(self, address):
        hrp, data = bech32.bech32_decode(address)
        if hrp not in ('tb', 'bc'):
            raise ValueError('Invalid Bech32 address')
        decoded = bech32.convertbits(data[1:], 5, 8, False)
        script = b'\x00\x14' + bytes(decoded)
        return hashlib.sha256(script).digest()[::-1].hex()


    def connect(self):
        sock = socket.create_connection((self.electrum_host, self.electrum_port))
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.ssock = context.wrap_socket(sock, server_hostname=self.electrum_host)


    def disconnect(self):
        if self.ssock:
            self.ssock.close()
            self.ssock = None


    def _send_request(self, request):
        if not self.ssock:
            raise ConnectionError("Not connected to Electrum server")
        self.ssock.sendall((json.dumps(request) + "\n").encode("utf-8"))
        response = self.ssock.recv(4096)
        return json.loads(response.decode('utf-8'))


    def get_balance(self):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "blockchain.scripthash.get_balance",
            "params": [self.scripthash]
        }
        response = self._send_request(request)
        if "result" in response:
            return response["result"]["confirmed"] / 1e8
        else:
            raise ValueError("Unexpected response or error:", response)


    def get_address(self):
        return self.address


    def get_utxos(self):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "blockchain.scripthash.listunspent",
            "params": [self.scripthash]
        }
        response = self._send_request(request)
        if "result" in response:
            return response["result"]
        else:
            raise ValueError("Unexpected response or error:", response)


    def _create_inputs(self, utxos, target_amount=None):
        inputs = []
        total_input = 0
        for utxo in utxos:
            if target_amount and total_input >= target_amount:
                break
            input_obj = Input(
                prev_txid=utxo['tx_hash'],
                output_n=utxo['tx_pos'],
                value=utxo['value'],
                address=self.address,
                script_type='p2wpkh',
                network=self.network
            )
            inputs.append(input_obj)
            total_input += utxo['value']
        return inputs, total_input


    def _estimate_fee(self, num_inputs, num_outputs, fee_rate_sat_per_byte):
        estimated_size = (num_inputs * 91) + (num_outputs * 31) + 10
        return estimated_size * fee_rate_sat_per_byte


    def _create_and_broadcast_tx(self, inputs, outputs):
        tx = Transaction(inputs=inputs, outputs=outputs, network=self.network, witness_type='segwit')
        tx.sign(self.key)
        raw_tx = tx.raw_hex()
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "blockchain.transaction.broadcast",
            "params": [raw_tx]
        }
        response = self._send_request(request)
        if "result" in response:
            return response["result"]
        else:
            raise ValueError("Unexpected response or error:", response)


    def send_bitcoin(self, to_address, amount_btc, fee_rate_sat_per_byte=10):
        amount_sat = int(amount_btc * 1e8)
        utxos = self.get_utxos()
        
        inputs, total_input = self._create_inputs(utxos, amount_sat)
        
        if total_input < amount_sat:
            raise ValueError("Insufficient funds")
        
        fee = self._estimate_fee(len(inputs), 2, fee_rate_sat_per_byte)
        
        outputs = [Output(amount_sat, to_address, network=self.network)]
        
        change = total_input - amount_sat - fee
        if change > 546:
            outputs.append(Output(change, self.address, network=self.network))
        else:
            fee += change
        
        return self._create_and_broadcast_tx(inputs, outputs)


    def send_all_bitcoin(self, to_address, fee_rate_sat_per_byte=10):
        utxos = self.get_utxos()
        
        if not utxos:
            raise ValueError("No UTXOs available")
        
        inputs, total_input = self._create_inputs(utxos)
        
        fee = self._estimate_fee(len(inputs), 1, fee_rate_sat_per_byte)
        amount_to_send = total_input - fee

        if amount_to_send <= 546:
            raise ValueError("Amount to send is too small (dust)")

        outputs = [Output(amount_to_send, to_address, network=self.network)]
        
        return self._create_and_broadcast_tx(inputs, outputs)







if __name__ == "__main__":
    ######### Configuration ##########
    electrum_server = 'testnet4-electrumx.wakiyamap.dev:51002'
    btc_network = 'testnet'
    private_key_hex = '0000000000000000000000000000000000000000000000000000000000000001'
    ##################################




    ####### Wallet Connection #######
    wallet = BTCMinimalWallet(private_key_hex, network=btc_network, electrum_server=electrum_server)
    wallet.connect()
    #################################




    ########### Commands ############
    if(len(sys.argv) < 2):

        # Wallet Information
        balance = wallet.get_balance()
        utxo_count = len(wallet.get_utxos())
        print(f"############################### WALLET ###############################")
        print(f"[*] Bitcoin Bech32 Address: {wallet.get_address()}")
        print(f"[*] UTXO Count: {utxo_count}")
        print(f"[*] Confirmed Balance: {balance:.8f} BTC")
        print(f"######################################################################\n")
    
        # Usage
        print("Usage: python3 btc.py --send <to_address> <amount>")
        print("       python3 btc.py --send-all <to_address>")
        print("       python3 btc.py --utxos\n")
        sys.exit(1)




    elif(sys.argv[1] == "--send-all"):
        if(len(sys.argv) < 3):
            print("Usage: python3 btc.py --send-all <to_address>\n")
            sys.exit(1)

        to_address = sys.argv[2]
        tx_id = wallet.send_all_bitcoin(to_address)
        print(f"[*] All funds sent! Transaction ID: {tx_id}\n")




    elif(sys.argv[1] == "--send"):
        if(len(sys.argv) < 3):
            print("Usage: python3 btc.py --send <to_address> <amount>\n")
            sys.exit(1)

        to_address = sys.argv[2]
        amount = float(sys.argv[3])
        tx_id = wallet.send_bitcoin(to_address, amount)
        print(f"[*] Transaction sent! Transaction ID: {tx_id}\n")




    elif(sys.argv[1] == "--utxos"):
        utxos = wallet.get_utxos()
        print(json.dumps(utxos, indent=4))
        print("")
    #################################

    wallet.disconnect()

