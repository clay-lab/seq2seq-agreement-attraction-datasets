import re
import string
import random
import logging

from typing import Dict

from ..language_funs import string_conditions
from ...spacyutils import nlp, EDoc

log = logging.getLogger(__name__)

def no_dist_conditions(s: str) -> bool:
	'''
	Applies conditions to en sentence in order.
	These are currently ordered by how long it takes
	to perform each check, with shorter ones earlier.
	'''
	if not string_conditions(s):
		return False
	
	# English-specific filters
	if s[-1] == '.':
		# must not end with a . preceded by a capital letter (happens when splitting on middle names)
		if s[-2].isupper():
			return False
		
		# must not end with a . preceded by an abbreviation
		if s[-5:] in ['Prof.', 'Blvd.']:
			return False
		
		if s[-4:] in ['Mrs.', 'Ave.', 'Ltd.', 'Inc.']:
			return False
		
		if s[-3:] in ['Mr.', 'Dr.', 'Ms.', 'St.', 'Av.']:
			return False
	
	# now we have to parse
	try:
		s = nlp(s)
		
		# if the root is not a verb, we don't want it
		if not s.root_is_verb:
			return False
		
		# if there is no subject, we don't want it
		if not s.has_main_subject:
			return False
		
		# if the main verb cannot be inflected, we don't want it
		if not s.main_verb.can_be_inflected:
			return False
		
		# if there are distractors, we don't want it for training
		if s.has_main_subject_verb_distractors:
			return False
		
		return s
	except KeyboardInterrupt:
		sys.exit('User terminated program.')	
	except Exception as e:
		log.warn(f'Example {s} ran into an error!:\n\n')
		log.warn(traceback.format_exc())
		log.warn('\n\n')
		return False

def pres_or_past(s: EDoc, pres_p: float = 0.5) -> Dict:
	'''Generate a present tense or past tense pair, with p(past-to-pres) = pres_p.'''
	return present_pair(s) if random.random() < pres_p else past_pair(s)

def present_pair(s: EDoc) -> Dict:
	'''
	Get a pair of sentenecs where the source is 
	past tense and the target is present tense.
	''' 
	return {
		'src': s.make_main_verb_past_tense(),
		'prefix': 'pres',
		'tgt': s.make_main_verb_present_tense()	
	}

def past_pair(s: EDoc) -> Dict:
	'''
	Get a pair of sentences where the 
	source and target are in past tense.
	'''
	s = s.make_main_verb_past_tense()
	
	return {
		'src': s,
		'prefix': 'past',
		'tgt': s
	}

def pres_or_past_no_pres_dist(s: EDoc, pres_p: float = 0.5) -> Dict:
	'''
	Get a pair of sentences where the
	source is in past tense, the target
	may be in present (p=pres_p) tense
	or past tense. If the target is
	in present tense, all will be renumbered
	so that they are no longer distractors.
	
	However, you should _probably_ not being using
	this, since it will not necessarily renumber
	all distractors correctly (i.e., proper nouns).
	Instead, filter out sentences with distractors
	to begin with, which will ensure accuracy.
	'''
	d = pres_or_past(s=s, pres_p=pres_p)
	
	if d['prefix'] == 'pres':
		d['tgt'] = d['tgt'].auto_renumber_main_subject_verb_distractors()
	
	return d
