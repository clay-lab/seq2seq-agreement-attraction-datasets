'''
Useful wrappers for editing spaCy
Some early parts of this are inspired by
https://github.com/chartbeat-labs/textacy/blob/main/src/textacy/spacier/utils.py
'''
import inspect
import logging

from typing import Union, List, Dict, Set, Tuple
from collections import Counter

import spacy

from spacy.tokens.doc import Doc
from spacy.tokens.token import Token

from pattern.en import lexeme # just to deal with a bug
from pattern.en import singularize, pluralize
from pattern.en import conjugate
from pattern.en import SG, PL
from pattern.en import PAST, PRESENT, INFINITIVE

from .constants import *
from .timeout import timeout

log = logging.getLogger(__name__)

nlp_ = spacy.load('en_core_web_trf', disable=['ner'])

# how many times to look up for a subject
# when determining whether a sentence can form a polar question
LOOK_FOR_SUBJECTS_LIMIT: int = 10

def flatten(items: 'Iterable', seqtypes: Tuple['Class'] = (list, tuple)):
	for i, x in enumerate(items):
		while i < len(items) and isinstance(items[i], seqtypes):
			items[i:i+1] = items[i]
	
	return items

# workaround for pattern.en bug in python > 3.6
try:
	_ = lexeme('bad pattern.en >:(')
except RuntimeError:
	pass

class ParseError(Exception):
	pass

def nlp(s: str) -> 'EDoc':
	with timeout(error_message=f'"{s}" took too long to process!'):
		try:
			return EDoc(nlp_(s))
		except Exception:
			raise ParseError(f'"{s}" ran into a parsing error!')

class EToken():
	'''
	Wrapper around spaCy Token to implement useful methods.
	'''
	def __init__(self, token: Token = None, d: Dict = None) -> 'EToken':
		'''
		Creates an EToken from a spaCy Token.
		This has all the attributes needed to create
		a (E)Doc, but crucially they are editable.
		Note that this does NOT implement all of the
		other useful methods available to a spaCy Token,
		just what is needed to create something editable
		to make a new EDoc.
		'''
		if token is None and d is None:
			raise ValueError('At least one of token or d must be provided!')
			
		if token is not None and d is not None:
			raise ValueError('At most one of token or d may be provided!')
		
		if d is None:
			self._token 		= token
			self.text 			= token.text
			self.whitespace_	= token.whitespace_
			self.tag_			= token.tag_
			self.pos_			= token.pos_
			self.morph 			= token.morph
			self.lemma_			= WRONG_LEMMAS.get(token.text, token.lemma_)
			self.dep_ 			= token.dep_
			self._head 			= token.head
			self.is_sent_start 	= token.is_sent_start
			self.ent_iob_		= token.ent_iob_
			self.i 				= token.i
		elif token is None:
			for k in d:
				setattr(self, k, d[k])
		
		self._format_token()
	
	def _format_token(self) -> None:
		# spaCy doesn't respect this property when
		# we create a Doc manually using the constructor.
		# I don't know why. But let's fix it here.
		# this is a hack, but it will work for us.
		if self.i == 0:
			self.is_sent_start = True
		
		if self.text in INCORRECT_MORPHS:
			self.set_morph(**INCORRECT_MORPHS[self.text])
		elif (
			self.text in INCORRECT_MORPHS_PRESENT_TENSE and 
			self.get_morph('Tense') == 'Pres'
		):
			self.set_morph(**INCORRECT_MORPHS_PRESENT_TENSE[self.text])	
		elif (
			self.pos_ == 'VERB' and
			self.get_morph('Tense') == 'Pres' and
			self.lemma_ == self.text
		):	# english hack: if we're a present tense
			# verb whose lemma matches the text,
			# we're plural!
			self.set_morph(Number='Plur')
		elif self.is_number:
			if self.text.lower() == 'one':
				self.set_morph(Number='Sing')
			else:
				self.set_morph(Number='Plur')
		
		if self.text in INCORRECT_POS:
			self.pos_ = INCORRECT_POS[self.text]
	
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
	def head(self) -> 'EToken':
		'''
		We do this as a property to save memory:
		this way we don't actually cast the head of the token
		to EToken until we need it. The problem is that
		not doing it this way would recursively cast every
		EToken to a head redundantly up the tree.
		'''
		return EToken(self._head) if not self.dep_ == 'ROOT' else self
	
	@head.setter
	def head(self, t: Union[Token,'EToken']) -> None:
		self._head = t
	
	@classmethod
	def from_definition(
		cls,
		text: str,
		whitespace_: str,
		tag_: str = '',
		pos_: str = '',
		morph: str = '',
		lemma_: str = '',
		head: str = '',
		dep_: str = '',
		is_sent_start: bool = False,
		ent_iob_: str = '',
		i: int = None,
	) -> 'EToken':
		'''Manually create an EToken.'''
		return EToken(d=dict(
			text=text,
			whitespace_=whitespace_,
			tag_=tag_,
			pos_=pos_,
			morph=morph,
			lemma_=lemma_,
			head=head,
			dep_=dep_,
			is_sent_start=is_sent_start,
			ent_iob_=ent_iob_,
			i=i,
		))
	
	def to_dict(self) -> dict:
		'''
		Return a dict that can be modified to construct an EToken
		from definition.
		'''
		return {k: v for k, v in vars(self) if not k.startswith('_')}		
	
	@property
	def polarity(self) -> str:
		'''Is the (verb) token positive or negative?'''
		if not (self.is_aux or self.is_verb):
			raise ValueError(f'A {self.pos_} cannot be positive or negative!')
		
		if not self.is_aux and any(t for t in self.children if t.dep_ == 'neg'):
			return 'Neg'
		elif self.is_aux and any(t for t in self.head.children if t.dep_ == 'neg'):
			return 'Neg'
		
		return 'Pos'
	
	@property
	def is_positive(self):
		'''Is the verb token positive?'''
		return self.polarity == 'Pos'
	
	@property
	def is_negative(self):
		'''Is the verb token negative?'''
		return self.polarity == 'Neg'
	
	@property
	def rights(self) -> 'EToken':
		'''Generator for the underlying Token's rights attribute.'''
		for t in self._token.rights:
			yield EToken(t)
	
	@property
	def children(self) -> 'EToken':
		'''Generator for the underlying Token's children attribute.'''
		for t in self._token.children:
			yield EToken(t)
	
	@property
	def is_aux(self) -> bool:
		'''Is the token an AUX?'''
		# be, even if it is a main verb, is always
		# grammatically an aux
		return self.pos_ == 'AUX' or self.lemma_ == 'be'
	
	@property
	def is_verb(self) -> bool:
		'''Is the token a verb?'''
		return self.pos_ == 'VERB'
	
	@property
	def is_number(self) -> bool:
		'''
		Is the word a string representation
		of a number (for English)?
		'''
		return word_is_number(self.text)	
	
	@property
	def can_be_inflected(self) -> bool:
		'''Can the (VERB) token be reinflected?'''
		return (
			not self.tag_ in ['VBN', 'VBG'] and
			(
				self.is_verb or 
				(self.is_aux and self.lemma_ in INFLECTED_AUXES)
			)
		)
	
	@property
	def can_be_decapitalized(self) -> bool:
		'''Can the token be safely decapitalized?'''
		# proper nouns and I (PRON) cannot be decapitalized
		return self.pos_ != 'PROPN' and not self.text == 'I'
	
	@property
	def is_expl(self) -> bool:
		'''Is the token an expletive?'''
		return self.pos_ == 'expl'
	
	@property
	def is_pronoun(self) -> bool:
		'''Is the token a pronoun?'''
		return self.pos_ == 'PRON'
	
	@property
	def is_noun(self) -> bool:
		'''Is the token a noun?'''
		return self.pos_ == 'NOUN'
	
	@property
	def is_determiner(self) -> bool:
		'''Is the token a determiner?'''
		return self.pos_ == 'DET'
	
	@property
	def can_be_numbered(self) -> bool:
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
	def is_inflected(self) -> bool:
		'''Is the (VERB) token inflected?'''
		return self.is_past_tense or self.is_present_tense	
	
	@property
	def determiner(self) -> Union['EToken',List['EToken']]:
		'''Returns the determiner(s) associated with the token.'''
		d = [
			c 
			for c in self.children 
				if 	c.dep_ in ['det', 'nummod'] or 
					(c.dep_ == 'amod' and c.text in AMOD_DETERMINERS)
		]
		
		if len(d) == 1:
			d = d[0]
		elif len(d) == 0:
			d = None
		
		return d
	
	@property
	def object(self) -> Union['EToken',List['EToken']]:
		'''Return the object(s) of the token.'''
		o = [t for t in self.children if t.dep_ in OBJ_DEPS]
		s = self.subject
		if not isinstance(s,list):
			s = [s] if s is not None else []
		
		o = [t for t in o if not any(t.i == t2.i for t2 in s)]
		if len(o) == 1:
			return o[0]
		elif len(o) > 1:
			return o
	
	@property
	def subject(self) -> Union['EToken',List['EToken']]:
		'''Return the subject(s) of the token.'''
		s = [t for t in self.children if t.dep_ in SUBJ_DEPS]
		
		# in passives, spaCy parses the participle as the main verb
		# and assigns it the dependency to the subject
		# however, we return the main verb as the aux
		# in this case, we want to get the subject spaCy assigned
		# to the participle instead, so we go through the head
		# of the auxpass = main_verb
		if not s:
			s = [t for t in self.head.children if t.dep_ in SUBJ_DEPS]
		
		if not s and self.is_aux:
			s = self.head.subject if not self.dep_ == 'ROOT' else None
		
		# this means we don't actually have a subject
		# sentence fragment, misparsed, or ungrammatical
		if s is None or not s:
			return None
		
		# now that we know we have something,
		# check for edge cases involve expletive/locative
		# inversion
		if not isinstance(s,list):
			s = [s]
		
		if (
			all(t.dep_ == 'expl' for t in s) and 			 # there
			(
				any(t.dep_ == 'xcomp' for t in self.children) or # to
				(self.is_aux and any(t.dep_ == 'xcomp' for t in self.head.children))
			)
		):
			ref_token = (
				self 
				if not (self.is_aux and any(t.dep_ == 'xcomp' for t in self.head.children)) 
				else self.head
			)
			# there used/seems to be/have been [subj]
			if any(t.lemma_ == 'be' for t in ref_token.children): # be
				s.extend([
					t for t in [
						t for t in ref_token.children if t.lemma_ == 'be'
					][0].children
						if t.dep_ in SUBJ_DEPS
				])
			elif any(t.is_verb for t in ref_token.children):
				# unaccusatives with there-inversion embedded under raising
				# in these cases, the actual inverted subject gets
				# misparsed as the object. this should not catch anything
				# else with an object dependency, since there inversion
				# without be can only happen with unaccusatives to begin with
				s.extend([
					t for t in [
						t for t in ref_token.children if t.is_verb
					][0].children
						if t.dep_ in OBJ_DEPS
				])
		elif (
			all(t.dep_ == 'expl' for t in s) and 
			(
				not self.lemma_ == 'be' or
				(self.is_aux and not any(t.lemma_ == 'be' for t in self.head.children))
			)
		):  # misparsed "there" with unaccusatives without raising
			ref_token = self if not (self.is_aux and not any(t.lemma_ == 'be' for t in self.head.children)) else self.head
			s.extend([
				t for t in ref_token.children if t.dep_ in OBJ_DEPS	
			])
		
		# attrs only really count as subjectss
		# if they have a correlate with a real
		# subject. so if everything is attr,
		# then we don't really have a subject
		# but instead a SC or something like that
		# this also happens if spaCy misparses stylistic
		# inversion, but that's rare and we don't want it anyway
		if all(t.dep_ == 'attr' for t in s):
			return None
		
		if len(s) == 1:
			return s[0]
		elif len(s) > 1:
			return sorted(s, key=lambda t: t.i)
	
	@property
	def has_subject(self) -> bool:
		'''Does the token have any subject(s)?'''
		return True if self.subject else False
	
	@property
	def has_object(self) -> bool:
		'''Does the token have any object(s)?'''
		return True if self.object else False

	@property
	def is_transitive(self) -> bool:
		'''Is the token transitive?'''
		return True if self.has_subject and self.has_object else False
	
	@property
	def is_intransitive(self) -> bool:
		'''Is the token intransitive?'''
		return not self.is_transitive	
	
	@property
	def _morph_to_dict(self) -> Dict[str,str]:
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
		return '|'.join(['='.join([str(k), str(v)]) for k, v in d.items()])
	
	def set_morph(self, **kwargs) -> Dict:
		'''
		Set/update morphs using kwargs.
		Use kwarg=None to remove a property.
		'''
		d = self._morph_to_dict
		d = {**d, **kwargs}
		d = {k: v for k, v in d.items() if v is not None}
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
			raise ValueError(
				f"'{self.text}' can't be renumbered; "
				f"it's a {self.pos_} ({self.tag_}), "
				f"not a numbered det/noun!"
			)
		
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
			self.tag_ = 'NN'
	
	def pluralize(self) -> None:
		'''Make a (NOUN) token plural.'''
		if not self.get_morph('Number') == 'Plur':
			self.text = PLURALIZE_MAP.get(self.text.lower(), pluralize(self.text.lower()))
			self.text = (self.text[0].upper() if self.is_sent_start else self.text[0]) + self.text[1:]
			self.set_morph(Number='Plur')
			self.tag_ = 'NNS'
	
	def reinflect(
		self, 
		number: str = None, 
		tense: str = None, 
		**kwargs: Dict[str,str]
	) -> None:
		'''Reinflect the (VERB) token.'''
		if not self.can_be_inflected:
			raise ValueError(f"'{self.text}' can't be reinflected; it's a {self.pos_} ({self.tag_}), not a finite verb!")
		
		if number is None and tense is None:
			raise ValueError("At least one of {number, tense} must not be None!")
		
		number = self.get_morph('Number') if number is None else number
		tense  = self.get_morph('Tense') if tense is None else tense
		
		# used to cannot be made present tense 
		# (*He uses to, *They use to)
		if (
			self.text == 'used' and 						# used
			any(t.dep_ == 'xcomp' for t in self.children)	# to
			and tense == PRESENT
		):
			raise ValueError(
				f'"{self.text} to" cannot be made present tense!'
			)
		
		# we need to filter out Nones, in case the current word
		# doesn't have these morphs
		c_kwargs = dict(number=NUMBER_MAP.get(number), tense=TENSE_MAP.get(tense))
		c_kwargs = {k: v for k, v in c_kwargs.items() if v is not None}
		c_kwargs = {**c_kwargs, **kwargs}
		
		# first, see if the verb is in the map
		# then, see if the verb's specific number is in the map
		# if not, it's because it's None, so see if the verb's
		# text is in the map with 'any' number (common for past tense)
		# and then get the tense info if it's there 
		if CONJUGATE_MAP.get(self.text, {}).get(c_kwargs.get('number'), {}).get(c_kwargs.get('tense'), {}):
			text = CONJUGATE_MAP[self.text][c_kwargs['number']][c_kwargs['tense']]
		elif CONJUGATE_MAP.get(self.text, {}).get('any', {}).get(c_kwargs.get('tense'), {}):
			text = CONJUGATE_MAP[self.text]['any'][c_kwargs['tense']]
		else:
			text = conjugate(self.text, **c_kwargs)
		
		# if conjugation has produced an empty 
		# string, something has gone wrong
		if not text:
			raise ParseError(
				f'Reinflection of "{self.text}" ({c_kwargs}) '
				 'was unsuccessful!'
			)
		
		# capitalize if we're at the beginning of a sentence
		self.text = text if not self.is_sent_start else (text[0].upper() + text[1:])
		
		n = 'Sing' if NUMBER_MAP.get(number) == SG else 'Plur' if NUMBER_MAP.get(number) == PL else None
		t = 'Past' if TENSE_MAP.get(tense) == PAST else 'Pres' if TENSE_MAP.get(tense) == PRESENT else None
		
		m_kwargs = dict(Number=n, Tense=t)
		if tense == INFINITIVE:
			m_kwargs.update(dict(VerbForm='Inf', Tense=None))
		
		m_kwargs = {**m_kwargs, **kwargs}
		
		self.set_morph(**m_kwargs)
		
		if TENSE_MAP.get(tense) == PAST:
			self.tag_ = 'VBD'
		elif TENSE_MAP.get(tense) == INFINITIVE:
			self.tag_ = 'VB'
		elif TENSE_MAP.get(tense) == PRESENT:
			if NUMBER_MAP.get(number) == SG:
				self.tag_ = 'VBZ'
			elif NUMBER_MAP.get(number) == PL:
				self.tag_ = 'VBP'
	
	def make_past_tense(self, number: str) -> None:
		'''Make the (VERB) token past tense.'''
		self.reinflect(number=number, tense=PAST)
	
	def make_present_tense(self, number: str) -> None:
		'''Make the (VERB) token present tense.'''
		self.reinflect(number=number, tense=PRESENT)
	
	def make_infinitive(self) -> None:
		'''Make the (VERB) token infinitive.'''
		self.reinflect(tense=INFINITIVE)

class EDoc():
	'''
	Wrapper around spaCy Doc to implement useful methods.
	'''
	def __init__(
		self,
		Doc: Doc = None, 
		s: str = None, 
		previous: 'EDoc' = None
	) -> 'EDoc':
		'''Creates an EDoc wrapper around a spaCy Doc.'''
		if s is None and Doc is None:
			raise ValueError('At least one of s or Doc must be specified!')
		
		if len(set([v for v in [s, Doc] if v is not None])) > 1:
			raise ValueError('At most one of s or Doc may be specified!')
		
		if s is not None:
			Doc = nlp_(s)
		
		self.doc = Doc
		self.vocab = Doc.vocab
		self.user_data = Doc.user_data
		self.previous = previous
		
		# keep the history so we can recreate this object exactly
		# but get it in an informative way that excludes the mostly internal functions
		stack = inspect.stack()
		
		most_recent_call_from_outside_self = [s.function in dir(self) for s in stack].index(False) - 1
		if stack[most_recent_call_from_outside_self].function == '__init__':
			most_recent_call_from_outside_self += 1
		
		stack = stack[most_recent_call_from_outside_self]
		caller_args = inspect.getargvalues(stack.frame)
		non_self_args = inspect.formatargvalues(*[arg if not arg == ['self'] else [] for arg in caller_args])
		
		self.caller_args = non_self_args
		self.caller = stack.function
			
	def __repr__(self) -> str:
		'''Returns a string representation of the EDoc.'''
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
	
	@property
	def history(self) -> None:
		'''Print a string representation of the EDoc's history.'''
		print(self._history.replace(").", ") \\\n    .") + f'\n--> {self}')
	
	@property
	def _history(self) -> str:
		'''Get a string representation of the EDoc's history.'''
		string = ''
		if hasattr(self, 'caller'):
			if hasattr(self, 'previous') and self.previous is not None:
				string += f'{self.previous._history}.'
			
			string += f'{self.caller}{self.caller_args}'
		
		return string
	
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
		heads 		= [t.head.i if not hasattr(t, 'head_i') else t.head_i for t in self]
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
			heads[i]		= t.head.i if not hasattr(t, 'head_i') else t.head_i
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
			ents=ents,
		)
		
		return EDoc(new_s, previous=self)
	
	def _copy_with_remove(
		self,
		indices: Union[int,List[int]],
		move_deps_to: Union[int,List[int]],
	) -> 'EDoc':
		'''
		Creates a copy of the current doc with
		the tokens at the indices removed.
		Dependencies associated with the removed indices
		are update to the location specified in move_deps_to.
		Generally best to avoid; used internally
		for conjunction reduction.
		'''
		indices 	 = [indices] if not isinstance(indices,(list,range)) else indices
		move_deps_to = [move_deps_to] if not isinstance(move_deps_to,(list,range)) else indices
			
		if any(i > (len(self) - 1) for i in indices + move_deps_to):
			raise IndexError(
				f'The current doc is length {len(self)}, so '
				f'there is no token to remove at index >{len(self) - 1}!'
			)
		
		tokens 		= [t for t in self.doc if not t.i in indices]
		vocab 		= self.vocab
		words 		= [t.text for t in tokens]
		
		# if we removed the first token, capitalize the new first token
		if not words[0][0].isupper():
			words[0] = words[0][0].upper() + words[0][1:]
		
		spaces = []
		for t in tokens:
			# if the removed token has no whitespace,
			# we need to remove it from the token that 
			# will now take its place
			if t.i + 1 in indices:
				spaces.append(self[t.i+1].whitespace_ == ' ')
			else:
				spaces.append(t.whitespace_ == ' ')
		
		user_data	= self.user_data
		tags 		= [t.tag_ for t in tokens]
		pos 		= [t.pos_ for t in tokens]
		morphs 		= [str(t.morph) for t in tokens]
		lemmas 		= [t.lemma_ for t in tokens]
		heads 		= [t.head.i if not hasattr(t, 'head_i') else t.head_i for t in self if not t.i in indices]
		
		# have to reduce the head indices for each index we remove
		for i, move_to in zip(indices, move_deps_to):
			heads 	= [h - 1 if h > i else move_to if h == i else h for h in heads]
		
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
		
		return EDoc(new_s, previous=self)
	
	def _copy_with_add(
		self,
		token: EToken,
		index: int,
	) -> 'EDoc':
		'''
		Creates a copy of the current doc with
		tokens added. Generally best to avoid;
		used internally for adding auxes to 
		questions.
		'''
		tokens 		= self[:]
		heads 		= [t.head.i if not hasattr(t, 'head_i') else t.head_i for t in tokens]
		heads 		= [h + 1 if h > index else h for h in heads]
		
		tokens.insert(index, token)
		heads.insert(index, token.head.i if not hasattr(token, 'head_i') else token.head_i)
		
		vocab 		= self.vocab
		words 		= [t.text for t in tokens]
		
		# if we have added to the beginning of the sentence
		# we capitalize the token added and 
		# then decapitalize the next token if possible
		if index == 0:
			words[0] = words[0][0].upper() + words[0][1:]
			if tokens[1].can_be_decapitalized:
				words[1] = words[1][0].lower() + words[1][1:]
		
		# if we have added to a position preceding a no whitespace,
		# remove the punctuation of the added token
		if self[index].whitespace_ == '':
			spaces 	= [t.whitespace_ == ' ' if t.i != index else False for t in tokens]
		else:
			spaces 	= [t.whitespace_ == ' ' for t in tokens]
		
		user_data	= self.user_data
		tags 		= [t.tag_ for t in tokens]
		pos 		= [t.pos_ for t in tokens]
		morphs 		= [str(t.morph) for t in tokens]
		lemmas 		= [t.lemma_ for t in tokens]
		
		deps 		= [t.dep_ for t in tokens]
		sent_starts = [t.is_sent_start for t in tokens]
		sent_starts = [True] + [False for _ in range(len(tokens)-1)]
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
		
		return EDoc(new_s, previous=self)
	
	# CONVENIENCE PROPERTIES
	@property
	def polarity(self) -> str:
		'''Is main clause positive or negative?'''
		return self.main_verb.polarity
	
	@property
	def is_positive(self) -> bool:
		'''Is the main clause positive?'''
		return self.polarity == 'Pos'
	
	@property
	def is_negative(self) -> bool:
		'''Is the main clause negative?'''
		return self.polarity == 'Neg'
	
	@property
	def root(self) -> EToken:
		'''Get the root node (i.e., main verb) of s.'''
		try:
			return [t for t in self if t.dep_ == 'ROOT'][0]
		except IndexError:
			return None
	
	@property
	def root_is_verb(self) -> bool:
		'''
		Is the root a verb or aux?
		This is False if spaCy messed up.
		'''
		if self.root:
			return self.root.is_verb or self.root.is_aux
		else:
			return False
	
	@property
	def main_verb(self) -> EToken:
		'''Gets the tensed main verb.'''
		if self.root_is_verb:
			v = self.root
			# in questions and/or passives, the root is the non-inflected verb, but we want the aux
			# this also happens with stacked auxiliaries (i.e., would be, would have been, etc.)
			while any(t for t in v.children if t.dep_ in ['auxpass', 'aux']):
				v = [t for t in v.children if t.dep_ in ['auxpass', 'aux']][0]
			
			return v
		else:
			return None
	
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
		return True if self.main_subject else False
	
	@property
	def main_subject(self) -> Union[EToken,List[EToken]]:
		'''Gets the main clause subject of the SDoc if one exists.'''
		v = self.main_verb
		if v is None:
			return None
		
		s = v.subject
		
		# missing subject due to sentence fragments
		# or misparses
		if s is None:
			return None
		
		# now that we know we have something
		# handle extensions and edge cases
		if not isinstance(s,list):
			s = [s]
		
		s.extend(self._get_conjuncts(s[0]))
		
		if len(s) == 1:
			s = s[0]
			# this is a weird bug spaCy has
			# about hyphenated verbs
			if s.text in VERB_PREFIXES:
				s = [t for t in s.children if t.dep_ in SUBJ_DEPS.union({'compound'})]
				s.extend(self._get_conjuncts(s[0]))
				if len(s) == 1:
					s = s[0]
		
		if isinstance(s,list):
			s = sorted(s, key=lambda t: t.i)
		
		return s
	
	@property
	def main_subject_number(self) -> str:
		'''Gets the number feature of the main clause subject.'''
		s = self.main_subject
		
		if self.main_verb.get_morph('Number'):
			# trust the inflection of the verb if it exists
			return self.main_verb.get_morph('Number')
		else:
			return self._get_noun_number(s)
	
	@property
	def _main_subject_index(self) -> int:
		'''What is the final index of the main subject?'''
		s = self.main_subject
		if isinstance(s, list):
			s_loc = max([subj.i for subj in s]) + 1
		elif s is None:
			s_loc = None
		else:
			s_loc = s.i + 1
		
		return s_loc
	
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
	
	@property
	def main_subject_determiner(self) -> Union[EToken,List[EToken]]:
		'''Get the determiner(s) of the main subject.'''
		s = self.main_subject
		if isinstance(s, list):
			d = [t.determiner for t in s]
		else:
			d = s.determiner
		
		return d
	
	@property
	def main_subject_verb_interveners(self) -> List[EToken]:
		'''
		Get the tokens for the nouns that 
		intervene between the head noun(s)
		of the main subject and the main verb.
		'''
		s = self.main_subject
		if not isinstance(s,list):
			s = [s]
		
		if any(t.text in ALL_PARTITIVES for t in s):
			parts = [t for t in s if t.text in ALL_PARTITIVES]
			s.extend(self._get_partitive_head_noun(part) for part in parts)
			s = flatten(s)
			
			s_loc = max(t.i for t in s)
			
			if s_loc is None:
				return []
		else:
			s_loc = self._main_subject_index
			if s_loc is None:
				return []
		
		# we only consider interveners
		# that occur before the verb
		# for now
		v_loc = self.main_verb.i
		if s_loc + 1 >= v_loc:
			return []
		
		interveners = [t for t in self[s_loc+1:v_loc]]
		if interveners:
			interveners += [None]
			# something is only really an intervener if
			# (i)   it has a different tag from the next thing
			# (ii)  it is a noun (NOUN or PROPN)
			# (iii) it is not a direct child of the subject
			# 		(which happens with compounds)
			# (iv)	it is not part of a compound noun (since
			# 		only the head of the compound should count)
			# (v)	it is not the head of a partitive (whose
			#		number features don't really count)
			# we use the indices to check for children since
			# the children generator returns a copy rather than
			# a reference
			interveners = [
				t for i, t in enumerate(interveners[:-1])
				if (
					interveners[i+1] is None or
					interveners[i+1].tag_ != t.tag_ and
					interveners[i+1].pos_ != t.pos_
				) and 
				t.pos_ in ['NOUN', 'PROPN'] and
				not t.dep_ in ['compound', 'nmod'] and 
				not (
					(
						t.text in PARTITIVES_WITH_P.union(PARTITIVES_OPTIONAL_P) and
						any(word.text in PARTITIVES_P_MAP.get(word.text, ['of']) for word in t.children)
					) and 
					(
						t.text in PARTITIVES_WITH_INDEFINITE_ONLY and
						t.determiner and 
						isinstance(t.determiner,list) and 
						not any(word.get_morph('Definite') == 'Ind' for word in t.determiner)
					) and 
					(
						t.text in PARTITIVES_WITH_INDEFINITE_ONLY and
						t.determiner and 
						not isinstance(t.determiner,list) and 
						not t.determiner.get_morph('Definite') == 'Ind'
					) and 
					(
						t.text in PARTITIVES_OPTIONAL_P and 
						any(t.children)
					)
				)
			]
		
		return interveners
	
	@property
	def has_main_subject_verb_interveners(self) -> bool:
		'''Do any nouns come between the main subject and its verb?'''
		return any(self.main_subject_verb_interveners)
	
	@property
	def main_subject_verb_intervener_structures(self) -> List[str]:
		'''What structure is each intervener embedded in?'''
		s = self.main_subject
		if isinstance(s,list):
			s = s[-1]
		
		d = self.main_subject_verb_interveners
		
		if d:
			d_dep_seqs = []
			for intervener in d:
				path = self._get_path(fr=intervener, to=s)
				path = [t for t in path if not t.i == s.i]
				if path:
					d_dep_seqs.append(list(dict.fromkeys([STRUCTURE_MAP.get(t.dep_, t.dep_) for t in path])))
				else:
					path = self._get_path(fr=intervener, to=self.root)[:-1]
					d_dep_seqs.append(list(dict.fromkeys([STRUCTURE_MAP.get(t.dep_, t.dep_) for t in path])))
			
			d_dep_seqs = [
				[dep for dep in dep_seq if not dep in EXCLUDE_DEPS]
				for dep_seq in d_dep_seqs
			]
			
			d_dep_seqs = [
				','.join(list(dict.fromkeys(dep_seq)))
				for dep_seq in d_dep_seqs
					if len(dep_seq) > 0
			]
			
			return d_dep_seqs
	
	@property
	def main_subject_verb_final_intervener_structure(self) -> str:
		'''What structure is the final intervener embedded in?'''
		d = self.main_subject_verb_intervener_structures
		if d:
			return d[-1]
	
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
		# assume singular if the morph for number doesn't exist
		distractors = [t for t in interveners if (t.get_morph('Number') or 'Sing') != n]
		return distractors
	
	@property
	def has_main_subject_verb_distractors(self) -> bool:
		'''Are there any distractors between the main clause subject and the main clause verb?'''
		return any(self.main_subject_verb_distractors)
	
	@property
	def main_subject_verb_distractor_structures(self) -> List[str]:
		'''What structure is each distractor embedded in?'''
		s = self.main_subject
		if isinstance(s,list):
			s = s[-1]
		
		d = self.main_subject_verb_distractors
		
		if d:
			d_dep_seqs = []
			for intervener in d:
				path = self._get_path(fr=intervener, to=s)
				path = [t for t in path if not t.i == s.i]
				if path:
					d_dep_seqs.append(list(dict.fromkeys([STRUCTURE_MAP.get(t.dep_, t.dep_) for t in path])))
				else:
					path = self._get_path(fr=intervener, to=self.root)[:-1]
					d_dep_seqs.append(list(dict.fromkeys([STRUCTURE_MAP.get(t.dep_, t.dep_) for t in path])))
			
			d_dep_seqs = [
				[dep for dep in dep_seq if not dep in EXCLUDE_DEPS]
				for dep_seq in d_dep_seqs
			]
			
			d_dep_seqs = [
				','.join(list(dict.fromkeys(dep_seq))) 
				for dep_seq in d_dep_seqs
					if len(dep_seq) > 0
			]
			
			return d_dep_seqs
	
	@property
	def main_subject_verb_final_distractor_structure(self) -> str:
		'''What structure is the final distractor embedded in?'''
		d = self.main_subject_verb_distractor_structures
		if d:
			return d[-1]	
	
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
	def main_object(self) -> Union[EToken,List[EToken]]:
		v = self.main_verb
		s = v.object
		
		if s is not None:
			if not isinstance(s,list):
				s = [s]
			
			s.extend(self._get_conjuncts(t) for t in s[:])
			s = flatten(s)
			
			if len(s) == 1:
				s = s[0]
			
			if isinstance(s,list):
				s = sorted(s, key=lambda t: t.i)
			
			return s
	
	@property
	def main_object_determiner(self) -> Union[EToken,List[EToken]]:
		'''Get the determiner(s) of the main object.'''
		o = self.main_object
		if isinstance(o, list):
			d = [t.determiner for t in o]
		else:
			d = o.determiner
		
		return d
	
	@property
	def main_object_number(self) -> str:
		'''
		What is the number of the main object of the verb?
		Returns None if there is no object.
		'''
		if self.has_main_object:
			o = self.main_object
			if isinstance(o,list) and len(o) > 1:
				return self._get_list_noun_number(o, deps=OBJ_DEPS)
			elif o.text in ALL_PARTITIVES:
				return self._get_partitive_noun_number(o, deps=OBJ_DEPS)
			else:
				return self._get_noun_number(o, deps=OBJ_DEPS)
	
	@property
	def has_main_object(self) -> bool:
		'''Does the sentence have an object of the main verb?'''
		return True if self.main_object else False
	
	@property
	def is_transitive(self) -> bool:
		'''Is the sentence('s main verb) transitive?'''
		return self.has_main_object
	
	@property
	def is_intransitive(self) -> bool:
		'''Is the sentence('s main verb) intransitive?'''
		return not self.is_transitive
	
	@property
	def pos_seq(self) -> List[str]:
		'''Get the part of speech sequence of the sentence.'''
		return [t.pos_ for t in self] 
	
	@property
	def tag_seq(self) -> List[str]:
		'''Get the tag sequence of the sentence.'''
		return [t.tag_ for t in self]
	
	@property
	def main_clause_verbs(self) -> List[EToken]:
		'''Get all the verbs in the main clause of the sentence.'''
		v = self.main_verb
		vs = [v] + [t for t in self._get_conjuncts(v) if t.is_aux or t.is_verb]
		if self.main_verb.is_aux:
			vs = vs + self._get_conjuncts(self.root)
		
		for v in vs:
			vs.extend([t for t in self._get_conjuncts(v) if t.is_aux or t.is_verb])
		
		for i, v in enumerate(vs):
			if any(t for t in v.children if t.dep_ in ['aux', 'auxpass']):
				vs[i] = [t for t in v.children if t.dep_ in ['aux', 'auxpass']][0]
		
		# remove any duplicates by indices
		unique_indices = set(t.i for t in vs)
		deduped_vs = []
		for i in unique_indices:
			verbs = [t for t in vs if t.i == i and (t.is_aux or t.is_verb)]
			if verbs and not any(t.i == i for t in deduped_vs):
				deduped_vs.append(verbs[0])
		
		vs = sorted(deduped_vs, key = lambda t: t.i)
		# we could also technically add 'VBN' here, since those are also
		# non-finite. however, spaCy frequently misparses conjoined main
		# verbs as VBNs, so we want to include them. if we're making
		# a question using these verbs, the misparsing SHOULD throw an
		# error, so don't try to silence it here!
		vs = [v for v in vs if not v.tag_ == 'VBG']
		
		return vs
		
	@property
	def can_form_polar_question(self) -> bool:
		'''Can the sentence form a polar question?'''
		
		# can only make questions from sentences 
		# that aren't already questions
		# and are parsed correctly
		if not self[-1].text in ['.', '!'] or self[-1].dep_ != 'punct':
			return False
		
		vs = self.main_clause_verbs
		
		# ungrammatical sentences
		# lack a main clause verb
		if not vs:
			return False
		
		# we're not doing contracted verbs now
		if any(v.text.startswith("'") for v in vs):
			return False
		
		# spaCy sometimes misparses non-restrictive
		# relative clauses as conjunctions
		# get the subject of each verb and ensure it's
		# not the head of a non-restricted relative
		ss = []
		for v in vs:
			s = v.subject
			if s and self._can_be_inverted_subject(s, v):
				ss.append(s)
			elif s and not self._can_be_inverted_subject(s, v):
				return False
			else:
				next_v = v
				limit = 0
				while not next_v.subject:
					next_v = next_v.head
					# we've reached the root but still haven't found
					# a subject, so break
					if next_v.dep_ == 'ROOT':
						return False
					
					limit += 1
					if limit > LOOK_FOR_SUBJECTS_LIMIT:
						log.warn(
							f'Could not find a subject for "{v}" in "{self}" '
							f'within {LOOK_FOR_SUBJECTS_LIMIT}!'
						)
						return False
				
				if self._can_be_inverted_subject(next_v.subject, next_v):
					ss.append(next_v.subject)
				else:
					return False
		
		ss = flatten(ss)
		ds = flatten([s.determiner for s in ss if s.determiner is not None])
		if any(s.text == 'which' for s in ss + ds):
			return False
		
		# misparses
		if any(t.get_morph('VerbForm') == 'Inf' for t in vs):
			return False
		
		# sometimes spaCy identifies a non-finite verb
		# as a main clause verb, due to misparsing
		# if the sentence is misparsed, we won't be able
		# to make a question out of it reliably
		if any(not t.can_be_inflected for t in vs if not t.is_aux):
			# cannot_be_inflected = [t for t in vs if not t.can_be_inflected and t.tag_ == 'VBN']
			# log.info(
			# 	f'"{self}" cannot be made into a polar question because it contains '
			# 	f'non-finite main clause verb(s): "{",".join([t.text for t in cannot_be_inflected])}" '
			# 	f'({",".join([t.tag_ for t in cannot_be_inflected])})! '
			# 	f'This is probably because it is ungrammatical or was parsed incorrectly.'
			# )
			return False
		
		# we need to make sure that all of the main clause
		# verbs that share a subject would use the same auxiliary
		# to form a question
		all_v_lemmas = {}
		for v in vs:
			# run up the tree until we find the verb's subject
			tmp_v = v
			limit = 0
			while not tmp_v.subject:
				tmp_v = tmp_v.head
				limit += 1
				if limit > LOOK_FOR_SUBJECTS_LIMIT:
					log.warn(
						f'Could not find a subject for "{v}" in "{self}" '
						f'within {LOOK_FOR_SUBJECTS_LIMIT}!'
					)
					return False
			
			# get the first subject position for that verb
			tmp_subject = tmp_v.subject
			if isinstance(tmp_subject,list):
				tmp_subject = sorted(tmp_subject, key=lambda t: t.i)[0]
			
			# record the position of that subject 
			# and the auxiliary associated with its verb
			all_v_lemmas[tmp_subject.i] = (
				all_v_lemmas
					.get(tmp_subject.i, set())
					.union({f'{v.lemma_}_{v.pos_}' if v.is_aux else 'do_AUX'})
			)
		
		# if any one subject would require more than
		# one aux, we cannot form a polar question
		# e.g., He can go and would be happy. -/-> *Can he go and would be happy?
		# in this case, it would have to be He can go and he would be happy. --->
		# Can he go and would he be happy?
		for i in all_v_lemmas:
			if len(all_v_lemmas[i]) > 1:
				# log.info(
				# 	f'"{self}" cannot be made into a question '
				# 	f'because multiple auxiliaries would be required for '
				# 	f'subject "{self[i]}" at position {i} ({", ".join(all_v_lemmas[i])})!'
				# )
				return False
		
		return True
	
	def _get_partitive_head_noun(self, t: Union[Token,EToken]) -> Union[EToken,List[EToken]]:
		'''Get the head noun of a partitive.'''
		if not t.text in ALL_PARTITIVES:
			raise ValueError(
				f'Cannot get the head of a non-partitive noun "{t}"!'
			)
		
		def get_of_head_noun(t: EToken) -> Union[EToken,List[EToken]]:
			'''Get the head noun of a partitive that has of.'''
			if any(t.text in PARTITIVES_P_MAP.get(t.text, ['of']) for t in t.children):
				head_noun = [t for t in t.children if t.text in PARTITIVES_P_MAP.get(t.text, ['of'])][0]
				head_noun = list(head_noun.children)
				# X of the most Y of the Z, where Y is an ADJ
				# we only do this for partitives, because otherwise
				# it is ambiguous (e.g., "The most notable of the people" could
				# refer to one person or to many, but "Some of the most notable of the people"
				# can only be plural)
				# if (
				# 	all(t.pos_ == 'ADJ' for t in head_noun) and 
				# 	(
				# 		any(w.text == 'most' for t in head_noun for w in t.children) or
				# 		any(t.get_morph('Degree') == 'Sup' for t in head_noun)
				# 	)
				# ):
				# 	if any(w.text == 'of' for t in head_noun for w in t.children):
				# 		head_noun = [w for t in head_noun for w in t.children if w.text == 'of'][0]
				# 		head_noun = list(head_noun.children)
				# 	else:
				# 		head_noun = [t]
				
				for t in head_noun[:]:
					head_noun.extend(self._get_conjuncts(t))
			else:
				head_noun = t
			
			if isinstance(head_noun,list) and len(head_noun) == 1:
				# this is tricky: 
				#	we want to properly deal with things like "Some of the smartest of the group" (plur)
				# 	and "Some of the cleanest "
				# if head_noun[0].text in ALL_PARTITIVES and any(t.text == 'of' for t in head_noun[0].children):
				# 	# we land here in weird cases like
				# 	# "some of the smartest of the group"
				# 	return t
				# else:
				return head_noun[0]
			
			return head_noun
		
		if t.text in PARTITIVES_WITH_P:
			return get_of_head_noun(t)
						
		if t.text in PARTITIVES_OPTIONAL_P:
			if any(t.text in PARTITIVES_P_MAP.get(t.text, ['of']) for t in t.children):
				return get_of_head_noun(t)
			else:
				return [t for t in t.children if t.pos_ in NOUN_POS_TAGS]
		
		# this covers cases like "a lot of people are/the money is"
		# this is surprisingly tricky to do straightforwardly!
		if t.text in PARTITIVES_WITH_INDEFINITE_ONLY:
			s_det = [t for t in t.children if t.dep_ == 'det']
			if s_det and s_det[0].get_morph('Definite') == 'Ind':
				return get_of_head_noun(t)
		
		return t
	
	def _get_conjuncts(self, t: Union[Token,EToken]) -> List[EToken]:
		'''Returns all conjuncts dependent on the first in a coordinated phrase.'''
		conjuncts = [t for t in t.rights if t.dep_ == 'conj']
		for i, c in enumerate(conjuncts[:]):
			if c.text in ALL_PARTITIVES:
				# the next line addresses cases when spaCy parses the
				# partitive as the noun to which others bear a conj dependency
				# we want those nouns, but not the partitive head noun itself
				conjuncts.extend(self._get_conjuncts(c))
				conjuncts[i] = self._get_partitive_head_noun(c)
		
		conjuncts = flatten(conjuncts)
		
		for c in conjuncts[:]:
			conjuncts.extend(
				t 
				for t in self._get_conjuncts(c) 
					if not any(t.i == t2.i for t2 in conjuncts)
			)
		
		return conjuncts
	
	def _get_noun_number(self, s: EToken, deps: List[str] = SUBJ_DEPS) -> str:
		'''Handles special logic for getting noun number.'''
		if s is None:
			# default value if no noun is passed
			return 'Sing'
		elif isinstance(s,list) and len(s) > 1:
			# if the subject is a list, there could be many reasons
			# so we have a special function to deal with that
			return self._get_list_noun_number(s, deps=deps)
		elif s.is_verb and not s.can_be_inflected:
			# gerunds and nominal verbs are grammatically singular
			return 'Sing'
		elif (
			s.dep_ in ['csubj', 'csubjpass'] or 
			(s.dep_ in OBJ_DEPS and s.tag_ in ['WP', 'WD', 'WDT'])
		):	# clausal subjects/object are not correctly associated
			# with a Singular number feature
			return 'Sing'
		# this isn't actually true, since these can be used with ellipsis
		# for mass nouns
		# elif s.text in ['Some', 'some', 'Any', 'any'] and s.dep_ != 'det':
		# 	# when 'some' or 'any' are dets, they can be singular or plural
		# 	# but when they are the head noun, it should be plural
		# 	return 'Plur'
		elif s.text in ALL_PARTITIVES:
			# special logic here, so a separate function
			return self._get_partitive_noun_number(s)
		elif (
			s.determiner and
			isinstance(s.determiner,list) and
			any(t for t in s.determiner if t.tag_ in DET_TAGS) and
			[t for t in s.determiner if t.tag_ in DET_TAGS][0].get_morph('Number') and
			not [t for t in s.determiner if t.tag_ in DET_TAGS][0] in ALL_PARTITIVES
		):	# this happens with "all the ...", which tags 'all' as 'PDT'
			# we also want to account for single cases of 'all ...', where it is partitive,
			# so don't use a determiner if it is a partitive, even if it has a number feature
			# in this case, we want to treat all as a partitive and NOT use its number
			# as the number of the subject
			return [t for t in s.determiner if t.tag_ in DET_TAGS][0].get_morph('Number')
		elif (
			s.determiner and 
			not isinstance(s.determiner,list) and 
			s.determiner.get_morph('Number') and 
			s.determiner.tag_ in DET_TAGS and 
			not s.determiner.text in ALL_PARTITIVES
		):	# if there is a helpful determiner that isn't a list
			# that has a number feature (i.e., 'these')
			# and it isn't a partitive (since some partitives
			# have default number features, which shouldn't override
			# the noun's number)
			return s.determiner.get_morph('Number')
		elif (
			s.text in PLURALS_WITH_NO_DETERMINERS and 
			(
				not s.determiner or 
				(
					not isinstance(s.determiner,list) and 
					s.determiner.text == 'all'
				)
			)
		):	# some nouns have the same singular and plural forms
			# but when they have no determiner, they are always plural
			# if they are a count noun. 'all' is exceptional
			# because if it occurs with one of these special nouns, 
			# it is always plural. ('some' is ambiguous)
			return 'Plur'
		elif s.get_morph('Number'):
			# turns out just about the last thing we want to do is trust
			# the number feature spaCy assigns. go figure
			return s.get_morph('Number')
		elif s.pos_ == 'ADJ' and s.text in NUMBERS_FOR_ADJECTIVES_USED_AS_NOUNS:
			return NUMBERS_FOR_ADJECTIVES_USED_AS_NOUNS[s.text]
		else:
			# usually we end up here because of adjectives serving
			# as nouns (the latter, etc.), or genuine ambiguity 
			# (neither is/are, etc.)
			log.warning(
				f'No number feature for "{s}" was found in "{self}"! '
				 "I'm going to guess it's singular, but this may be wrong!"
			)
			return 'Sing'
	
	def _get_partitive_noun_number(self, s: EToken, deps: List[str] = SUBJ_DEPS) -> str:
		'''Returns the number of a partitive subject.'''
		# this currently covers cases like "some of the (schools are/group is) unsure..."
		def process_head_noun(head_noun: EToken) -> str:
			'''
			If there is a single head noun,
			return its number morph. Otherwise,
			get the number feature of the multiple
			head nouns.
			'''
			if isinstance(head_noun,list) and len(head_noun) == 1:
				return process_default(head_noun[0])
			elif not isinstance(head_noun,list):
				return process_default(head_noun)
			else:
				return self._get_list_noun_number(head_noun, deps=deps)
		
		def process_default(s: EToken) -> str:
			'''
			If we can't find the special things that make
			partitives partitives, we do some default processing
			here. Return the number of the token if it exists,
			otherwise assume singular.
			'''
			d = s.determiner
			if not isinstance(d,list):
				d = [d] if d is not None else []
			
			if (
				s.text in ['number'] and 
				any(t.get_morph('Definite') == 'Ind' for t in d) and
				any(t.text in PARTITIVES_P_MAP.get(t.text, ['of']) for t in s.children)
			):
				# number is special: it can only be used as
				# plurals when it is the head noun of a partitive
				# this occurs when there is an "of" phrase, but no number
				# information can be found inside of it (e.g., "a number of the most
				# prominent...")
				return 'Plur'
			elif (
				s.pos_ == 'ADJ' and
				(
					any(t.text == 'most' for t in s.children) or
					s.get_morph('Degree') == 'Sup'
				)
			): 	# a number of the most notable, some of the most notable ...
				return 'Plur'
			elif s.get_morph('Number'):
				return s.get_morph('Number')
			elif s.text in ['Some', 'some', 'Any', 'any']:
				# we end up here if we have 'some' as a subject
				# of a copular sentence. like "some were discarded buses,
				# rais carriages."
				return 'Plur'
			elif s.is_verb and not s.can_be_inflected:
				# gerunds and nominalized verbs are singular
				return 'Sing'
			elif (
				d and
				any(t for t in d if t.tag_ in DET_TAGS) and
				[t for t in d if t.tag_ in DET_TAGS][0].get_morph('Number') and
				not [t for t in d if t.tag_ in DET_TAGS][0] in ALL_PARTITIVES
			):	# this happens with "all the ...", which tags 'all' as 'PDT'
				# we also want to account for single cases of 'all ...', where it is partitive,
				# so don't use a determiner if it is a partitive, even if it has a number feature
				# in this case, we want to treat all as a partitive and NOT use its number
				# as the number of the subject
				return [t for t in d if t.tag_ in DET_TAGS][0].get_morph('Number')
			# elif (
			# 	s.determiner and 
			# 	not isinstance(s.determiner,list) and 
			# 	s.determiner.get_morph('Number') and 
			# 	s.determiner.tag_ in DET_TAGS and 
			# 	not s.determiner.text in ALL_PARTITIVES
			# ):	# if there is a helpful determiner that isn't a list
			# 	# that has a number feature (i.e., 'these')
			# 	# and it isn't a partitive (since some partitives
			# 	# have default number features, which shouldn't override
			# 	# the noun's number)
			# 	return s.determiner.get_morph('Number')
			else:
				log.warning(
					f'No number feature for "{s}" was found in "{self}"! '
					 "I'm going to guess it's singular, but this may be wrong!"
				)
				return 'Sing'
		
		if s.text in ALL_PARTITIVES:
			head_noun = self._get_partitive_head_noun(s)
			if head_noun:
				return process_head_noun(head_noun)
			else:
				return process_default(s)
		
		raise ValueError(
			"_get_partitive_noun_number should only "
			"be called with a subject that could be a partitive!"
		)
	
	def _get_list_noun_number(self, s: List[EToken], deps: List[str] = SUBJ_DEPS) -> str:
		'''
		We call this to get the number of the subject when
		there are multiple subject dependencies in a sentence.
		This happens with expletive 'it' subjects, some copular
		sentences, and sentences with conjoined subjects.
		'''
		# failsafe
		if len(s) == 1:
			return self._get_noun_number(s[0])
		
		tag_counts = Counter([t.dep_ for t in s])
		# happens with some dummy 'it' subject sentences
		# and some copular sentences
		# one subject and one attr
		if any(tag_counts[dep] == 1 for dep in deps) and tag_counts['attr'] == 1:
			nums = [t.get_morph('Number') if not (t.is_verb and t.can_be_inflected) else 'Sing' for t in s]
			# if all the subjects are singular and we have one attr
			# and one nsubj, then the subject is singular
			if all([n == 'Sing' for n in nums]):
				return 'Sing'
			# this happens in weird cases like
			# "the best thing were the movies we watched..."
			# or partitives "Some of the best people were..."
			# in this case, we just go with the verb number if possible
			# since that is less likely to be errorful.
			# otherwise, choose the first number feature that exists
			# in a subject noun. If none exists, use singular as a default
			else:
				# we only trust the verb number if we have a subject noun
				# since objects don't agree
				if deps == SUBJ_DEPS:
					if self.main_verb.get_morph('Number'):
						return self.main_verb.get_morph('Number')
					
				if s[0].text in ALL_PARTITIVES:
					return self._get_partitive_noun_number(s[0])
				
				for subj in s:
					if subj.get_morph('Number'):
						return subj.get_morph('Number')
				else:
					log.warning(
						f'No token in "{s}" has a number feature! ({self}) '
					 	f"I'm going to guess it's singular, but this may be wrong!"
					)
					return 'Sing'
		elif tag_counts['expl'] == 1 and any(tag_counts[dep] == 1 for dep in OBJ_DEPS):
			# this happens when spaCy has misparsed an unaccusative with there inversion
			d = [d for d in OBJ_DEPS if tag_counts[d] == 1 and not d == 'expl']
			s = [t for t in s if t.dep_ in d]
			if len(s) == 1:
				s = s[0]
				return self._get_noun_number(s)
			else:
				return self._get_list_noun_number(s)
		else:
			# conjoined subjects (i.e., and, or, etc.)
			return 'Plur'
	
	def _get_path(self, fr: Union[Token,EToken], to: Union[Token,EToken]) -> List[Union[Token,EToken]]:
		'''
		Get the dependency path linking two (E)Tokens.
		If no path exists, return an empty list.
		'''
		path = [fr]
		if fr.i == to.i:
			return path		
		elif fr.head.i == to.i:
			path.append(to)
			return path
		elif fr.head.i == fr.i:
			return []
		else:
			ext_path = self._get_path(fr.head, to)
			if ext_path is None:
				return []
			else:
				path.extend(ext_path)
				return path
	
	# CONVENIENCE METHODS.
	# These return new objects; they do NOT modify in-place.
	def reinflect_main_verb(
		self, 
		number: str, 
		tense: str, 
		conjoined: bool = True,
		**kwargs
	) -> 'EDoc':
		'''Reinflect the main verb.'''
		# get conjoined verbs and reinflect those too
		# this can be easily turned off
		if not self.main_verb.can_be_inflected or self.main_verb.get_morph('VerbForm') == 'Inf':
			raise ValueError(
				f'The main verb "{self.main_verb}" of "{self}" is non-finite! '
				f'This is usually due to the sentence being ungrammatical, '
				f'or because spaCy misparsed something. Unable to reinflect.'
			)
		
		if conjoined:
			# conj_vs = [t for t in v.children if t.dep_ == 'conj' and t.can_be_inflected]
			# # don't reinflect conjoined verbs if they have their own subjects
			# conj_vs = [
			# 	[v]
			# 	if v.can_be_inflected and not v.has_subject
			# 	else [
			# 		t for t in v.children 
			# 		if 	t.dep_ in ['aux', 'auxpass'] and 
			# 			t.can_be_inflected and 
			# 			not v.has_subject
			# 		]
			# 	for v in conj_vs
			# ]
			# all_vs = [v] + [i for s in conj_vs for i in s]
			all_vs = self.main_clause_verbs
		else:
			all_vs = [self.main_verb]
			
		# in questions, can't change make present if 
		# main verb is "used to" (*Does/do he/they use to...?)
		# the EToken object catches this if it is a sentence,
		# but it can't when it is a question because "use to" is 
		# possible as an infinitive: ('Did he use to go?')
		if any(
			v.lemma_ == 'do' and 								# did
			v.is_aux and 										# Q
			v.head.text in ['use', 'used'] and					# used/use
			any(t.dep_ == 'xcomp' for t in v.head.children) and	# to
			tense == PRESENT									# cannot make present tense
			for v in all_vs
		):
			raise ValueError(
				f'Cannot make "{self}" present tense because '
				f'"{v.head.text} to" cannot be present tense!'
			)
		
		# this will allow us to account for contractions
		whitespaces_modified = []
		
		for v in all_vs:
			if not TENSE_MAP.get(v.get_morph('Tense')) == TENSE_MAP[tense]:
				# handle contractions
				starts_with_apostrophe = v.text.startswith("'")
				if (v.text in HOMOPHONOUS_VERBS and HOMOPHONOUS_VERBS[v.text]['condition'](v)):
					if any(kwargs.keys()):
						log.warning(
							f'{v.text} is homophonous to another verb. ' 
							f'Kwargs {kwargs} will be not be used for '
							 'reinflection to attempt to get the right behavior '
							 'though they will be added to the morphology.'
						)
					
					m_number = 'Sing' if NUMBER_MAP.get(number) == SG else 'Plur'
					m_tense  = 'Pres' if TENSE_MAP.get(tense) == PRESENT else 'Past'
					
					d_number = 'singular' if number == 'Sing' else 'plural'
					d_tense = 'present' if tense == PRESENT else 'past'
					
					morph_kwargs = {'Number': m_number, 'Tense': m_tense, **kwargs}
					morph_kwargs = {k: v for k, v in morph_kwargs.items() if v is not None}
					
					if HOMOPHONOUS_VERBS[v.text].get(d_number, {}).get(d_tense, {}):
						v.text = HOMOPHONOUS_VERBS[v.text][d_number][d_tense]
						v.set_morph(**morph_kwargs)
					elif HOMOPHONOUS_VERBS[v.text].get('any', {}).get(d_tense, {}):
						v.text = HOMOPHONOUS_VERBS[v.text]['any'][d_tense]
						v.set_morph(**morph_kwargs)
					else:
						v.reinflect(number, tense, **kwargs)
				else:
					v.reinflect(number, tense, **kwargs)
				
				# if we've removed an apostrophe, we need 
				# to add a space after the preceding word
				if starts_with_apostrophe and not v.text.startswith("'"):
					before_word = self[v.i-1]
					before_word.whitespace_ = ' '
					whitespaces_modified.append(before_word)
				
		return self.copy_with_replace(tokens=all_vs + whitespaces_modified)
	
	def make_main_verb_past_tense(self) -> 'EDoc':
		'''Convert the main verb to past tense.'''
		vs = self.main_clause_verbs
		
		if all(v.get_morph('Tense') == 'Past' for v in vs):
			return self
		
		n = self.main_subject_number
		return self.reinflect_main_verb(number=n, tense=PAST)
	
	def make_main_verb_present_tense(self) -> 'EDoc':
		'''Convert the main verb to present tense.'''
		vs = self.main_clause_verbs
		
		if all(v.get_morph('Tense') == 'Pres' for v in vs):
			return self
		
		n = self.main_subject_number
		return self.reinflect_main_verb(number=n, tense=PRESENT)
	
	def renumber_main_subject(self, number: str) -> 'EDoc':
		'''Renumber the main subject, along with its determiner and verb.'''
		if self.has_conjoined_main_subject and NUMBER_MAP.get(number) == SG:
			edoc = self._remove_conjunctions_to_main_subject()
		elif (
				self.main_subject.text in ALL_PARTITIVES and
				self.has_main_subject_verb_distractors
			):
			# if there is a partitive subject and distractors,
			# it means we are dealing with a plural partitive
			# the best way around that is to delete the partitive
			edoc = self._remove_partitive_from_main_subject()			
		else:
			edoc = self
		
		tokens = []
		
		s = edoc.main_subject
		# at this point, it's because we have a copular sentence,
		# so renumber all args. conjunctions were removed above
		if isinstance(s,list):
			for t in s:
				t.renumber(number=number)
				tokens.append(t)
		else:
			s.renumber(number=number)
			tokens.append(s)
		
		d = edoc.main_subject_determiner
		if d:
			if isinstance(d,list):
				for t in d:
					t.renumber(number=number)
					tokens.append(t)
			else:
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
	
	def _remove_partitive_from_main_subject(self) -> 'EDoc':
		'''
		Return a copy of the current EDoc with all but the
		first noun of a conjoined subject removed. Useful
		when renumbering a sentence with a conjoined subject.
		'''
		# this is tricky because we sometimes want to keep the determiner
		# and sometimes not:
		#     a lot of people are --sing--> a person is (not 'person is')
		#     a lot of the money is --sing--> the money is (not 'a money is')
		# for now let's disallow this
		raise NotImplementedError('Cannot currently renumber sentences with a partitive subject.')
		
		# if not self.main_subject.text in ALL_PARTITIVES:
		# 	return self
		
		# s = self.main_subject
		
		# # remove tokens starting at this position
		# starting_index 	= s.i
		
		# # get the children of the subject
		# s_chi = [t for t in s.children if t.dep_ != 'det']
		# if s_chi:
		# 	s_chi = s_chi[0].children
		
		# if not s_chi:
		# 	# if there are no children, it means the partitive
		# 	# itself determines the number, so there's nothing to change
		# 	return self
		
		# # until this position
		# remove_until 	= min([t.i for t in s_chi]) - 1
		
		# # remove from one after the head of the conjP
		# # until the final position to remove (range() is [x,y))
		# range_to_remove = range(starting_index+1, remove_until+1)
		
		# return self._copy_with_remove(indices=range_to_remove)
	
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
	
	def make_sentence_polar_question(self) -> 'EDoc':
		'''Convert a sentence EDoc into a polar question.'''
		# if we have conjoined multiple clauses, 
		# we need to make each a question separately
		if not self.can_form_polar_question:
			raise ValueError(
				f'"{self}" cannot form a polar question! '
				f'This is usually either due to it already '
				f'being a question, it being a fragment/ungrammatical, '
				f'because spaCy misparsed something, or because it has a '
				f'contracted verb.'
			)
		
		# get the main clause verbs
		# we will loop through them
		# and add/replace each aux as needed
		vs = self.main_clause_verbs
		
		# we start by copying self,
		# and will modify it to make a question	
		question = self
		
		# this keeps track of how many 
		# tokens we've added so we can
		# properly adjust the positions
		# of everything else
		added = 0
		
		for v in vs:
			# if the verb has its own subject, we
			# need to invert them. if not, we don't
			# need to do inversion, just reinflection
			v_has_subject = True
			
			# the verb's subject attribute is recursive
			# but for questions, we don't want that, since
			# we need to know whether the verb
			# has its own subject to properly reorder things
			# so we have to check this manually here
			# exclude things that only have attrs, because 
			# those are "objects" of copular verbs (like become)
			s = [t for t in v.children if t.dep_ in SUBJ_DEPS]
			if all(t.dep_ == 'attr' for t in s):
				s = []
			
			if len(s) == 1:
				s = s[0]
			
			# if we have a chain of auxes, we need to step up through them
			# and see if the final verb has a subject
			next_v = v
			if not s and v.is_aux:
				while next_v.head.is_aux:
					next_v = next_v.head
				
				s = [t for t in next_v.head.children if t.dep_ in SUBJ_DEPS]
			
			if not (s and self._can_be_inverted_subject(s, next_v)):
				v_has_subject = False
				next_v = v
				while not next_v.subject:
					next_v = next_v.head
				
				s = next_v.subject
			
			# save this so we can put the preceding token here
			v_original_index = v.i
			v_original_whitespace_ = v.whitespace_
			
			aux = self._get_aux(v)
			aux.whitespace_ = ' '
			
			# if the verb has a subject,
			# do aux inversion or do-support
			if v_has_subject:
				# inflect the aux
				if aux.can_be_inflected:
					number = v.get_morph('Number')
					person = v.get_morph('Person')
					
					if person is not None:
						person = int(person)
					
					if number is None or person is None:
						s = v.subject
						if isinstance(s,list):
							number = self._get_list_noun_number(s) if number is None else number
							person = 3 if person is None else person
						else:
							if any(self._get_conjuncts(s)):
								s = [s]
								s.extend(self._get_conjuncts(s[0]))
								number = self._get_list_noun_number(s) if number is None else number 
								person = 3 if person is None else person
								s = s[0]
							elif s.text in ALL_PARTITIVES:
								number = self._get_partitive_noun_number(s) if number is None else number
								person = 3 if person is None else person
							else:
								number = self._get_noun_number(s) if number is None else number
								person = s.get_morph('Person')
								person = int(person) if person else 3
						
					tense = v.get_morph('Tense')
					aux.reinflect(number=number, person=person, tense=tense)
				
				# inversion means putting inserting the aux
				# at the earliest position of the subject
				aux.i = self._get_subject_initial_index(s)
				
				# if the verb is an aux already, we
				# need to set the dependencies of the
				# added aux accordingly
				if v.is_aux and not v.lemma_ == 'get':
					# if the verb is the head, then
					# set the head of aux to itself and
					# it is the root node
					if v.head.i == v_original_index:
						aux.head = aux
						aux.dep_ = 'ROOT'
					else:
						# account for passive auxiliaries,
						# which have existing dependencies
						# try:
						# 	aux.head = self[v.head.i+added+1]
						# except IndexError:
						# if the verb is near the end of the sentence
						# we might be trying to index past the max len
						# which raises IndexError. to get around this, 
						# we'll set a special attr that the copy_with_* 
						# functions will allow to override the actual 
						# index of the head if it exists
						aux.head_i = v.head.i+added+1	
						aux.dep_ = v.dep_
				else:
					try:
						aux.head = self[aux.head.i+added+1]
					except IndexError:
						# if the aux is near the end of the sentence
						# we might be trying to index past the max len
						# which raises IndexError. to get around this, 
						# we'll set a special attr that the copy_with_* 
						# functions will allow to override the actual 
						# index of the head if it exists
						aux.head_i = aux.head.i+added+1
				
				# if we have an n't contraction, we need to get rid of the
				# whitespace following the aux
				if v.is_negative:
					negs = [t for t in v.children if t.dep_ == 'neg']
					negs += [t for t in v.head.children if t.dep_ == 'neg']
					if any(t.text == "n't" for t in negs):
						aux.whitespace_ = ''
				
				# insert the auxiliary
				question =  question._copy_with_add(token=aux, index=aux.i+added)
				added 	 += 1
				
				# if we have an n't contraction, we need to move that with
				# the inverted aux. also deal with "cannot"
				if v.is_negative:
					negs = [t for t in v.children if t.dep_ == 'neg']
					negs += [t for t in v.head.children if t.dep_ == 'neg']
					if any(t.text == "n't" for t in negs):
						neg = [t for t in negs if t.text == "n't"][0]
						neg.head_i = v.head.i+added+1
						question = question._copy_with_add(token=neg, index=aux.i+added)
						added += 1
			
			# if the verb was already an aux, we need to remove
			# the aux in the original position
			if v.is_aux and not v.lemma_ == 'get':
				question =  question._copy_with_remove(indices=v_original_index+added, move_deps_to=aux.i)
				added 	 -= 1
			else:
				# if the verb is not an aux, we need
				# to reinflect it to the infinitive
				# form for do-support
				v.reinflect(tense=INFINITIVE)
				v.set_morph(Number=None, Tense=None, VerbForm='Inf')
				# try: 
				# 	v.head = self[v.head.i+added]
				# except IndexError:
				v.head_i = v.head.i+added
				
				question = question.copy_with_replace(tokens=v, indices=v.i+added)
			
			# if we moved n't, we also need to delete that
			if v.is_negative:
				negs = [t for t in v.children if t.dep_ == 'neg']
				negs += [t for t in v.head.children if t.dep_ == 'neg']
				if any(t.text == "n't" for t in negs):
					neg = [t for t in negs if t.text == "n't"][0]
					neg_index = neg.i
					question = question._copy_with_remove(indices=neg.i+added, move_deps_to=aux.i+added)
					added -= 1
				elif (
					any(t.text == 'not' for t in negs) and
					v.is_aux and 
					v.text == 'can' and
					v_original_whitespace_ == ''
				):
					neg = [t for t in negs if t.text == 'not'][0]
					prev_i = v_original_index - 1
					prev_token = self[prev_i]
					prev_token.whitespace_ = ' '
					
					# we need to replace the token before the 
					# new position of the negation,
					# not at the original index of that token
					replace_index = neg.i-1+added
					
					# if we're not replacing at the beginning of the sentence,
					# decapitalize the token if it should be decapitalized
					if not replace_index == 0 and prev_token.can_be_decapitalized:
						prev_token.text = prev_token.text[0].lower() + prev_token.text[1:]
					
					question = question.copy_with_replace(tokens=prev_token, indices=neg.i-1+added)
		
		q_mark, q_mark_i = self._get_question_punctuation(question)
		
		# remove extra stuff from the history 
		# that accumulates during the loops above
		question.caller = self.caller 
		question.caller_args = self.caller_args
		
		question = question.copy_with_replace(tokens=q_mark, indices=q_mark_i)
		
		question.previous = self
		
		return question
	
	def make_polar_question_sentence(self) -> 'EDoc':
		'''Covert a question into a sentence.'''
		raise NotImplementedError('Not currently doing this.')
	
	def _get_question_punctuation(self, question: 'EDoc') -> Tuple:
		# replace the final punct with a question mark
		final = question[-1]
		if not final.text in ['!', '.'] or final.dep_ != 'punct':
			raise ParseError(
				f'The sentence "{self}" does not end with '
				'an exclamation point or period! '
				"It may already be a question, or it wasn't "
				"parsed correctly. I won't make it a question."
			)
		
		final.text = '?'
		
		return final, final.i
	
	def _can_be_inverted_subject(self, s: Union[EToken,List[EToken]], v: EToken) -> bool:
		'''Can the passed subject be inverted with an aux?'''
		if not isinstance(s,list):
			s = [s]
		else:
			s = [s[0]]
		
		# a subject cannot be inverted with an aux
		# if it is clausal and the verb is not a gerund
		# (i.e., if it is headed by "that" or "to")
		if any(
			t.dep_ in ['csubj', 'csubjpass'] 
			for t in s 
			if 	t.tag_ not in ['VBG', 'VBN', 'VB', 'VBZ'] or 
				t.get_morph('VerbForm') == 'Inf'
		):
			# clausal_subject_text = ' '.join(
			# 	[
			# 		t.text 
			# 		for t in sorted([t for t in s[0].children] + s, key=lambda t: t.i)
			# 	]
			# )
			# 
			# log.info(
			# 	f'Cannot convert "{self}" to a polar question, because '
			# 	 'it has a clausal subject with a non-gerund verb '
			# 	f'("{clausal_subject_text}")!'
			# )
			return False
		
		# we can only do inversion for subjects that precede the verb
		# note that we only call this from the question-making method
		# and it already filters out stuff dependents for there-support
		# meaning that this will be okay even in those cases.
		if any(v.i < t.i for t in s):
			return False
		
		return True
	
	@staticmethod
	def _get_aux(v: EToken) -> EToken:
		'''Get the appropriate auxiliary for forming a question.'''
		if v.is_aux and not v.lemma_ == 'get':
			return v
		else:
			return EToken.from_definition(**{
				**Q_DO,
				'whitespace_': ' ',
				'head': v,
			})
	
	@staticmethod
	def _get_subject_initial_index(s: Union[EToken,List[EToken]]) -> int:
		'''Get the earliest index in the phrase of the subject.'''
		if isinstance(s,list):
			earliest_subject_index = min([t.i for t in s])
		else:
			earliest_subject_index = s.i
			s = [s]
		
		# recursive go through the children of the subject
		# until no more are found, and get the lowest index
		children = [t for n in s for t in n.children]
		all_children = children
		while children:
			children = [t for child in children for t in child.children]
			all_children = children + all_children
		
		children = all_children
		
		if children:
			earliest_subject_index = min([earliest_subject_index, *[t.i for t in children]])
		
		return earliest_subject_index