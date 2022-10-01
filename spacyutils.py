'''
Useful wrappers for editing spaCy
Some of this is adapted from 
https://github.com/chartbeat-labs/textacy/blob/main/src/textacy/spacier/utils.py
'''
from typing import *

import spacy

from spacy.tokens.doc import Doc
from spacy.tokens.token import Token

from pattern.en import lexeme # just to deal with a bug
from pattern.en import singularize, pluralize
from pattern.en import conjugate
from pattern.en import SG, PL
from pattern.en import PAST, PRESENT

SUBJ_DEPS: Set[str] = {"csubj", "csubjpass", "expl", "nsubj", "nsubjpass"}
NUMBER_MAP: Dict[str,str] = {
	'Singular': SG,
	'singular': SG,
	'Sing': SG,
	'sing': SG,
	'SG': SG,
	'Sg': SG,
	'sg': SG,
	'Plural': PL,
	'plural': PL,
	'Plur': PL,
	'plur': PL,
	'PL': PL,
	'Pl': PL,
	'pl': PL,
}

TENSE_MAP: Dict[str,str] = {
	'PAST': PAST,
	'Past': PAST,
	'past': PAST,
	'Pst': PAST,
	'pst': PAST,
	'PRESENT': PRESENT,
	'Present': PRESENT,
	'present': PRESENT,
	'Pres': PRESENT,
	'pres': PRESENT
}

nlp_ = spacy.load('en_core_web_sm', disable=['ner'])
nlp = lambda s: EDoc(nlp_(s))

# workaround for pattern.en bug in python > 3.6
try:
	lexeme('bad pattern.en >:(')
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
		self.rights 		= token.rights
		self.children 		= token.children
		self.i 				= token.i
	
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
		return self.is_verb or self.is_aux
	
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
	def can_be_numbered(self):
		'''Can the (NOUN) token be renumbered?'''
		return self.is_noun or self.is_pronoun
	
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
		d = {k: v for k, v in [f.split('=') for f in m.split('|')]}
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
		if NUMBER_MAP[number] == SG:
			self.singularize()
		elif NUMBER_MAP[number] == PL:
			self.pluralize()
	
	def singularize(self) -> None:
		'''Make a (NOUN) token singular.'''
		if not self.can_be_numbered:
			raise ValueError(f'"{self.text}" can\'t be singularized; it\'s a {self.pos_}, not a noun!')
		
		if not self.get_morph('Number') == 'Sing':
			# bug in pattern.en.singularize and pluralize: don't deal with capital letters correctly
			self.text = singularize(self.text.lower())
			self.text = (self.text[0].upper() if self.is_sent_start else self.text[0]) + self.text[1:]
			self.set_morph(Number='Sing')
	
	def pluralize(self) -> None:
		'''Make a (NOUN) token plural.'''
		if not self.can_be_numbered:
			raise ValueError(f"'{self.text}' can't be pluralized; it's a {self.pos_}, not a noun!")
		
		if not self.get_morph('Number') == 'Plur':
			self.text = pluralize(self.text.lower())
			self.text = (self.text[0].upper() if self.is_sent_start else self.text[0]) + self.text[1:]
			self.set_morph(Number='Plur')
	
	def reinflect(self, number: str = None, tense: str = None, **kwargs: Dict[str,str]) -> None:
		'''Reinflect the (VERB) token.'''
		if not self.can_be_inflected:
			raise ValueError(f"'{self.text}' can't be reinflected; it's a {self.pos_}, not a verb!")
		
		if number is None and tense is None:
			raise ValueError("At least one of {number, tense} must not be None!")
		
		number 	= self.get_morph('Number') if number is None else number
		tense 	= self.get_morph('Tense') if tense is None else tense
		
		self.text = conjugate(
						self.text, 
						number=NUMBER_MAP[number], 
						tense=TENSE_MAP[tense],
						**kwargs
					)
		
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
		indices 	= [indices] if not isinstance(indices, list) else indices
		
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
	
	# CONVENIENCE PROPERTIES
	@property
	def root(self) -> Token:
		'''Get the root node (i.e., main verb) of s.'''
		return EToken([
			t for t in self.doc if t.dep_ == 'ROOT'
		][0])
	
	@property
	def main_verb(self) -> Token:
		'''Convenience method for get_root().'''
		return self.root
	
	@property
	def main_verb_tense(self) -> str:
		'''Gets the tense of the main verb.'''
		v = self.main_verb
		return v.get_morph('Tense')
	
	@property
	def main_subject(self) -> Union[EToken,List[EToken]]:
		'''Gets the main clause subject of the SDoc if one exists.'''
		v = self.main_verb
		s = [EToken(t) for t in v.children if t.dep_ in SUBJ_DEPS]
		s.extend(EToken(t) for t in self._get_conjuncts(s[0]))
		
		if len(s) == 1:
			s = s[0]
		
		return s
	
	@property
	def main_subject_number(self) -> str:
		'''Gets the number feature of the main clause subject.'''
		s = self.main_subject
		
		if isinstance(s,list) and len(s) > 1:
			# conjoined subjects (i.e., 'and', 'or', etc.)
			return 'Plur'
		else:
			return s.get_morph('Number')
	
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
	
	@staticmethod
	def _get_conjuncts(t: Union[Token,EToken]):
		'''Returns all conjuncts dependent on the first in a coordinated phrase.'''
		return [r for r in t.rights if r.dep_ == 'conj']
	
	# CONVENIENCE METHODS.
	# These return new objects; they do NOT modify in-place.
	def reinflect_main_verb(self, number, tense, **kwargs) -> 'EDoc':
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
	
	def renumber_main_subject(self, number) -> 'EDoc':
		s = self.main_subject
		s.renumber(number)
		
		v = self.main_verb
		v.reinflect(number=number)
		
		return self.copy_with_replace(tokens=[s,v])
	
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
		for i, t in enumerate(ds):
			f(ds[i])
		
		if ds:
			return self.copy_with_replace(tokens=ds)
	
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