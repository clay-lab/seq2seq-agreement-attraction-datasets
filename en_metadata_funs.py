from typing import *

def get_metadata(pair: Dict) -> Dict:
	"""
	Gets metadata about the passed example, consisting of a seq2seq mapping with a source, prefix, and target.
	:param pair: a dict mapping the keys 'src', 'prefix', and 'tgt' to an EDoc, a str, and an EDoc, respectively.
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
	source = pair['src']
	prefix = pair['prefix']
	target = pair['tgt']
	
	metadata = {}
	
	metadata.update({'subject_number': source.main_subject_number})
	
	if source.has_main_object:
		metadata.update({'object_number': source.main_object_number})
	else:
		metadata.update({'object_number': None})
	
	# main verb
	metadata.update({'main_verb': source.main_verb})
	
	metadata.update({'n_interveners': len(source.main_subject_verb_interveners)})
	if source.has_main_subject_verb_interveners:
		final_intervener_number = source.main_subject_verb_interveners[-1].get_morph('Number')
		metadata.update({'final_intervener_number': final_intervener_number})
	else:
		metadata.update({'final_intervener_number': None})
	
	metadata.update({'n_distractors': len(source.main_subject_verb_distractors)})
	metadata.update({'pos_sequence': source.pos_seq})
	metadata.update({'tense': pfx})
	
	return metadata