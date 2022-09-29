import spacy

from pattern.en import singularize, pluralize

from pattern.en import conjugate
from pattern.en import SG, PL
from pattern.en import PAST, PRESENT

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

def pres_or_past(grammar: PCFG, pres_p: float = 0.5) -> Tuple:
	
	return present_pair(grammar) if random.random() < pres_p else past_pair(grammar)

def pres_or_past_no_pres_dist(grammar: PCFG, pres_p: float = 0.5) -> Tuple:
	
	source, pfx, target = pres_or_past(grammar, pres_p)
	
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
