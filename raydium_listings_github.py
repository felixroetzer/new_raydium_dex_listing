# SOLANA RADYIUM DEX LISTINGS BOT!

# TODO Add Buys, Sells price and liquidity pool tracking management

import asyncio
import sys
import websockets
from websockets.exceptions import ConnectionClosedError
import json
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature
import pandas as pd
from tabulate import tabulate
import time
import threading
import telegram
import queue
from collections import deque
from dexscreener import DexscreenerClient
from dexscreener.models import TokenPair
from helpers import printd
import datetime
import os

wallet_address = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
seen_signatures = set()

solana_client = Client("https://api.mainnet-beta.solana.com")
solana_client_quicknode = Client("YOUR_QUICKNODE_URI")
solana_client_devnet = Client("https://api.devnet.solana.com")
solana_client_testnet = Client("https://api.testnet.solana.com")


class RaydiumListingDataCollector:

    def __init__(self):
        self.solana_client_quicknode = solana_client_quicknode
        self.all_coins_data = {}
        self.dexscreener_client = DexscreenerClient()
        self.seen_signatures = seen_signatures
        self.data_queue = queue.Queue()
        self.new_listings_queue = queue.Queue()
        self.new_listing_raydium_queue = queue.Queue()
        self.new_algo_signal_queue = queue.Queue()
        self.raydiumi_listing_addresses_2h = {}
        self.raydium_listing_addresses_2h = deque(maxlen=2000)
        self.data_frame = {}
        self.sent = False

    async def getTokens(self, str_signature):

        signature = Signature.from_string(str_signature)
        transaction = solana_client_quicknode.get_transaction(signature, encoding="jsonParsed",
                                                              max_supported_transaction_version=0).value
        try:
            instruction_list = transaction.transaction.transaction.message.instructions
            for instructions in instruction_list:
                if instructions.program_id == Pubkey.from_string(wallet_address):
                    print("============NEW POOL DETECTED====================")
                    Token0 = instructions.accounts[8]
                    Token1 = instructions.accounts[9]
                    # Your data
                    data = {'Token_Index': ['Token0', 'Token1'],
                            'Account Public Key': [Token0, Token1]}
                    df = pd.DataFrame(data)
                    table = tabulate(df, headers='keys', tablefmt='fancy_grid')
                    print(table)

                    if str(Token0) == 'So11111111111111111111111111111111111111112':
                        self.new_listings_queue.put(Token1)
                    else:
                        self.new_listings_queue.put(Token0)

        except AttributeError as e:
            print(e)

    async def check_queue(self):

        if self.new_listing_raydium_queue.empty():
            print("NO NEW LISTINGS!")
        else:
            print("NEW LISTING!")
            new_coin = self.new_listing_raydium_queue.get()
            print(f"New Raydium Listing Coin: {new_coin[0]}")
            print(f"Pair Address: {new_coin[1]}")
            print(f"Base Token Address: {new_coin[2]}")
            print(f"URL: {new_coin[3]}")

    async def run(self):
        while True:
            try:
                uri = "wss://api.mainnet-beta.solana.com"
                count = 0
                ### GET YOUR OWN SOLANA MAINNET WEBSOCKET URI FROM QUICKNODE !!!
                quicknode_uri = "###YOURQUICKNODESOLANAMAINNETWEBSOCKETURI###"
                async with websockets.connect(quicknode_uri) as websocket:
                    # Send subscription request
                    await websocket.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "logsSubscribe",
                                                     "params": [{"mentions": [wallet_address]},
                                                                {"commitment": "finalized"}]}))
                    first_resp = await websocket.recv()
                    response_dict = json.loads(first_resp)

                    if 'result' in response_dict:
                        print("Subscription successful. Subscription ID: ", response_dict['result'])

                    async for response in websocket:
                        response_dict = json.loads(response)
                        if count % 200 == 0:
                            await self.check_queue()
                        if count % 800 == 0:
                            print(response_dict)
                        count += 1
                        if response_dict['params']['result']['value']['err'] == None:
                            signature = response_dict['params']['result']['value']['signature']
                            if signature not in self.seen_signatures:
                                self.seen_signatures.add(signature)
                            log_messages_set = set(response_dict['params']['result']['value']['logs'])
                            search = "initialize2"
                            if any(search in message for message in log_messages_set):
                                print(f"True, https://solscan.io/tx/{signature}")
                                await self.getTokens(signature)
                            else:
                                pass

            except websockets.exceptions.ConnectionClosedError:
                print("Connection closed unexpectedly. Reconnecting...")
                continue

            except Exception as e:
                print("An error occurred:", e)
                break

    async def main(self):
        while True:
            await self.run()



