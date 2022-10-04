from typing import Dict

def get_metadata(pair: Dict) -> Dict:
	"""
	Gets metadata about the passed example, consisting of a seq2seq mapping with a source, prefix, and target.
	:param pair: a dict mapping the keys 'src', 'prefix', and 'tgt' to an EDoc, a str, and an EDoc, respectively.
	:returns dict: a dictionary recording metadata for the source and target examples 
	"""
	source = pair['src']
	prefix = pair['prefix']
	target = pair['tgt']
	
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
				distractor_structures=source.main_subject_verb_distractor_structures,
				final_distractor_structure=source.main_subject_verb_final_distractor_structure,
				pos_sequence=source.pos_seq,
				tag_sequence=source.tag_seq,
				tense=prefix,
				src_history=source._history,
				tgt_history=target._history,
			)
	
	return metadata