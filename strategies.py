import time
from datetime import datetime
import pyxtb

class XTBBaseStrategy:
	
	def __init__(self, client, symbol, timeframe):
		
		self.timeframe = timeframe
		self.symbol = symbol
		self.client = client
		self.__internal_setup__()
	
	def __internal_setup__(self):
		
		self.curr_minute = self.client.servertime().minute
		self.last_minute = self.curr_minute
	
	def on_keep_alive(self, *args):
		
		self.client.ping()
	
	def on_bar(self, *args):
		
		print("bar")
	
	def on_tick(self, *args):
		
		res = args[0]
		client = args[1]
		unix_servertime = res["timestamp"]/1000
		self.curr_minute = datetime.utcfromtimestamp(unix_servertime).minute
		if self.curr_minute != self.last_minute:
			self.last_minute = self.curr_minute
			if self.curr_minute % self.timeframe == 0:
				self.on_bar(res, client)
	
	def run(self):
		
		self.keep_stream = pyxtb.XTBStream("getKeepAlive", self.client.sid)
		self.client.subscribe(self.keep_stream, XTBBaseStrategy.on_keep_alive, self)
		self.tick_stream = pyxtb.XTBStream("getTickPrices", self.client.sid).add("symbol", self.symbol).add("minArrivalTime", 100).add("maxLevel", 0)
		self.client.subscribe(self.tick_stream, XTBBaseStrategy.on_tick, self)
		try:
			while True:
				time.sleep(30)
		except KeyboardInterrupt:
			self.client.unsubscribe(self.keep_stream)
			self.client.unsubscribe(self.tick_stream)
