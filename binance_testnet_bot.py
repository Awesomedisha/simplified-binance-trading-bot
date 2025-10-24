import logging
import json
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
import requests
from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BasicBot:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize the trading bot with API credentials.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        try:
            if testnet:
                # CORRECT TESTNET URLs for Binance Futures
                self.client = Client(api_key, api_secret, testnet=True)
                self.client.API_URL = 'https://testnet.binancefuture.com'
                # Additional testnet configuration
                self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
            else:
                self.client = Client(api_key, api_secret)
            
            logger.info(f"Bot initialized successfully. Testnet: {testnet}")
            
            # Verify connection
            self._verify_connection()
        except Exception as e:
            logger.error(f"Error during bot initialization: {e}")
            sys.exit(1)

    def _verify_connection(self):
        """Verify the connection to Binance API."""
        try:
            # Verify futures connection
            server_time = self.client.futures_time()
            logger.info(f"Connection verified. Server time: {server_time.get('serverTime')}")
            
            # Try to get account info to verify API key permissions
            try:
                account = self.client.futures_account()
                logger.info("API key has correct futures permissions")
            except BinanceAPIException as e:
                if e.code == -2015:
                    logger.error("API key doesn't have futures permissions or IP not whitelisted")
                    logger.error("Please create a new API key with 'Enable Futures' checked")
                raise
                
        except BinanceAPIException as e:
            logger.error(f"Error verifying connection: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error verifying connection: {e}")
            raise

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        Place a market order.
        """
        order_details = {"symbol": symbol, "side": side, "quantity": quantity}
        logger.info(f"Placing MARKET order: {order_details}")
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"Successfully placed MARKET order. Response: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Binance API Error placing MARKET order: {e}")
            return {"error": str(e)}
        except BinanceOrderException as e:
            logger.error(f"Binance Order Error placing MARKET order: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error placing MARKET order: {e}")
            return {"error": str(e)}

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """
        Place a limit order.
        """
        order_details = {"symbol": symbol, "side": side, "quantity": quantity, "price": price}
        logger.info(f"Placing LIMIT order: {order_details}")
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',  # Good 'Til Canceled
                quantity=quantity,
                price=price
            )
            logger.info(f"Successfully placed LIMIT order. Response: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Binance API Error placing LIMIT order: {e}")
            return {"error": str(e)}
        except BinanceOrderException as e:
            logger.error(f"Binance Order Error placing LIMIT order: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error placing LIMIT order: {e}")
            return {"error": str(e)}

    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, stop_price: float, limit_price: float) -> Dict:
        """
        Place a stop-limit order.
        """
        order_details = {
            "symbol": symbol, 
            "side": side, 
            "quantity": quantity, 
            "stop_price": stop_price, 
            "limit_price": limit_price
        }
        logger.info(f"Placing STOP_LIMIT order: {order_details}")
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP',
                timeInForce='GTC',
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price
            )
            logger.info(f"Successfully placed STOP_LIMIT order. Response: {order}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Binance API Error placing STOP_LIMIT order: {e}")
            return {"error": str(e)}
        except BinanceOrderException as e:
            logger.error(f"Binance Order Error placing STOP_LIMIT order: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error placing STOP_LIMIT order: {e}")
            return {"error": str(e)}

    def get_order_status(self, symbol: str, order_id: int) -> Dict:
        """
        Get the status of an order.
        """
        logger.info(f"Getting order status for Order ID {order_id} on {symbol}")
        try:
            order_status = self.client.futures_get_order(
                symbol=symbol,
                orderId=order_id
            )
            return order_status
        except BinanceAPIException as e:
            logger.error(f"Binance API Error getting order status: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting order status: {e}")
            return {"error": str(e)}

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        Cancel an order.
        """
        logger.info(f"Cancelling Order ID {order_id} on {symbol}")
        try:
            response = self.client.futures_cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            logger.info(f"Successfully cancelled order. Response: {response}")
            return response
        except BinanceAPIException as e:
            logger.error(f"Binance API Error cancelling order: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error cancelling order: {e}")
            return {"error": str(e)}

    def get_account_balance(self) -> Dict:
        """
        Get the account balance for futures.
        """
        logger.info("Getting account balance...")
        try:
            # Use futures_account_balance()
            balance = self.client.futures_account_balance()
            return balance
        except BinanceAPIException as e:
            logger.error(f"Binance API Error getting account balance: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error getting account balance: {e}")
            return {"error": str(e)}

def print_menu():
    """Prints the main menu for the bot."""
    print("\n" + "="*50)
    print("BINANCE TESTNET TRADING BOT")
    print("="*50)
    print("1. Place Market Order")
    print("2. Place Limit Order")
    print("3. Place Stop-Limit Order")
    print("4. Check Order Status")
    print("5. Cancel Order")
    print("6. Check Account Balance")
    print("7. Exit")
    print("="*50)
    return input("Enter your choice (1-7): ")

def get_user_input(prompt: str, input_type: type = str):
    """
    Get and validate user input.
    """
    while True:
        try:
            user_input = input(prompt)
            return input_type(user_input)
        except ValueError:
            print(f"Invalid input. Please enter a valid {input_type.__name__}.")
        except Exception as e:
            print(f"An error occurred: {e}")

def main():
    """
    Main function to run the bot.
    """
    # --- LOAD CONFIGURATION ---
    # REPLACE WITH YOUR NEW API KEYS
    API_KEY = "AgiQY0lSt4pobLprbc14MfD2xmHZt43NKFTauvNK1JyJkIMsCDyLRO5ExWFYbR88"
    API_SECRET = "07CklPsGufBY9gWNQEiPyFXTQXbyXmowwAEyg8hY96qDKLynRphsGgeMaJEx6ecy"
    
    if "YOUR_NEW_API_KEY_HERE" in API_KEY or "YOUR_NEW_API_SECRET_HERE" in API_SECRET:
        print("="*50)
        print("ERROR: Please update API_KEY and API_SECRET in main()")
        print("\nSTEPS TO FIX:")
        print("1. Go to: https://testnet.binancefuture.com/")
        print("2. Login and go to API Key Management")
        print("3. Generate NEW API Key with 'Enable Futures' CHECKED")
        print("4. If setting IP restrictions, whitelist your current IP")
        print("5. Copy the new keys and paste them in the code")
        print("="*50)
        logger.error("API keys not set. Exiting.")
        sys.exit(1)
        
    try:
        bot = BasicBot(api_key=API_KEY, api_secret=API_SECRET, testnet=True)
    except Exception as e:
        print(f"\n{'='*50}")
        print("Failed to initialize bot. Please check:")
        print("1. API key has 'Enable Futures' permission")
        print("2. Your IP is whitelisted (if you set restrictions)")
        print("3. You're using keys from testnet.binancefuture.com")
        print(f"{'='*50}\n")
        print(f"Error: {e}")
        return

    while True:
        try:
            choice = print_menu()
            
            if choice == '1':
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                side = get_user_input("Enter side (BUY or SELL): ").upper()
                quantity = get_user_input("Enter quantity: ", float)
                result = bot.place_market_order(symbol, side, quantity)
                print(f"\nResult: {json.dumps(result, indent=2)}")

            elif choice == '2':
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                side = get_user_input("Enter side (BUY or SELL): ").upper()
                quantity = get_user_input("Enter quantity: ", float)
                price = get_user_input("Enter limit price: ", float)
                result = bot.place_limit_order(symbol, side, quantity, price)
                print(f"\nResult: {json.dumps(result, indent=2)}")

            elif choice == '3':
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                side = get_user_input("Enter side (BUY or SELL): ").upper()
                quantity = get_user_input("Enter quantity: ", float)
                stop_price = get_user_input("Enter stop price: ", float)
                limit_price = get_user_input("Enter limit price: ", float)
                result = bot.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
                print(f"\nResult: {json.dumps(result, indent=2)}")
                
            elif choice == '4':
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                order_id = get_user_input("Enter order ID: ", int)
                result = bot.get_order_status(symbol, order_id)
                print(f"\nResult: {json.dumps(result, indent=2)}")
                
            elif choice == '5':
                symbol = get_user_input("Enter symbol (e.g., BTCUSDT): ")
                order_id = get_user_input("Enter order ID: ", int)
                result = bot.cancel_order(symbol, order_id)
                print(f"\nResult: {json.dumps(result, indent=2)}")
                
            elif choice == '6':
                balance = bot.get_account_balance()
                print(f"\nAccount Balance: {json.dumps(balance, indent=2)}")
                
            elif choice == '7':
                print("Exiting bot...")
                logger.info("Bot shutdown by user")
                break
            else:
                print("Invalid choice. Please select 1-7")
                
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            logger.warning(f"Unexpected error in main loop: {e}")

if __name__ == "__main__":
    main()