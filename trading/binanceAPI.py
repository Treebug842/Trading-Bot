#!/bin/env python3
# Written by Treebug842

from binance.client import Client
from binance.enums import *
from datetime import datetime
import time

from . import config

class Binance:
	# Method for writing errors to log
	def __writeError_to_log(self, error, coin, amount):
		with open("transaction_logs.txt", "a") as file:
			if error == "MINAMOUNT_BUY": file.write(f"Unable to buy {amount} {coin}\nAmount too low!")
			elif error == "MINAMOUNT_SELL": file.write(f"Unable to sell {amount} {coin}\nAmount too low!")
			elif error == "INSUFFICIENT_SELL": file.write(f"Unable to sell {amount} {coin}\nInsufficient funds!")
			elif error == "INSUFFICIENT_BUY": file.write(f"Unable to buy {amount} {coin}\nAmount too low!")
			elif error == "OTHER_BUY": file.write(f"Unable to buy {amount} {coin}\nError unknown")
			elif error == "OTHER_SELL": file.write(f"Unable to sell {amount} {coin}\nError unknown")
			elif error == "CONNECT": file.write("Unable to connect to Binance API!")
			file.write("\n\n")

	def __init__(self):
		self.client = Client(config.apiKey, config.apiSecurity) #Connect to API

		# Error handleing for API connection
		try: err = 1 if self.client.get_account_status()['data'] != 'Normal' else 0
		except: err = 1
		if err != 0:
			self.__writeError_to_log("CONNECT", "", 0)
			print("Unable to connect to API!")
			exit(1)

		self.info = self.client.get_account() # Request account info

	# Method for writing transactions to logs
	def __write_to_log(self, data, time):
		with open("transaction_logs.txt", "a") as file:
			file.write(f"Transaction order created {time}\n")
			file.write(f"ServerTime: {self.client.get_server_time()['serverTime']} {data[0]['timeInForce']}\n")
			file.write(f"Currency: {data[0]['symbol']}		Amount: {data[0]['executedQty']}\n")
			file.write(f"OrderID: {data[0]['orderId']}		Status: {data[0]['status']}\n")
			file.write(f"Type: {data[0]['type']}			Buy/Sell: {data[0]['side']}\n")
			file.write("\n\n")

	# Method for returning valid balances
	def __get_balances(self):
		balances = []
		x = self.info['balances']
		for b in x:
			if float(b['free']) > 0:
				balances.append(b)
		return balances

	# Method for converting AUD to coin price
	def __aud_to_coin(self, audAmount, coin):
		symbol = coin + "AUD"
		try: price = self.client.get_avg_price(symbol=symbol)
		except Exception as e:
			if e.message == "Invalid symbol.": print("Invalid Symbol!"); exit(1)
		return ((1 / float(price['price'])) * float(audAmount))

	# Method for converting currencies
	def __convert_coins(self, first, second, amount):
		try: rev_price = self.client.get_avg_price(symbol=(second + first))
		except Exception as e:
			if e.message == "Invalid symbol.": print("Invalid Symbol!"); exit(1)
		price = 1 / float(rev_price['price'])
		converted = price * amount
		return int(converted - 0.5)

	# Method for buying at market price
	def market_buy(self, coin, amount):
		if float(self.client.get_symbol_info(coin)['filters'][2]['minQty']) > float(amount):
			self.__writeError_to_log("MINAMOUNT_BUY", coin, amount)
			print("Minimum tradeable amount not met")
			exit(0)
		co = 0
		try: order = self.client.order_market_buy(symbol=coin, quantity=amount)
		except Exception as e:
			if e.message == "Filter failure: MIN_NOTIONAL": 
				self.__writeError_to_log("INSUFFICIENT_BUY", coin, amount)
				print("Minimum tradeable amount not met")
				exit(0)
			else:
				self.__writeError_to_log("OTHER_BUY", coin, amount)
				print("Order Failed: Errror Code:")
				print(e.message)
				exit(0)
		if order['status'] != "FILLED":
			self.__writeError_to_log("OTHER_BUY", coin, amount)
			print("Order did not go through!")
			exit(0)
		orderId = str(order['orderId']).strip()
		def checkOrder(co):
			_check = "UNABLE TO GET CHECK"
			if co > 10: print("Unable to verify Order!"); return "NULL"
			time.sleep(1)
			try: _check = self.client.get_order(symbol=order['symbol'], orderId=orderId)
			except: co += 1; checkOrder(co)
			return _check
		check = checkOrder(co)
		self.__write_to_log((order, check), datetime.now())
		return (order, check)

	def market_buyAll(self, coin, sellingCoin):
		for bal in self.__get_balances():
			if bal["asset"] == sellingCoin:
				balance = float(bal['free'])
				amount = self.__convert_coins(sellingCoin, (coin.split(sellingCoin)[0]), balance)
		buyAmount = amount
		return self.market_buy(coin, buyAmount)

	# Method for selling at market price
	def market_sell(self, coin, amount):
		if float(self.client.get_symbol_info(coin)['filters'][2]['minQty']) > float(amount):
			self.__writeError_to_log("MINAMOUNT_SELL", coin, amount)
			print("Minimum tradeable amount not met")
			exit(0)
		co = 0
		try: order = self.client.order_market_sell(symbol=coin, quantity=amount)
		except Exception as e:
			if e.message == "Filter failure: MIN_NOTIONAL":
				self.__writeError_to_log("MINAMOUNT_SELL", coin, amount) 
				print("Minimum tradeable amount not met")
				exit(0)
			elif e.message == "Account has insufficient balance for requested action.":
				self.__writeError_to_log("INSUFFICIENT_SELL", coin, amount)
				print("Account has insufficient balance for requested action!")
				exit(0)
			else:
				self.__writeError_to_log("OTHER_SELL", coin, amount)
				print("Order Failed: Errror Code:")
				print(e.message)
				exit(0)
		if order['status'] != "FILLED":
			self.__writeError_to_log("OTHER_SELL", coin, amount)
			print("Order did not go through!")
			exit(0)
		orderId = str(order['orderId']).strip()
		def checkOrder(co):
			_check = "UNABLE TO GET CHECK"
			if co > 10: print("Unable to verify Order!"); return "NULL"
			time.sleep(1)
			try: _check = self.client.get_order(symbol=order['symbol'], orderId=orderId)
			except: co += 1; checkOrder(co)
			return _check
		check = checkOrder(co)
		self.__write_to_log((order, check), datetime.now())
		return (order, check)

	def market_sellAll(self, coin, sellingCoin):
		for bal in self.__get_balances():
			if bal["asset"] == sellingCoin:
				amount = float(bal['free'])
		stepSize = float(self.client.get_symbol_info(coin)['filters'][2]['stepSize'])
		sellAmount = 0
		while (sellAmount < amount):
			sellAmount += stepSize
		sellAmount -= stepSize
		decimalAmount = len(str(amount).split(".")[1])
		sellAmount = round(sellAmount, decimalAmount)
		return self.market_sell(coin, sellAmount)

