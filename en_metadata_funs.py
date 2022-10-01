from typing import Dict

def get_en_metadata(pair: Dict) -> Dict:
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
	
	if source.has_main_subject_verb_interveners:
		final_intervener_number = source.main_subject_verb_interveners[-1].get_morph('Number')
	else:
		final_intervener_number = None
	
	metadata = dict(
				subject_number=source.main_subject_number,
				object_number=source.main_object_number,
				main_verb=source.main_verb.text,
				main_verb_lemma=source.main_verb.lemma_,
				n_interveners=len(source.main_subject_verb_interveners),
				final_intervener_number=final_intervener_number,
				n_distractors=len(source.main_subject_verb_distractors),
				pos_sequence=source.pos_seq,
				tense=prefix
			)
	
	return metadata