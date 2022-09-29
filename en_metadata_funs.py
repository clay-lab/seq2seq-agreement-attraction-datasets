from typing import *

def get_labels(t) -> List[str]:
	'''
	Get the labels of an NLTK tree.
	
	:param t: the tree whose labels to return
	:returns labels: a list of the labels of the Tree as strings,
					 corresponding to the linear order in which they would be printed.
	'''
	labels = [t.label().symbol()]
	for child in t:
		if isinstance(child, Tree):
			labels.extend(get_labels(child))
	
	return labels

def get_pos_labels(t) -> List[str]:
	'''
	Get the part-of-speech labels from an NLTK tree.
	This returns only the labels for the terminal nodes.
	
	:param t: the tree whose labels to return
	:returns labels: a list of the labels of the terminal nodes of the tree as strings,
					 corresponding to the linear order in which they would be printed.
	'''
	labels = []
	for child in t:
		if isinstance(child, Tree) and not isinstance(child[0], str):
			labels.extend(get_pos_labels(child))
		elif isinstance(child, str) or child[0] == '':
			pass
		elif not isinstance(child.label(), str):
			labels.append(child.label().symbol())
		else:
			labels.append(child.label())
	
	return labels

def format_tree_string(
	t, 
	lang: str = None, 
	pfx: str = None
) -> str:
	"""
	Convert a tree to a string.
	:param t: an NLTK Tree
	:param lang: str: the name of the language that generate the string (currently unused)
	:param pfx: str: whether the sentence is past or present (currently unused)
	:return: the flattened version of the tree as a string
	"""
	flattened_tree = ' '.join(t.leaves())
	flattened_tree = flattened_tree.strip()
	flattened_tree = flattened_tree.capitalize()
	flattened_tree += '.'
	
	return flattened_tree

def get_english_pos_seq(pos_seq: List[str]) -> str:
	'''Remove unwanted info from English pos tags for comparison purposes and return as a string.'''
	pos_seq = [
		pos_tag
			.replace('_sg', '')
			.replace('_pl', '')
		for pos_tag in pos_seq
	]
	pos_seq = '[' + '] ['.join([l for tag in [pos_tag.split() for pos_tag in pos_seq if pos_tag] for l in tag]) + ']'
	
	return pos_seq

def get_metadata(pair: Dict) -> Dict:
	"""
	Gets metadata about the passed example, consisting of a seq2seq mapping with a source, prefix, and target.
	:param source: the source Tree
	:param pfx: str: the task prefix passed to the model
	:param target: the target Tree
	:returns metadata: a dictionary recording the following properties for the example:
					   - transitivity of the main verb (v_trans)
					   - definiteness of main clause subject/object (subj_def, obj_def)
					   - number of main clause subject/object (subj_num, obj_num)
					   - the identity of the main auxiliary (main_aux)
					   - how many adverbial clauses before the main clause
					   - how many adverbial clauses after the main clause
					   - the number of adverbial clauses
					   - the PoS sequence of the source and target
	"""
	source = source.copy(deep=True)
	target = target.copy(deep=True)
	
	metadata = {}
	
	# definiteness of main clause subject
	main_clause_subject = grep_next_subtree(source, r'^DP$')
	main_clause_subject = grep_next_subtree(main_clause_subject, r'^NP$')
	while grep_next_subtree(main_clause_subject[0], r'^NP$'):
		main_clause_subject = grep_next_subtree(main_clause_subject[0], r'^NP$')
	
	main_clause_subject = grep_next_subtree(main_clause_subject, r'^N_')
	
	# number of main clause subject
	if main_clause_subject.label().symbol().endswith('sg'):
		metadata.update({'subject_number': 'sg'})
	else:
		metadata.update({'subject_number': 'pl'})
	
	main_clause_verb_phrase = grep_next_subtree(source, r'^VP$')
	main_clause_object = grep_next_subtree(main_clause_verb_phrase, r'^DP$')
	main_clause_object = grep_next_subtree(main_clause_object, r'^NP$')
	while grep_next_subtree(main_clause_object[0], r'^NP$'):
		main_clause_object = grep_next_subtree(main_clause_object[0], r'^NP$')
	
	main_clause_object = grep_next_subtree(main_clause_object, r'^N_')
		
	# number of main clause object
	if main_clause_object.label().symbol().endswith('sg'):
		metadata.update({'object_number': 'sg'})
	else:
		metadata.update({'object_number': 'pl'})
	
	# main verb
	main_clause_verb = grep_next_subtree(source, r'^V$')
	metadata.update({'main_verb': main_clause_verb[0]})
	
	# number of total, singular, and plural noun phrases between the head noun of the subject and the verb
	main_clause_full_subject = grep_next_subtree(source, r'^DP$')
	main_clause_full_subject = grep_next_subtree(main_clause_full_subject, r'^NP$')
	labels = get_labels(main_clause_full_subject)
	
	intervener_positions = [
		position 
		for position in main_clause_full_subject.treepositions() 
			if  hasattr(main_clause_full_subject[position], '_label') and
				(
					main_clause_full_subject[position].label().symbol().endswith('sg') or 
					main_clause_full_subject[position].label().symbol().endswith('pl')
				)
	][1:]
	
	if intervener_positions:
		final_intervener_number = re.findall(
			r'_(.*)', main_clause_full_subject[intervener_positions[-1]].label().symbol()
		)[0]
		
		metadata.update({'final_intervener_number': final_intervener_number})
	else:
		metadata.update({'final_intervener_number': None})
	
	# then filter to the sg or pl nouns after that
	pre_main_verb_noun_labels = [pos for pos in labels if pos.endswith('sg') or pos.endswith('pl')]
	
	# since the first noun in the list represents the subject, we exclude everything that matches it,
	# since matching nouns are not "distractors"
	distractors = [l for l in pre_main_verb_noun_labels if not l == pre_main_verb_noun_labels[0]]
	
	# subtract one from each to account for the actual head noun, which is not a distractor
	metadata.update({'n_distractors': len(distractors)})
	
	if metadata['n_distractors'] > 0:
		# get the number of the final pre-verb intervening noun (if one exists)
		# if there are any distractors
		# (if they are all the same, there's no way it can be attraction, but we are
		# interested in attraction if there are intermediate distractors)
		# first position is the subject
		
		# are the distractors in RCs or PPs or both?
		distractor_positions = [
			pos 
			for pos in intervener_positions
				if not re.findall(r'^N_(.*)$', str(main_clause_full_subject[pos].label())) == metadata['subject_number']
		]
		
		distractor_path_labels = [
			set([
				str(main_clause_full_subject[path[:i]].label()) 
				for i, _ in enumerate(path)
					if str(main_clause_full_subject[path[:i]].label()) in ['CP', 'PP']
			])
			for path in distractor_positions
		]
		
		distractor_structures = ['both' if len(ls) == 2 else ''.join(ls) for ls in distractor_path_labels]
		
		if distractor_structures == []: breakpoint()
		
		# if we've done all late attachment, it gives us a weird result. since the models aren't getting structures
		# we want to treat this like early attachment, which means rewriting some stuff
		if len(set(distractor_structures)) > 1:
			for i, _ in enumerate(distractor_structures[1:]):
				prev_distractor_structure = distractor_structures[i]
				if distractor_structures[i+1] != prev_distractor_structure:
					distractor_structures[i+1] = 'both'
		
		metadata.update({
			'each_distractor_structure': ','.join(distractor_structures),
			'distractor_structures': 'both' if len(set(distractor_structures)) == 2 else ','.join(set(distractor_structures)),
			'final_distractor_structure': distractor_structures[-1]
		})
	else:
		metadata.update({
			'each_distractor_structure': None,
			'distractor_structures': None,
			'final_distractor_structure': None,
		})
	
	# get pos seq with details suppressed	
	pos_seq = get_english_RC_PP_pos_seq(get_pos_labels(source))
	metadata.update({'pos_sequence': pos_seq})
	
	metadata.update({'tense': pfx})
	
	return metadata