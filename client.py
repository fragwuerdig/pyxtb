import json, socket, ssl, pandas
import numpy, threading
from datetime import datetime
import time	
from .command import XTBCommand
from .command import XTBStream

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
			partial_response = sock.recv(1024)
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
	
	@staticmethod
	def stream_handler(stream, socket_tuple, callback):
		
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
		stop_streaming_command = "stop" + streaming_command
		stop_stream = XTBStream(stop_streaming_command, stream.sid())
		socket_tuple[2].send(stop_stream.get_bytes())
		
	
	def subscribe(self, stream, callback):
		
		sslctx = ssl.create_default_context()
		sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
		sock.connect(('xapi.xtb.com',self.stream_port))
		ssock = sslctx.wrap_socket(sock, server_hostname='xapi.xtb.com')
		thr = threading.Thread(target=XTBClient.stream_handler, args=(stream, (sslctx, sock, ssock), callback))
		self.threads[stream.command()] = thr
		thr.start()
	
	def unsubscribe(self, stream):
		
		t = self.threads[stream.command()]
		setattr(t, "do_run", False)
		t.join()
