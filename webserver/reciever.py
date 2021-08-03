#!/bin/env python3
# Written by Treebug842

from datetime import datetime
from socket import *
import json

class CreateServer():

	def __init__(self):
		self.port = 80
		# self.whitelist = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

	def __writeError_to_log(self, error):
		with open("alert_logs.txt", "a") as file:
			if error == "FORBIDDEN": file.write("Unwhitelisted IP address has tried to connect")
			elif error == "BAD_REQUEST": file.write("Recieved Bad Request")
			file.write("\n\n")

	def __write_to_log(self, message, time):
		with open("alert_logs.txt", "a") as file:
			file.write(f"Alert recieved {time}\n")
			file.write(f"Type: {message['type']}")
			file.write(f"Coin pair: {message['coin']}")
			file.write("\n\n")

	def runServer(self):
		serversocket = socket(AF_INET, SOCK_STREAM)
		try:
			serversocket.bind(('', self.port))
			serversocket.listen(5)
			while(True):
				while(True):
					(clientsocket, address) = serversocket.accept()
					raw_request = clientsocket.recv(5000).decode()
					request_data = raw_request.split("\n")

					# if address[0] not in self.whitelist:
					# 	data = "HTTP/1.1 403 Forbidden\r\n\r\n"
					# 	clientsocket.sendall(data.encode())
					# 	clientsocket.shutdown(SHUT_WR)
					# 	self.__writeError_to_log("FORBIDDEN")
					# 	break

					if request_data[0] != 'POST /webhook HTTP/1.1\r':
						data = "HTTP/1.1 400 Bad Request\r\n\r\n"
						clientsocket.sendall(data.encode())
						clientsocket.shutdown(SHUT_WR)
						self.__writeError_to_log("BAD_REQUEST")
						break

					data = "HTTP/1.1 200 OK\r\n\r\n"
					clientsocket.sendall(data.encode())
					clientsocket.shutdown(SHUT_WR)

					message = json.loads(request_data[-1])
					self.__write_to_log(message, datetime.now())

					self.trigger(message)
				
		except KeyboardInterrupt:
			print("\nShutting down...\n")
		except Exception as err:
			print("Error:'n")
			print(err)
		serversocket.close()




























