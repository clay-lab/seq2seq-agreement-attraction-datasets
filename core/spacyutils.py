'''
Useful wrappers for editing spaCy
Some of this is adapted from 
https://github.com/chartbeat-labs/textacy/blob/main/src/textacy/spacier/utils.py
'''
from typing import Union, List, Dict, Set
from collections import Counter

import spacy

from spacy.tokens.doc import Doc
from spacy.tokens.token import Token

from pattern.en import lexeme # just to deal with a bug
from pattern.en import singularize, pluralize
from pattern.en import conjugate
from pattern.en import SG, PL
from pattern.en import PAST, PRESENT

from .constants import *

nlp_ = spacy.load('en_core_web_trf', disable=['ner'])
nlp  = lambda s: EDoc(nlp_(s))

# workaround for pattern.en bug in python > 3.6
try:
	_ = lexeme('bad pattern.en >:(')
except RuntimeError:
	pass

class EToken():
	'''
	Wrapper around spaCy Token to implement useful methods.
	'''
	def __init__(self, token: Token) -> 'EToken':
		'''
		Creates an EToken from a spaCy Token.
		This has all the attributes needed to create
		a (E)Doc, but crucially they are editable.
		Note that this does NOT implement all of the
		other useful methods available to a spaCy Token,
		just what is needed to create something editable
		to make a new EDoc.
		'''
		self.text 			= token.text
		self.whitespace_	= token.whitespace_
		self.tag_			= token.tag_
		self.pos_			= token.pos_
		self.morph 			= token.morph
		self.lemma_			= token.lemma_
		self.head 			= token.head
		self.dep_ 			= token.dep_
		self.is_sent_start 	= token.is_sent_start
		self.ent_iob_		= token.ent_iob_
		self.rights 		= [EToken(t) for t in token.rights]
		self.children 		= [EToken(t) for t in token.children]
		self.i 				= token.i
		
		# spaCy doesn't respect this property when
		# we create a Doc manually using the constructor.
		# I don't know why. But let's fix it here.
		# this is a hack, but it will work for us.
		if self.i == 0:
			self.is_sent_start = True
		
		if self.text in INCORRECT_MORPHS:
			self.set_morph(**INCORRECT_MORPHS[self.text])		
	
	def __len__(self) -> int:
		'''Returns the length in characters of the token text.'''
		return len(self.text)
	
	def __unicode__(self) -> str:
		'''Returns the text of the token.'''
		return self.text
	
	def __bytes__(self) -> bytes:
		'''Returns the bytes of the token text.'''
		return self.__unicode__.encode('utf8')
	
	def __str__(self) -> str:
		'''Returns the text of the token.'''
		return self.__unicode__()
	
	def __repr__(self) -> str:
		'''Returns the text of the token.'''
		return self.__str__()
	
	@property
	def is_aux(self):
		'''Is the token an AUX?'''
		return self.pos_ == 'AUX'	
	
	@property
	def is_verb(self) -> bool:
		'''Is the token a verb?'''
		return self.pos_ == 'VERB'
	
	@property
	def can_be_inflected(self) -> bool:
		'''Can the (VERB) token be reinflected?'''
		return (self.is_verb and not self.tag_ == 'VBN') or self.is_aux
	
	@property
	def is_expl(self):
		'''Is the token an expletive?'''
		return self.pos_ == 'expl'
	
	@property
	def is_pronoun(self):
		'''Is the token a pronoun?'''
		return self.pos_ == 'PRON'
	
	@property
	def is_noun(self):
		'''Is the token a noun?'''
		return self.pos_ == 'NOUN'
	
	@property
	def is_determiner(self):
		'''Is the token a determiner?'''
		return self.pos_ == 'DET'
	
	@property
	def can_be_numbered(self):
		'''Can the (NOUN) token be renumbered?'''
		return self.is_noun or self.is_pronoun or self.is_determiner
	
	@property
	def is_singular(self) -> bool:
		'''Is the morph singular?'''
		n = self.get_morph('Number')
		return n == 'Sing' if n else None
	
	@property
	def is_plural(self) -> bool:
		'''Is the morph plural?'''
		n = self.get_morph('Number')
		return n == 'Plur' if n else None
	
	@property
	def is_past_tense(self) -> bool:
		'''Is the morph past tense?'''
		t = self.get_morph('Tense')
		return t == 'Past' if t else None
	
	@property
	def is_present_tense(self) -> bool:
		'''Is the morph present tense?'''
		t = self.get_morph('Tense')
		return t == 'Pres' if t else None
	
	@property
	def is_inflected(self):
		'''Is the (VERB) token inflected?'''
		return self.is_past_tense or self.is_present_tense	
	
	@property
	def _morph_to_dict(self) -> Dict:
		'''Get the morphological information as a dictionary.'''
		m = str(self.morph)
		if m:
			d = {k: v for k, v in [f.split('=') for f in m.split('|')]}
		else:
			d = {}	
		
		return d	
	
	@staticmethod
	def _dict_to_morph(d: Dict[str,str]) -> str:
		'''Convert a dict to morph format.'''
		d = {k: v for k, v in d.items() if v is not None}
		return '|'.join(['='.join([k, v]) for k, v in d.items()])
	
	def set_morph(self, **kwargs) -> Dict:
		'''
		Set/update morphs using kwargs.
		Use kwarg=None to remove a property.
		'''
		d = self._morph_to_dict
		d = {**d, **kwargs}
		self.morph = self._dict_to_morph(d)
	
	def get_morph(self, *args) -> Union[str,List[str]]:
		'''Returns the morphs in args that exist.'''
		ms = [self._morph_to_dict.get(k) for k in args]
		ms = [m for m in ms if m]
		if len(ms) == 1:
			ms = ms[0]
		
		return ms if ms else None
	
	def renumber(self, number: str) -> None:
		'''Renumber the token (if it is a noun).'''
		if not self.can_be_numbered:
			raise ValueError(f"'{self.text}' can't be renumbered; it's a {self.pos_}, not a det/noun!")
		
		if NUMBER_MAP[number] == SG:
			self.singularize()
		elif NUMBER_MAP[number] == PL:
			self.pluralize()
	
	def singularize(self) -> None:
		'''Make a (NOUN) token singular.'''
		if not self.get_morph('Number') == 'Sing':
			# bug in pattern.en.singularize and pluralize: don't deal with capital letters correctly
			# need to add exceptions: this doesn't work for 'these', 'those', 'all', etc. 
			self.text = SINGULARIZE_MAP.get(self.text.lower(), singularize(self.text.lower()))
			self.text = (self.text[0].upper() if self.is_sent_start else self.text[0]) + self.text[1:]
			self.set_morph(Number='Sing')
	
	def pluralize(self) -> None:
		'''Make a (NOUN) token plural.'''
		if not self.get_morph('Number') == 'Plur':
			self.text = PLURALIZE_MAP.get(self.text.lower(), pluralize(self.text.lower()))
			self.text = (self.text[0].upper() if self.is_sent_start else self.text[0]) + self.text[1:]
			self.set_morph(Number='Plur')
	
	def reinflect(
		self, 
		number: str = None, 
		tense: str = None, 
		**kwargs: Dict[str,str]
	) -> None:
		'''Reinflect the (VERB) token.'''
		if not self.can_be_inflected:
			raise ValueError(f"'{self.text}' can't be reinflected; it's a {self.pos_}, not a verb!")
		
		if number is None and tense is None:
			raise ValueError("At least one of {number, tense} must not be None!")
		
		number 	= self.get_morph('Number') if number is None else number
		tense 	= self.get_morph('Tense') if tense is None else tense
		try:
			self.text = conjugate(
							self.text, 
							number=NUMBER_MAP[number], 
							tense=TENSE_MAP[tense],
							**kwargs
						)
		except :
			print(self.text)
			breakpoint()
			
		n = 'Sing' if NUMBER_MAP[number] == SG else 'Plur'
		t = 'Past' if TENSE_MAP[tense] == PAST else 'Pres'
		
		self.set_morph(Number=n, Tense=t, **kwargs)
	
	def make_past_tense(self, number: str) -> None:
		'''Make the (VERB) token past tense.'''
		self.reinflect(number=number, tense=PAST)
	
	def make_present_tense(self, number: str) -> None:
		'''Make the (VERB) token present tense.'''
		self.reinflect(number=number, tense=PRESENT)

class EDoc():
	'''
	Wrapper around spaCy Doc to implement useful methods.
	'''
	def __init__(self, Doc: Doc) -> 'EDoc':
		'''Creates an EDoc wrapper around a spaCy Doc.'''
		self.doc = Doc
		self.vocab = Doc.vocab
		self.user_data = Doc.user_data
	
	def __repr__(self) -> str:
		'''Returns the sentence text of the Doc.'''
		return self.__str__()
	
	def __str__(self) -> str:
		'''Returns the sentence text of the Doc.'''
		return self.__unicode__()
	
	def __len__(self) -> int:
		'''Gets the length in words of the Doc.'''
		return len(self.doc)
	
	def __getitem__(self, i: Union[int,slice,str]) -> EToken:
		'''
		Returns an EToken of the token at index/indices.
		Also allows for getting attributes by name.
		'''
		if isinstance(i, slice):
			return [EToken(t) for t in self.doc[i]]
		elif isinstance(i, int):
			return EToken(self.doc[i])
		elif isinstance(i, str):
			return getattr(self, i)
	
	def __iter__(self) -> EToken:
		'''Iterates over tokens in the Doc.'''
		for t in self.doc:
			yield EToken(t)
	
	def __unicode__(self) -> str:
		'''Returns the text representation of the Doc.'''
		return ''.join([t.text_with_ws for t in self.doc])
	
	def __bytes__(self) -> bytes:
		'''Returns the bytes representation of the Doc.'''
		return self.__unicode__().encode('utf-8')
	
	def __setitem__(self, key, value) -> None:
		'''
		Because spaCy Doc is non-writable, 
		we have to return a new object.
		'''
		raise NotImplementedError((
			"To set a value, use copy_with_replace"
			"(tokens, indices) instead to create a new EDoc."
		))
	
	# Main thing of importance: allows editing by
	# returning a new spaCy doc that is identical to
	# the old one except with the tokens replaced.
	def copy_with_replace(
		self, 
		tokens: Union[Token,EToken,List[Union[Token,EToken]]], 
		indices: Union[int,List[int]] = None
	) -> 'EDoc':
		'''
		Creates a copy of the current SDoc with 
		the tokens at each of the indices
		replaced with snew tokens from the list.
		'''
		# get the properties of the current doc
		tokens 		= [tokens] if not isinstance(tokens, list) else tokens
		indices		= [t.i for t in tokens] if indices is None else indices
		indices 	= [indices] if not isinstance(indices,(list,range)) else indices
		
		if not len(tokens) == len(indices):
			raise ValueError('There must be an equal number of tokens and indices!') 
		
		vocab 		= self.vocab
		words 		= [t.text for t in self.doc]
		spaces 		= [t.whitespace_ == ' ' for t in self.doc]
		user_data	= self.user_data
		tags 		= [t.tag_ for t in self.doc]
		pos 		= [t.pos_ for t in self.doc]
		morphs 		= [str(t.morph) for t in self.doc]
		lemmas 		= [t.lemma_ for t in self.doc]
		heads 		= [t.head.i for t in self.doc]
		deps 		= [t.dep_ for t in self.doc]	
		sent_starts = [t.is_sent_start for t in self.doc]
		ents 		= [t.ent_iob_ for t in self.doc]
		
		# replace the properties at each index with the properties from the updated tokens
		for i, t in zip(indices, tokens):
			words[i] 		= t.text
			spaces[i]		= t.whitespace_
			tags[i]			= t.tag_
			pos[i]			= t.pos_
			morphs[i]		= str(t.morph)
			lemmas[i] 		= t.lemma_
			heads[i]		= t.head.i
			deps[i]			= t.dep_
			sent_starts[i] 	= t.is_sent_start
			ents[i]			= t.ent_iob_
		
		new_s = Doc(
			vocab=vocab,
			words=words,
			spaces=spaces,
			user_data=user_data,
			tags=tags,
			pos=pos,
			morphs=morphs,
			lemmas=lemmas,
			heads=heads,
			deps=deps,
			sent_starts=sent_starts,
			ents=ents
		)
		
		return EDoc(new_s)		
	
	def _copy_with_remove(
		self,
		indices: Union[int,List[int]]
	) -> 'EDoc':
		'''
		Creates a copy of the current doc with
		the tokens at the indices removed.
		Generally best to avoid; used internally
		for conjunction reduction.
		'''
		indices 	= [indices] if not isinstance(indices,(list,range)) else indices
				
		if any(i > (len(self) - 1) for i in indices):
			raise IndexError(
				f'The current doc is length {len(self)}, so '
				f'there is no token to remove at index >{len(self) - 1}!'
			)
		
		tokens 		= [t for t in self.doc if not t.i in indices]
		
		vocab 		= self.vocab
		words 		= [t.text for t in tokens]
		spaces 		= [t.whitespace_ == ' ' for t in tokens]
		user_data	= self.user_data
		tags 		= [t.tag_ for t in tokens]
		pos 		= [t.pos_ for t in tokens]
		morphs 		= [str(t.morph) for t in tokens]
		lemmas 		= [t.lemma_ for t in tokens]
		heads 		= [t.head.i for t in tokens]
		
		# have to reduce the head indices for each index we remove
		for i in indices:
			heads 	= [h - 1 if h > i else h for h in heads]
		
		deps 		= [t.dep_ for t in tokens]	
		sent_starts = [t.is_sent_start for t in tokens]
		sent_starts[0] = True # what if removing the first token?
		ents 		= [t.ent_iob_ for t in tokens]
		
		new_s = Doc(
			vocab=vocab,
			words=words,
			spaces=spaces,
			user_data=user_data,
			tags=tags,
			pos=pos,
			morphs=morphs,
			lemmas=lemmas,
			heads=heads,
			deps=deps,
			sent_starts=sent_starts,
			ents=ents
		)
		
		return EDoc(new_s)
	
	# CONVENIENCE PROPERTIES
	@property
	def root(self) -> EToken:
		'''Get the root node (i.e., main verb) of s.'''
		try:
			return EToken([
				t for t in self.doc if t.dep_ == 'ROOT'
			][0])
		except KeyboardInterrupt:
			print(self.doc)
			breakpoint()
	
	@property
	def root_is_verb(self) -> bool:
		'''
		Is the root a verb or aux?
		This is False if spaCy messed up.
		'''
		return self.root.is_verb or self.root.is_aux
	
	@property
	def main_verb(self) -> EToken:
		'''Convenience method for get_root().'''
		if self.root_is_verb:
			# in passives, the root is the participle, but we want the aux
			auxpass = [t for t in self.root.children if t.dep_ == 'auxpass']
			if auxpass:
				return auxpass[0]
			else:
				return self.root
		else:
			raise ValueError('There is no main verb for this sentence! (spaCy messed up)')
	
	@property
	def main_verb_tense(self) -> str:
		'''Gets the tense of the main verb.'''
		v = self.main_verb
		return v.get_morph('Tense')
	
	@property
	def has_main_subject(self) -> bool:
		'''
		Does the main verb have a subject?
		Ungrammatical sentences and fragments
		can fail this.
		'''
		try:
			self.main_subject
			return True
		except IndexError:
			return False
	
	@property
	def main_subject(self) -> Union[EToken,List[EToken]]:
		'''Gets the main clause subject of the SDoc if one exists.'''
		v = self.main_verb		
		s = [EToken(t) for t in v.children if t.dep_ in SUBJ_DEPS]
		
		# in passives, spaCy parses the participle as the main verb
		# and assigns it the dependency to the subject
		# however, we return the main verb as the aux
		# in this case, we want to get the subject spaCy assigned
		# to the participle instead, so we go through the head
		# of the auxpass = main_verb
		if not s:
			s = [EToken(t) for t in v.head.children if t.dep_ in SUBJ_DEPS]
			
		s.extend(EToken(t) for t in self._get_conjuncts(s[0]))
		
		if len(s) == 1:
			s = s[0]
		
		return s
	
	@property
	def main_subject_number(self) -> str:
		'''Gets the number feature of the main clause subject.'''
		s = self.main_subject
		
		if isinstance(s,list) and len(s) > 1:
			return self._get_list_subject_number(s)
		elif self.main_subject.dep_ in ['csubj', 'csubjpass']:
			# clausal subjects are not correctly associated
			# with a Singular number feature
			return 'Sing'
		else:
			return s.get_morph('Number')
	
	@property
	def has_singular_main_subject(self) -> str:
		'''Is the main subject singular?'''
		return self.main_subject_number == 'Sing'
	
	@property
	def has_plural_main_subject(self) -> str:
		'''Is the main subject plural?'''
		return self.main_subject_number == 'Plur'
	
	@property
	def has_conjoined_main_subject(self):
		'''Is the main subject a conjoined phrase?'''
		s = self.main_subject
		
		if isinstance(s,list):
			return any(self._get_conjuncts(s[0]))
		
		return False
	
	def _get_list_subject_number(self, s: List[EToken]) -> str:
		'''
		We call this to get the number of the subject when
		there are multiple subject dependencies in a sentence.
		This happens with expletive 'it' subjects, some copular
		sentences, and sentences with conjoined subjects.
		'''
		tag_counts = Counter([t.dep_ for t in s])
		# happens with some dummy 'it' subject sentences
		# and some copular sentences
		# one subject and one attr
		if tag_counts['nsubj'] == 1 and tag_counts['attr'] == 1:
			nums = [t.get_morph('Number') for t in s]
			# if all the subjects are singular and we have one attr
			# and one nsubj, then the subject is singular
			if all([n == 'Sing' for n in nums]):
				return 'Sing'
			# this happens in weird cases like
			# "the best thing were the movies we watched..."
			# in this case, we just go with the verb number if possible
			# otherwise, choose the first number feature that exists
			# in a subject noun. If none exists, breakpoint
			else:
				if self.main_verb.get_morph('Number'):
					return self.main_verb.get_morph('Number')
				
				for subj in s:
					if subj.get_morph('Number'):
						return subj.get_morph('Number')
				else:
					print(self.doc)
					breakpoint()			
		else:
			# conjoined subjects (i.e., and, or, etc.)
			return 'Plur'
	
	@property
	def main_subject_determiner(self) -> Union[EToken,List[EToken]]:
		'''Get the determiner(s) of the main subject.'''
		s = self.main_subject
		if not isinstance(s, list):
			s = [s]
		
		d = [c for subj in s for c in subj.children if c.dep_ == 'det']
		if len(d) == 1:
			d = d[0]
		elif len(d) == 0:
			d = None
		
		return d
	
	@property
	def main_subject_verb_interveners(self) -> List[EToken]:
		'''
		Get the tokens for the nouns that 
		intervene between the head noun(s)
		of the main subject and the main verb.
		'''
		s = self.main_subject
		if isinstance(s, list):
			s_loc = max([subj.i for subj in s]) + 1
		else:
			s_loc = s.i + 1
		
		v_loc = self.main_verb.i
		interveners = [EToken(t) for t in self[s_loc:v_loc] if t.pos_ == 'NOUN']
		
		return interveners
	
	@property
	def has_main_subject_verb_interveners(self) -> bool:
		'''Do any nouns come between the main subject and its verb?'''
		return any(self.main_subject_verb_interveners)
	
	@property
	def main_subject_verb_distractors(self) -> List[EToken]:
		'''
		Get the tokens for the interveners
		between the subject and the main verb
		that mismatch the head noun of the subject
		in the number feature. Note that this
		currently only works for distractors
		that occur after the subject head noun
		(i.e., not on Wagers et al. 2009) structures).
		'''
		n 			= self.main_subject_number
		interveners = self.main_subject_verb_interveners
		distractors = [t for t in interveners if t.get_morph('Number') != n]
		return distractors
	
	@property
	def has_main_subject_verb_distractors(self) -> bool:
		'''Are there any distractors between the main clause subject and the main clause verb?'''
		return any(self.main_subject_verb_distractors)
	
	@property
	def main_subject_verb_distractors_determiners(self) -> List[EToken]:
		'''
		Get the determiners for the interveners
		between the subject and the main verb
		that mismatch the head noun of the subject
		in the number feature. Note that this
		currently only works for distractors
		that occur after the subject head noun
		(i.e., not on Wagers et al. 2009) structures).
		'''
		n 			= self.main_subject_number
		interveners = self.main_subject_verb_interveners
		distractors = [t for t in interveners if t.get_morph('Number') != n]
		distractors_d = [t for d in distractors for t in d.children if d.dep_ == 'det']
		return distractors_d
	
	@property
	def has_main_object(self) -> bool:
		'''Does the sentence have an object of the main verb?'''
		return True if self.main_object else False
	
	@property
	def main_object(self) -> Union[EToken,List[EToken]]:
		v = self.main_verb
		s = [EToken(t) for t in v.children if t.dep_ in OBJ_DEPS]
		if s:
			s.extend(EToken(t) for t in self._get_conjuncts(s[0]))
		
		if len(s) == 1:
			s = s[0]
		
		return s
	
	@property
	def main_object_number(self) -> str:
		'''
		What is the number of the main object of the verb?
		Returns None if there is no object.
		'''
		if self.has_main_object:
			o = self.main_object
			if isinstance(o,list) and len(o) > 1:
				return 'Plur'
			else:
				return o.get_morph('Number')
	
	@property
	def pos_seq(self) -> List[str]:
		'''Get the part of speech sequence of the sentence.'''
		return [t.pos_ for t in self] 
	
	@staticmethod
	def _get_conjuncts(t: Union[Token,EToken]):
		'''Returns all conjuncts dependent on the first in a coordinated phrase.'''
		return [r for r in t.rights if r.dep_ == 'conj']
	
	# CONVENIENCE METHODS.
	# These return new objects; they do NOT modify in-place.
	def reinflect_main_verb(self, number: str, tense: str, **kwargs) -> 'EDoc':
		'''Reinflect the main verb.'''
		v = self.main_verb
		v.reinflect(number, tense, **kwargs)
		
		return self.copy_with_replace(tokens=v)
	
	def make_main_verb_past_tense(self) -> 'EDoc':
		'''Convert the main verb to past tense.'''
		n = self.main_subject_number
		return self.reinflect_main_verb(number=n, tense=PAST)
	
	def make_main_verb_present_tense(self) -> 'EDoc':
		'''Convert the main verb to present tense.'''
		n = self.main_subject_number
		return self.reinflect_main_verb(number=n, tense=PRESENT)
	
	def renumber_main_subject(self, number: str) -> 'EDoc':
		'''Renumber the main subject, along with its determiner and verb.'''
		if self.has_conjoined_main_subject and NUMBER_MAP.get(number) == SG:
			edoc = self._remove_conjunctions_to_main_subject()
		else:
			edoc = self
		
		tokens = []
		
		s = edoc.main_subject
		s.renumber(number=number)
		tokens.append(s)
		
		d = edoc.main_subject_determiner
		if d:
			d.renumber(number=number)
			tokens.append(d)
		
		v = edoc.main_verb
		v.reinflect(number=number)
		tokens.append(v)
		
		return edoc.copy_with_replace(tokens=tokens)
	
	def _remove_conjunctions_to_main_subject(self) -> 'EDoc':
		'''
		Return a copy of the current EDoc with all but the
		first noun of a conjoined subject removed. Useful
		when renumbering a sentence with a conjoined subject.
		'''
		if not self.has_conjoined_main_subject:
			return self
		
		s = self.main_subject
		
		# remove tokens after this position
		starting_index 	= s[0].i
		
		# until this position
		remove_until 	= max([t.i for t in s[1:]])
		
		# remove from one after the head of the conjP
		# until the final position to remove (range() is [x,y))
		range_to_remove = range(starting_index+1, remove_until+1)
		
		return self._copy_with_remove(indices=range_to_remove)
	
	def singularize_main_subject(self) -> 'EDoc':
		'''Make the main subject singular, and reinflect the verb.'''
		return self.renumber_main_subject(number=SG)
	
	def pluralize_main_subject(self) -> 'EDoc':
		'''Make the main subject plural.'''
		return self.renumber_main_subject(number=PL)
	
	def renumber_main_subject_verb_distractors(self, number: str) -> 'EDoc':
		'''Change the number of all distractor nouns.'''
		n = NUMBER_MAP[number]
		if n == SG:
			f = lambda t: t.singularize()
		elif n == PL:
			f = lambda t: t.pluralize()
		
		ds = self.main_subject_verb_distractors
		for i, _ in enumerate(ds):
			f(ds[i])
		
		dds = self.main_subject_verb_distractors_determiners
		for i, _ in enumerate(dds):
			f(dds[i])
		
		if ds:
			return self.copy_with_replace(tokens=ds + dds)
	
	def singularize_main_subject_verb_distractors(self) -> 'EDoc':
		'''Make all distractor nouns singular.'''
		return self.renumber_main_subject_verb_distractors(number=SG)
	
	def pluralize_main_subject_verb_distractors(self) -> 'EDoc':
		'''Make all distractor nouns plural.'''
		return self.renumber_main_subject_verb_distractors(number=PL)
	
	def auto_renumber_main_subject_verb_distractors(self) -> 'EDoc':
		'''Make all distractor nouns match the main subject number.'''
		n = NUMBER_MAP[self.main_subject_number]
		return self.renumber_main_subject_verb_distractors(number=n)