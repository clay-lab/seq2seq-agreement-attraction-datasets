'''
general functions that are 
useful across different languages
'''
def string_conditions(s: str) -> bool:
	'''
	Does the string pass certain basic checks?
	A lot of data from naturalistic sets
	is noisy, so we filter out a lot of garbage here.
	'''
	
	# must be longer than a single character
	if len(s) <= 1:
		return False
	
	# must start with a capital letter
	if s[0].islower():
		return False
	
	# too long!
	if len(s.split()) > 50:
		return False
	
	# must not contain a semicolon (i.e., two sentences)
	# must not contain a quote (also two sentences)
	# must not have spaces before commas and periods
	# must not have a newline
	if any(c in s for c in [';', '"', ' ,', ' .', '\n']):
		return False
	
	# must not contain a colon separating two word characters (occurs in references lists)
	if re.search(r'\w:\w', s):
		return False
	
	return True