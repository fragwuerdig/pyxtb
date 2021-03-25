import json, socket, ssl, pandas
import numpy, threading
from datetime import datetime
import time

class XTBCommand:
	
	def __init__(self, name):
		
		self.json_obj = {}
		self.json_obj["command"] = name
		self.json_obj["arguments"] = {}
	
	def add(self, key, value):
		
		self.json_obj["arguments"][key] = value
		return self
	
	def get(self):
		
		return self.json_obj
	
	def get_bytes(self):
		
		return json.dumps(self.json_obj).encode("utf-8")

class XTBStream:
	
	def __init__(self, command, sid):
		
		self.json_obj = {}
		self.json_obj["command"] = command
		self.json_obj["streamSessionId"] = sid
	
	def add(self, key, value):
		
		self.json_obj[key] = value
		return self
	
	def command(self):
		
		return self.json_obj["command"]
	
	def sid(self):
	
		return self.json_obj["streamSessionId"]
	
	def get_bytes(self):
		
		return json.dumps(self.json_obj).encode("utf-8")

class XTBPing:

	def __init__(self, sid):

		self.json_obj = {}
		self.json_obj["command"] = "ping"
		self.json_obj["streamSessionId"] = sid

	def get_bytes(self):

		return json.dumps(self.json_obj).encode("utf-8")
