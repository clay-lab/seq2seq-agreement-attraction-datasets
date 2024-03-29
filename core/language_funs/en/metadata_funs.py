import string

from ...spacyutils import EDoc
from .grammar_funs import SALTS_WORDS

from typing import Dict, Union

def get_salts_metadata(d: Dict) -> Dict:
	'''Get the word(s) in salts that occur(s) in the sentence.'''
	s = d['src']
	s = set(s.translate(s.maketrans('', '', string.punctuation)).split()[1:])
	
	words = [word for word in SALTS_WORDS if word in s]
	words = ','.join(words)
	
	return dict(salts_word=words)

def get_source_metadata(source: Union[Dict,EDoc]) -> Dict:
	"""
	Gets basic metadata about the passed EDoc example.
	Does
	:param pair: a dict mapping the keys 'src', 'prefix', and 'tgt' to an EDoc, a str, and an EDoc, respectively.
	:returns dict: a dictionary recording metadata for the source and target examples 
	"""
	if isinstance(source,dict):
		source = list(source.values())[0]
	
	if source.has_main_subject_verb_interveners:
		final_intervener_number = source.main_subject_verb_interveners[-1].get_morph('Number')
	else:
		final_intervener_number = None
	
	# the EDoc gets the number by checking the verb first
	# to ensure that as much as possible tense reinflection
	# matches the verb's original tense rather than the number
	# of the subject head noun.
	# however, we want to record this from the actual subject
	# head if possible, since that way it will be easier to track
	# mismatches (i.e., bad agreement)
	try:
		main_subject_number = source.main_subject.get_morph('Number')
	except AttributeError:
		main_subject_number = None 
	
	# fall back to the reported number if one doesn't exist for the noun itself
	if main_subject_number is None:
		main_subject_number = source.main_subject_number
	
	# if we still don't have one, 
	# mimic the default behavior when no subject number is found,
	# since this is usually right
	if main_subject_number is None:
		main_subject_number = 'Sing'
	
	metadata = dict(
				subject_number=main_subject_number,
				object_number=source.main_object_number,
				source_main_verb=source.main_verb.text,
				source_main_verb_lemma=source.main_verb.lemma_,
				n_interveners=len(source.main_subject_verb_interveners),
				intervener_structures=source.main_subject_verb_intervener_structures,
				final_intervener_number=final_intervener_number,
				final_intervener_structure=source.main_subject_verb_final_intervener_structure,
				n_distractors=len(source.main_subject_verb_distractors),
				distractor_structures=source.main_subject_verb_distractor_structures,
				final_distractor_structure=source.main_subject_verb_final_distractor_structure,
				pos_sequence=source.pos_seq,
				tag_sequence=source.tag_seq,
				src_history=source._history,
			)
	
	return metadata

def get_metadata(pair: Dict) -> Dict:
	"""
	Gets metadata about the passed example, consisting of a seq2seq mapping with a source, prefix, and target.
	:param pair: a dict mapping the keys 'src', 'prefix', and 'tgt' to an EDoc, a str, and an EDoc, respectively.
	:returns dict: a dictionary recording metadata for the source and target examples 
	"""
	source = pair['src']
	prefix = pair['prefix']
	target = pair['tgt']
	
	metadata = get_source_metadata(source)
	
	if metadata['source_main_verb_lemma'] != target.main_verb.lemma_:
		main_verb_lemmas = ','.join(list(dict.fromkeys([source.main_verb.lemma_, target.main_verb.lemma_])))
	else:
		main_verb_lemmas = 'both_ident'		
	
	metadata.update(dict(
		target_main_verb=target.main_verb.text,
		target_main_verb_lemma=target.main_verb.lemma_,
		main_verb_lemmas=main_verb_lemmas,
		tense=prefix,
		tgt_history=target._history,
	))
	
	return metadata