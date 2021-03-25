
import json
from enum import IntEnum

class XTBPositionType(IntEnum):
	
	POSITION_LONG = 0
	POSITION_SHORT = 1

class XTBTradeType(IntEnum):
	
	BUY_MARKET = 0
	SELL_MARKET = 1
	BUY_LIMIT = 2
	SELL_LIMIT = 3
	BUY_STOP = 4
	SELL_STOP = 5

class XTBTradeExecutionType(IntEnum):
	
	TRADE_OPEN = 0
	TRADE_PENDING = 1
	TRADE_CLOSE = 2
	TRADE_MODIFY = 3
	TRADE_DELETE = 4 

class XTBTrade:
	
	def __init__(self):
		
		self.json_obj = {}
	
	def __repr__(self):
		
		return json.dumps(self.json_obj)
	
	def __str__(self):
		
		return json.dumps(self.json_obj)
	
	@staticmethod
	def buy(vol, name="long"):
		
		t = XTBTrade()
		t.json_obj["cmd"] = 0
		t.json_obj["customComment"] = name
		t.json_obj["expiration"] = 0
		t.json_obj["offset"] = 0
		t.json_obj["order"] = 0
		t.json_obj["sl"] = 0.0
		t.json_obj["symbol"] = ""
		t.json_obj["tp"] = 0.0
		t.json_obj["open"] = 0
		t.json_obj["volume"] = vol
		t.json_obj["price"] = 0.0001
		return t
	
	@staticmethod
	def sell(vol, name="short"):
		
		t = XTBTrade()
		t.json_obj["cmd"] = 1
		t.json_obj["customComment"] = name
		t.json_obj["expiration"] = 0
		t.json_obj["offset"] = 0
		t.json_obj["order"] = 0
		t.json_obj["sl"] = 0.0
		t.json_obj["symbol"] = ""
		t.json_obj["tp"] = 0.0
		t.json_obj["open"] = 0
		t.json_obj["volume"] = vol
		t.json_obj["price"] = 0.0001
		return t
	
	@staticmethod
	def close(vol, pos_id):
		
		t = XTBTrade()
		t.json_obj["cmd"] = 0
		t.json_obj["expiration"] = 0
		t.json_obj["offset"] = 0
		t.json_obj["order"] = pos_id
		t.json_obj["sl"] = 0.0
		t.json_obj["symbol"] = ""
		t.json_obj["tp"] = 0.0
		t.json_obj["type"] = 2
		t.json_obj["volume"] = vol
		t.json_obj["price"] = 0.0001
		return t
	
	@staticmethod
	def modify(vol, pos_id):
		
		t = XTBTrade()
		t.json_obj["cmd"] = 0
		t.json_obj["expiration"] = 0
		t.json_obj["offset"] = 0
		t.json_obj["order"] = pos_id
		t.json_obj["sl"] = 0.0
		t.json_obj["symbol"] = ""
		t.json_obj["tp"] = 0.0
		t.json_obj["type"] = 3
		t.json_obj["volume"] = vol
		t.json_obj["price"] = 0.0001
		return t
	
	def of(self, symbol):
		
		self.json_obj["symbol"] = symbol
		return self
	
	def at(self, price, using_limit=False):
		
		self.json_obj["price"] = price
		if using_limit:
			if self.json_obj["cmd"] == 0 or t.json_obj["cmd"] == 4:		# BUY MARKET
				self.json_obj["cmd"] = 2
			elif self.json_obj["cmd"] == 1 or t.json_obj["cmd"] == 5:		# SELL MARKET
				self.json_obj["cmd"] = 3
		else:
			if self.json_obj["cmd"] == 0 or t.json_obj["cmd"] == 2:		# BUY MARKET
				self.json_obj["cmd"] = 4
			elif self.json_obj["cmd"] == 1 or t.json_obj["cmd"] == 3:		# SELL MARKET
				self.json_obj["cmd"] = 5
		return self
	
	def profit(self, profit):
		
		self.json_obj["tp"] = profit
		return self
	
	def loss(self, loss):
		
		self.json_obj["sl"] = loss
		return self
	
	def get(self):
		
		print(self.json_obj)
		return self.json_obj
