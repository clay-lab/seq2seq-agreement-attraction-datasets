'''
Defines a with statement to use to timeout a 
function that might hang.
'''
import os
import signal
import logging

log = logging.getLogger(__name__)

if os.name == 'nt':
	log.warning(
		'WARNING: Timeout is not supported on Windows. '
		'(This message will be shown once per session.)'
	)

class timeout:
	def __init__(self, seconds=120, error_message='Timeout'):
		self.seconds = seconds
		self.error_message = error_message
	
	def handle_timeout(self, signum, frame):
		raise TimeoutError(self.error_message)
	
	def __enter__(self):
		if os.name != 'nt':
			signal.signal(signal.SIGALRM, self.handle_timeout)
			signal.alarm(self.seconds)			
	
	def __exit__(self, type, value, traceback):
		if os.name != 'nt':
			signal.alarm(0)