import json, socket, ssl, pandas
import numpy, threading
from datetime import datetime
from datetime import timedelta
import time	
from .command import XTBCommand
from .command import XTBStream
from .command import XTBPing
from .structs import XTBTrade
import pandas

class XTBClient:
	
	def __init__(self, demo=True):
		
		self.streams = {}
		self.demo = demo
		if demo:
			main_port = 5124
			self.stream_port = 5125
		else:
			main_port = 5112
			self.stream_port = 5113
		self.main_sslctx = ssl.create_default_context()
		self.main_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
		self.main_sock.connect(('xapi.xtb.com', main_port))
		self.main_ssock = self.main_sslctx.wrap_socket(self.main_sock, server_hostname='xapi.xtb.com')
		self.threads = {}
	
	@staticmethod
	def get_full_protocol_block(sock):
		
		response = bytearray()
		while True:
			partial_response = sock.recv(1)
			response += partial_response
			if response[-1] == 10 and response[-2] == 10:
				break
		return response
			
	def request(self, req):
		
		data = req.get_bytes()
		self.main_ssock.send(data)
		self.response = XTBClient.get_full_protocol_block(self.main_ssock)
		self.response = self.response.decode("utf-8")
		self.response = json.loads(self.response)
		return self.response
	
	def stream_handler(self, stream, socket_tuple, callback):
		
		## TODO: TIMEOUT, so that stream_handler is interruptable
		t = threading.currentThread()
		socket_tuple[2].setblocking(True)
		socket_tuple[2].send(stream.get_bytes())
		streaming_command = stream.command()
		if streaming_command.startswith("get"):
			streaming_command = streaming_command[3:]
		while getattr(t, "do_run", True):
			res = XTBClient.get_full_protocol_block(socket_tuple[2])
			json_obj = json.loads(res.decode("utf-8"))
			callback(json_obj["data"], self)
		stop_streaming_command = "stop" + streaming_command
		stop_stream = XTBStream(stop_streaming_command, stream.sid())
		socket_tuple[2].send(stop_stream.get_bytes())
		
	
	def subscribe(self, stream, callback):
		
		sslctx = ssl.create_default_context()
		sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
		sock.connect(('xapi.xtb.com',self.stream_port))
		ssock = sslctx.wrap_socket(sock, server_hostname='xapi.xtb.com')
		thr = threading.Thread(target=XTBClient.stream_handler, args=(self, stream, (sslctx, sock, ssock), callback))
		self.threads[stream.command()] = thr
		thr.start()
	
	def ping(self):

		req = XTBPing(self.sid).get_bytes()
		sslctx = ssl.create_default_context()
		sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
		sock.connect(('xapi.xtb.com',self.stream_port))
		ssock = sslctx.wrap_socket(sock, server_hostname='xapi.xtb.com')
		ssock.send(req)
		ssock.close()
		sock.close()

	def unsubscribe(self, stream):
		
		t = self.threads[stream.command()]
		setattr(t, "do_run", False)
		t.join()
	
	def login(self, username, password):
		
		res = self.request( \
			XTBCommand("login") \
				.add("userId", username) \
				.add("password", password) \
		)
		self.sid = res["streamSessionId"]
		return res["status"]
	
	def logout(self):
		
		res = self.request( \
			XTBCommand("logout") \
		)
		return res["status"]
	
	@staticmethod
	def filter_matching_records(records, key, value):
		
		l = []
		for record in records:
			if record[key] == value:
				l.append(record)
		return l
	
	def opentrades(self, name = None):
		
		res = self.request( \
			XTBCommand("getTrades") \
				.add("openedOnly", True) \
		)
		
		if name is not None:
			return XTBClient.filter_matching_records(res["returnData"], "customComment", name)
		else:
			return res["returnData"]
	
	def exit(self, name, qty, loss = None, profit = None):
		
		# check for open trades with that name
		ot = self.opentrades(name = name)
		if len(ot) > 0:
			pos_id = ot[0]["position"]
			pos_symb = ot[0]["symbol"]
		else:
			print("no such position to exit")
			return
		
		t = XTBTrade.modify(qty, pos_id).of(pos_symb)
		if loss is None and profit is None:
			t = XTBTrade.close(qty, pos_id).of(pos_symb)
		elif loss is None and profit is not None:
			t.profit(profit)
		elif loss is not None and profit is None:
			t.loss(loss)
		else:
			t.profit(profit)
			t.loss(loss)
			
		res = self.request( \
			XTBCommand("tradeTransaction") \
				.add("tradeTransInfo", t.get()) \
		)
		
	def entry(self, name, qty, symbol, is_short = False, stop = None, limit = None):
		
		# check for open trades with that name so that we don't
		# re-enter the same position
		ot = self.opentrades(name = name)
		if len(ot) > 0:
			print("Already entered position named" + name)
			return
		
		# build the transaction object
		if stop is not None and limit is not None:
			print("Error: Stop and Limit price where both specified.")
			return
		elif stop is None and limit is None:
			print("no limit or stop specified. Using Market Order")
			use_market_order = True
		elif limit is not None and stop is None:
			use_market_order = False
			price = float(limit)
			is_limit = True
		elif limit is None and stop is not None:
			use_market_order = False
			price = float(stop)
			is_limit = True
			
		if is_short:
			t = XTBTrade.sell(float(qty), name = name).of(str(symbol))
		else:
			t = XTBTrade.buy(float(qty), name = name).of(str(symbol))
		if not use_market_order:
			t.at(price, using_limit=is_limit)
		
		# request the trade
		res = self.request( \
			XTBCommand("tradeTransaction") \
				.add("tradeTransInfo", t.get()) \
		)
		if res["status"] == True:
			orderid = res["returnData"]["order"]
		else:
			print(res)
			print("Protocol Error when requesting the Trade: " + name)
			return
		
		# check transaction status
		res = self.request( \
			XTBCommand("tradeTransactionStatus") \
				.add("order", orderid) \
			)
	
	@staticmethod
	def hist_to_pandas(hist_array):
		
		j = pandas.read_json(json.dumps(hist_array))
		j = j.drop(columns='ctmString')
		j['ctm'] = j['ctm']/1000
		j['ctm'] =pandas.to_datetime(j['ctm'], unit='s')
		j = j.rename(columns={'ctm':'date'})
		j = j.set_index('date')
		# XTB gives close prices as absolute values
		# the others are differences to open
		j['close'] = j['open'] + j['close'] 
		j['high'] = j['open'] + j['high']
		j['low'] = j['open'] + j['low']
		return j
	
	def history(self, symbol, frame, ticks):
		
		req = XTBCommand("getChartRangeRequest")
		info = {}
		info["period"] = frame
		info["ticks"] = ticks
		n = datetime.now().replace(second=0)
		n = n.replace(microsecond=0)
		if frame == 1:
			pass
		elif frame == 5:
			n = n.replace(minute=n.minute - n.minute % 5)
		elif frame == 15:
			n = n.replace(minute=n.minute - n.minute % 15)
		elif frame == 30:
			n = n.replace(minute=n.minute - n.minute % 30)
		elif frame == 60:
			n = n.replace(minute=0)
		elif frame == 240:
			n = n.replace(minute=0)
			n = n.replace(hour=n.hour - n.hour % 4)
		elif frame == 1440:
			n = n.replace(minute=0, hour=0)
		elif frame == 10080:
			n = n.replace(minute=0, hour=0)
			dow = n.weekday()
			n = n - timedelta(days=dow)
		elif frame == 43200:
			n = n.replace(minute=0, hour=0, day=1)
		else:
			print("invalid frame value")
			return []
		n = int(n.timestamp()*1000)
		info["start"] =  n
		info["symbol"] = symbol
		info["end"] = 0
		req.add("info", info)
		res = self.request(req)
		return XTBClient.hist_to_pandas(res["returnData"]["rateInfos"])
