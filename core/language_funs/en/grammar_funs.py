import re
import sys
import string
import random
import logging
import traceback

from typing import Dict, Set, Union

from ..language_funs import string_conditions
from ...spacyutils import nlp, EDoc
from ...constants import *

log = logging.getLogger(__name__)

EN_STOP_CHARS: Set[str] = {
	'-',
	':',
	*[str(n) for n in range(10)], # digits, 0–9
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
	'No.',
	'approx.',
	'Approx.',
	'ca.',
	'Ca.',
	'Ps.',
	'ps.',
	'Col.',
	'col.',
	'Lt.',
	'lt.',
	'Gen.',
	'gen.',
	'Pvt.',
	'pvt.',
	'Pfc.',
	'pfc.',
	'Spc.',
	'spc.',
	'Cpl.',
	'cpl.',
	'Sgt.',
	'sgt.',
	'Sen.',
	'sen.',
	'Rep.',
	'rep.',
	'Ssg.',
	'ssg.',
	'Sfc.',
	'sfc.',
	'Msg.',
	'msg.',
	'Sgm.',
	'sgm.',
	'Csm.',
	'csm.',
	'Sma.',
	'sma.',
	'Cpt.',
	'Capt.',
	'cpt.',
	'capt.',
	'Maj.',
	'maj.',
	'Ltc.',
	'ltc.',
	'Bg.',
	'bg.',
	'Mg.',
	'mg.',
	'Ltg.',
	'ltg.',
	'Ga.',
	'ga.',
	'Brig.',
	'brig.',
	'Hon.',
	'hon.',
	'Nos.',
	'nos.',
	'Govt.',
	'govt.',
	'var.',
	'Var.',
}

MISPARSED_AS_VERBS: Set[str] = {
	'swans', # this should be a noun, but spaCy has misparsed it
			 # as a verb in 'Trumpeter swans winter along the upper Stuart.'
	'it', # don't know, but clearly wrong
	'debouche', # french
	'o', # don't know, but it's clearly wrong
	'in', # don't know, but it's clearly wrong
	'erinnert', # german
	'braucht', # german
	'te', # german
	'up', # not actually wrong, but misparsed as the verb in "level up"
	'between',
}

COMMON_VERB_TYPOS: Set[str] = {
	'where', # from were
	'seee', # from seee
	'lieas', # from lies
	'a', # from are (only used if it's a verb, so no worries about determiners)
	'ia' # from is
	'vere', # from veer
	'prevee', # ????
	'tooj', # from took
	'wnt', # from want
	'wonn', # from won
	'competied', # from compete
	'competies', # from compete
	'competended', # no idea
	'competends',
	'competend',
	'thik', # for think
	'residens', # for reside
	'liesin', # for lies in
	'legendnto', # for ???
	'Its', # for It's
	'isis', # for is
	'comprices', # for comprises
	'cincludes', # for includes
	'buit', # for built
	'bidded', # for bid
	'wereFK', # for were
	'superwised', # for supervised
	'ses', # for sees
	'reregisted', # for reregistered
	'getup', # for get up
	'though', # for 'thought'
	'sung', # for 'sang'
}

BAD_VERB_LEMMAS: Set[str] = {
	'focu', # due to a typo of "focuses"
}

# the wikipedia dump removes measure words
# like, "The terrain occupies 464 acres adjacent to..."
# becomes "The terrain occupies adjacent to..."
# for whatever reason. spaCy parses these as weird objects
# let's exclude them
BAD_OBJECTS: Set[str] = {
	'about',
	'adjacent',
	'the',
	'over',
	'approximately',
	'came',
	'an',
	'to',
	'.',
	'together',
	'between',
	'served',
	'former',
	'of',
}

def basic_conditions(s: str) -> Union[bool,EDoc]:
	'''Basic conditions to clean up noisy data.'''
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
		
		# no unidentified words or foreign words
		if any(t.pos_ == 'X' or t.tag_ == 'FW' for t in s):
			return False
		
		# main verb cannot start with a capital letter
		if s.main_verb.text[0].isupper():
			return False
		
		# disallow verbs with common typos
		if any(t in s.main_verb.text for t in COMMON_VERB_TYPOS):
			return False
		
		# spaCy has some trouble parsing certain rare verbs
		# 'Trumpeter swans winter along the upper Stuart.' parsed
		# 'swans' as the verb instead of winter
		if any(s.main_verb.text == t for t in MISPARSED_AS_VERBS):
			return False
		
		if any(s.main_verb.lemma_ == l for l in BAD_VERB_LEMMAS):
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
		
		return s
	except KeyboardInterrupt:
		sys.exit('User terminated program.')	
	except Exception as e:
		log.warning(f'\n\nExample "{s}" ran into an error!:\n\n')
		log.warning(traceback.format_exc())
		log.warning('\n\n')
		return False

def has_interveners_and_number_agreement_conditions(s: str) -> Union[bool,EDoc]:
	'''Returns sentences with number agreement and interveners.'''
	s = basic_conditions(s)
	if s:
		try:
			v = s.main_verb
			# was and were show agreement in the past tense,
			# but otherwise no English verbs do
			if v.get_morph('Tense') == 'Past' and not v.lemma_ == 'be':
				return False
			
			if not s.has_main_subject_verb_interveners:
				return False
			
			return s
		except KeyboardInterrupt:
			sys.exit('User terminated program.')	
		except Exception as e:
			log.warning(f'\n\nExample "{s}" ran into an error!:\n\n')
			log.warning(traceback.format_exc())
			log.warning('\n\n')
			return False
	else:
		return False	

def no_dist_conditions(s: str) -> Union[bool,EDoc]:
	'''
	If the sentence satisfies basic conditions and
	has no distractor nouns, return the sentence.
	Else, return False.
	'''
	s = basic_conditions(s)
	
	if s:	
		try:
			# if there are distractors, we don't want it for training
			if s.has_main_subject_verb_distractors:
				return False
			
			# a lot of these weird "The district covered about of Cambridge..."
			# show up. it's bizarre and consistently odd. I guess the measure
			# terms were removed from the dataset?
			if any(t for t in s if t.dep_ in OBJ_DEPS and t.text in BAD_OBJECTS):
				return False
			
			return s
		except KeyboardInterrupt:
			sys.exit('User terminated program.')	
		except Exception as e:
			log.warning(f'\n\nExample "{s}" ran into an error!:\n\n')
			log.warning(traceback.format_exc())
			log.warning('\n\n')
			return False
	else:
		return False

def question_conditions(s: str) -> Union[bool,EDoc]:
	'''
	No distractors, plus no presubject modifiers.
	Also main verbs must not be an aux. (We want do-support.)
	'''
	s = no_dist_conditions(s)
	if s:
		if any(v.is_aux for v in s.main_clause_verbs):
			return False
		
		subject = s.main_subject
		if isinstance(subject,list):
			subject_position = min([t.i for t in subject])
		else:
			subject_position = subject.i
		
		if any(t.i < subject_position for t in s.main_verb.children):
			return False
		else:
			return s		
	else:
		return False

def pres_or_past(s: EDoc, pres_p: float = 0.5) -> Dict:
	'''Generate a present tense or past tense pair, with p(past-to-pres) = pres_p.'''
	return present_pair(s) if random.random() < pres_p else past_pair(s)

def ques_or_past(s: EDoc, ques_p: float = 0.5) -> Dict:
	'''Generate a present tense or past tense pair, with p(past-to-pres) = pres_p.'''
	return question_pair(s) if random.random() < ques_p else past_pair(s)

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

def question_pair(s: EDoc) -> Dict:
	'''
	Get a pair of sentenecs where the source is 
	past tense and the target is present tense.
	''' 
	return {
		'src': s.make_main_verb_past_tense(),
		'prefix': 'ques_pres',
		'tgt': s.make_main_verb_present_tense().make_sentence_polar_question()
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
