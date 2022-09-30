'''
Short useful functions for working with spaCy Docs.
Some of this is adapted from 
https://github.com/chartbeat-labs/textacy/blob/main/src/textacy/spacier/utils.py
'''
from copy import deepcopy
from typing import *

import spacy

from spacy.tokens.doc import Doc
from spacy.tokens.token import Token

SUBJ_DEPS: Set[str] = {"csubj", "csubjpass", "expl", "nsubj", "nsubjpass"}

nlp_ = spacy.load('en_core_web_trf')
nlp = lambda s: EDoc(nlp_(s))

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
		return len(self.text)
	
	def __unicode__(self) -> str:
		return self.text
	
	def __bytes__(self) -> bytes:
		return self.__unicode__.encode('utf8')
	
	def __str__(self) -> str:
		return self.__unicode__()
	
	def __repr__(self) -> str:
		return self.__str__()

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
		return self.__str__()
	
	def __str__(self) -> str:
		return self.__unicode__()
	
	def __len__(self) -> int:
		return len(self.doc)
	
	def __getitem__(self, i: Union[int,Tuple]) -> Union[Token,'Span']:
		return EToken(self.doc[i])
	
	def __iter__(self) -> Token:
		yield from self.doc
	
	def __unicode__(self) -> str:
		return "".join([t.text_with_ws for t in self.doc])
	
	def __bytes__(self) -> bytes:
		return self.__unicode__.encode('utf-8')
	
	def __setitem__(self, key, value) -> None:
		raise NotImplementedError("To set a value, use copy_with_replace(tokens, indices) instead to create a new EDoc.")
	
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
		
		tokens 		= [tokens] if not isinstance(tokens, list) else tokens
		indices		= [t.i for t in tokens] if indices is None else indices
		indices 	= [indices] if not isinstance(indices, list) else indices
		
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
		return v.morph.get('Tense')[0]
	
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
			return 'Plur'
		else:
			return s.morph.get('Number')[0]
	
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
		distractors = [t for t in interveners if t.morph.get('Number') != n]
		return distractors
	
	@staticmethod
	def _get_conjuncts(t: Union[Token,EToken]):
		'''Returns all conjuncts dependent on the first in a coordinated phrase.'''
		return [r for r in t.rights if r.dep_ == 'conj']