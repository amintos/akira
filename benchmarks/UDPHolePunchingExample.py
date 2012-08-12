'''
This is a small firewall hole punching example in python.

'''


from socket import *
s = socket(type = SOCK_DGRAM)
s.bind(('', 2345))  # send this port and your ip to the other person
ip = '87.78.83.217' # get ip
s.connect((, 1234)) # and port of other person's socket
s.setblocking(0)
def g():
	try:
		print s.recvfrom(1024)
	except error:
		print 'nothing'

		
def f():
	s.send('hello other side!')

	
import time
while 1:
	f()
	print 'sent'
	time.sleep(0.1)
	g()
	time.sleep(0.1)
