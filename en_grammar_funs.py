import re
import string
import random

from typing import *

from spacyutils import *

NUMBER_MAP = {
	'Sing': SG,
	'Plur': PL
}

def en_conditions(s: str) -> bool:
	'''
	Applies conditions to en sentence in order.
	These are currently ordered by how long it takes
	to perform each check, with shorter ones earlier.
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
	
	# must consist only of punctuation and english letters
	if not s.translate(str.maketrans('', '', string.punctuation)).isascii():
		return False
	
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
	
	# must not contain a colon separating two word characters (occurs in references lists)
	if re.search(r'\w:\w', s):
		return False
	
	# now we have to parse
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
	
	return True

def reinflect(t: spacy.tokens.doc.Doc) -> spacy.tokens.doc.Doc:
	'''
	Converts the main verb in a sentence from past to present tense.
	'''
	# Make a deep copy so we don't mess up the original tree
	t_copy = t.copy(deep=True)
	
	# get the main clause verb
	main_clause_VP = grep_next_subtree(t_copy, r'^VP$')
	main_clause_V = grep_next_subtree(main_clause_VP, r'^V$')
	
	# get the number of the main clause subject
	main_clause_subject = grep_next_subtree(t_copy, r'^DP$')
	main_clause_subject = grep_next_subtree(main_clause_subject, r'^NP$')
	while grep_next_subtree(main_clause_subject[0], r'^NP$'):
		main_clause_subject = grep_next_subtree(main_clause_subject[0], r'^NP$')
	
	main_clause_subject = grep_next_subtree(main_clause_subject, r'^N_')
	subject_number = 'sg' if str(main_clause_subject.label()).endswith('sg') else 'pl'
	
	# map the past form of the verb to the present form based on the number of the subject
	main_clause_V[0] = PAST_PRES[subject_number][main_clause_V[0]]
	
	return t_copy

def pres_or_past(s: spacy.tokens.doc.Doc, pres_p: float = 0.5) -> Dict:
	
	return present_pair(s) if random.random() < pres_p else past_pair(s)

def present_pair(s: spacy.tokens.doc.Doc) -> Dict:
	breakpoint()

def past_pair(s: spacy.tokens.doc.Doc) -> Dict:
	'''Create a past --> past pair from a dependency parsed sentence.'''
	# get the main clause verb
	main_verb = [t for t in s if t.dep_ == 'ROOT'][0]
	if main_verb.morph.get('Tense')[0] == 'Past':
		return {
			'src': s,
			'prefix': 'past',
			'tgt': s
		}
	
	# to reinflect, we need to get the subject number
	main_subject = [t for t in main_verb.children if t.dep_ == 'nsubj'][0]
	main_subject_num = main_subject.morph.get('Number')[0]
	
	# unfortunately, spaCy token's text is not writable, so we have to get around this
	# this could be better optimized, but whatever for now
	s = pd.DataFrame(s.to_json()['tokens']).assign(word = [t.text for t in s])
	s.loc[s.dep == 'ROOT', 'word'] = conjugate(
										s[s.dep == 'ROOT'].word.iloc[0], 
										number=NUMBER_MAP[main_subject_num], 
										tense=PAST
									)
	
	s = ' '.join(s.word)
	s = re.sub(rf'\s([{string.punctuation}])', '\\1', s)
	
	s = nlp(s)
	
	return {
		'src': s,
		'prefix': 'past',
		'tgt': s
	}		

def pres_or_past_no_pres_dist(s: spacy.tokens.doc.Doc, pres_p: float = 0.5) -> Tuple:
	breakpoint()
	source, pfx, target = tuple(pres_or_past(s, pres_p).values())
	
	# for English, we do not care about distractors in the past tense, since they do not affect attraction
	# in fact, we WANT some of these for training
	if pfx == 'pres':
		# otherwise, we need to modify the tree to change the number of all interveners to match the subject's number
		main_clause_subject = grep_next_subtree(source, r'^DP$')
		
		# this works now because the main clause subject is always the first noun!
		# it will need to be changed if we add nouns before the main clause subject
		pre_verb_noun_positions = [
			pos 
			for pos in main_clause_subject.treepositions() 
			if 	not isinstance(main_clause_subject[pos],str) and 
				re.search(r'^N_', str(main_clause_subject[pos].label()))
		]
		main_clause_subject_pos = pre_verb_noun_positions[0]
		
		if len(pre_verb_noun_positions) > 1:
			main_clause_subject_number = re.findall(r'_(.*)', str(main_clause_subject[main_clause_subject_pos].label()))[0]
			intervener_positions = [
				pos 
				for pos in pre_verb_noun_positions[1:] 
					if not re.findall(r'_(.*)', str(main_clause_subject[pos].label()))[0] == main_clause_subject_number
			]
			
			for t in [source, target]:
				
				main_clause_subject = grep_next_subtree(t, r'^DP$')
				
				for pos in intervener_positions:
					if main_clause_subject_number == 'sg':
						main_clause_subject[pos] = Tree(
							main_clause_subject[main_clause_subject_pos].label(),
							[re.sub('s$', '', main_clause_subject[pos][0])]
						)
					elif main_clause_subject_number == 'pl':
						if not main_clause_subject[pos][0].endswith('s'):
							main_clause_subject[pos] = Tree(
								main_clause_subject[main_clause_subject_pos].label(),
								[f'{main_clause_subject[pos][0]}s']
							)
			
	return source, pfx, target