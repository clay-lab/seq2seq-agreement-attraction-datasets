'''
general functions that are 
useful across different languages
'''
import re

from ..constants import (
	EXCLUSION_STRINGS, 
	VALID_SENTENCE_ENDING_CHARS,
	DELIMITERS,
	MAX_SENTENCE_LENGTH_IN_WORDS,
	MIN_SENTENCE_LENGTH_IN_CHARS,
	EXCLUSION_REGEXES
)

def string_conditions(s: str) -> bool:
	'''
	Does the string pass certain basic checks?
	A lot of data from naturalistic sets
	is noisy, so we filter out a lot of garbage here.
	'''
	
	# must be longer than a single character
	if len(s) < MIN_SENTENCE_LENGTH_IN_CHARS:
		return False
	
	# must start with a capital letter
	if s[0].islower():
		return False
	
	# don't start with an acronym/abbreviation
	if s.split()[0].isupper():
		return False
	
	# too long!
	if len(s.split()) > MAX_SENTENCE_LENGTH_IN_WORDS:
		return False
	
	# must not contain a semicolon (i.e., two sentences)
	# must not contain a quote (also two sentences)
	# must not have spaces before commas and periods
	# must not have a newline
	if any(c in s for c in EXCLUSION_STRINGS):
		return False
	
	# must end with a valid sentenec ending character
	if not any(s.endswith(c) for c in VALID_SENTENCE_ENDING_CHARS):
		return False
	
	# must not contain an odd number of parentheses (partial sentences)
	for d1, d2 in DELIMITERS:
		if s.count(d1) != s.count(d2):
			return False
		
		# the closing delimiter can't come before the first opening delimiter
		if d1 in s and d2 in s:
			if s.index(d2) < s.index(d1):
				return False
		
		# the opening delimiter can't follow the final closing delimiter
		# we're not doing anything fancier than these because it's more annoying
		# and doesn't really come up
		if d2 in s and d1 in s:
			if s[::-1].index(d1) < s[::-1].index(d2):
				return False
	
	if any(re.search(regex, s) for regex in EXCLUSION_REGEXES):
		return False
	
	return True