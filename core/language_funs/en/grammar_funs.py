import re
import sys
import string
import random
import logging
import traceback

from typing import Dict, Set

from ..language_funs import string_conditions
from ...spacyutils import nlp, EDoc
from ...constants import NOUN_POS_TAGS, SUBJ_EXCL_TAGS

log = logging.getLogger(__name__)

EN_STOP_CHARS: Set[str] = {
	'-',
	':',
	*[str(n) for n in range(10)],
	'–', # ndash, separates numbers (which we don't want)
	'—', # mdash, can separate two independent sentences
}

EN_ABBREVIATIONS: Set[str] = {
	'Prof.',
	'Blvd.',
	'Mrs.',
	'Ave.',
	'Ltd.',
	'Inc.',
	'Mr.',
	'Dr.',
	'Ms.',
	'St.',
	'Av.',
	'no.',
	'No.'
}

def no_dist_conditions(s: str) -> bool:
	'''
	Applies conditions to en sentence in order.
	These are currently ordered by how long it takes
	to perform each check, with shorter ones earlier.
	'''
	if not string_conditions(s):
		return False
	
	# these characters lead to weird behavior
	# by spaCy
	if any(c in s for c in EN_STOP_CHARS):
		return False
	
	# must be ascii when punctuation is removed
	if not s.translate(s.maketrans('', '', string.punctuation)).isascii():
		return False
	
	# English-specific filters
	if s[-1] == '.':
		# must not end with a . preceded by a capital letter (happens when splitting on middle names)
		if s[-2].isupper():
			return False
		
		if any(s.endswith(abb) for abb in EN_ABBREVIATIONS):
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
		
		if isinstance(s.main_subject,list):
			if not any(t.pos_ in NOUN_POS_TAGS for t in s.main_subject):
				return False
		elif not s.main_subject.pos_ in NOUN_POS_TAGS:
			return False
		
		if isinstance(s.main_subject,list):
			if any(t.tag_ in SUBJ_EXCL_TAGS for t in s.main_subject):
				return False
		elif s.main_subject.tag_ in SUBJ_EXCL_TAGS:
			return False
		
		# if the main subject
		# can be converted to a floating
		# point number, exclude it
		# this leads to all kinds of weird behavior
		try:
			if isinstance(s.main_subject,list):
				float(s.main_subject[0].text.replace(',', ''))
			else:
				float(s.main_subject.text.replace(',', ''))
			
			return False
		except ValueError:
			pass
		
		# surprisingly frequent typo of 'they' -> 'the'
		# and missing subjects after 'the'
		if isinstance(s.main_subject,list):
			if s.main_subject[0].text.lower() == 'the':
				return False
		else:
			if s.main_subject.text.lower() == 'the':
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
		log.warning(f'\n\nExample "{s}" ran into an error!:\n\n')
		log.warning(traceback.format_exc())
		log.warning('\n\n')
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
