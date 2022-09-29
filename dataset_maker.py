# dataset maker
#
# use to make a corpus of random examples from huggingface datasets
# it is NOT recommended that you run this locally unless you feel
# like you have a lot of extra disk space you'd like to fill up
import os
import re
import json
import gzip
import spacy
import string

from tqdm import tqdm
from typing import *
from random import random
from datasets import load_dataset, Dataset
from itertools import zip_longest
from collections import defaultdict
from grammar_funs import *
from metadata_funs import *

# good defaults for conditions for English:
nlp = spacy.load('en_core_web_trf')

def has_inflected_main_verb_with_non_expletive_subject(s: str) -> bool:
	'''Is there a main verb in the sentence, and is it inflected?'''
	main_verb = [t for t in nlp(s) if t.dep_ == 'ROOT']
	if main_verb:
		if (
			main_verb[0].tag_ in ['VBZ', 'VBP', 'VBD'] and not
			main_verb[0].lemma_ == 'be'
		):
			if any([t.dep_ == 'expl' for t in main_verb[0].children]):
				return False
			elif [t for t in main_verb[0].children if t.dep_ == 'nsubj'][0].text.isupper():
				return False
			else:
				return True
	else:
		return False

def en_conditions(s: str) -> bool:
	'''
	Applies conditions to en sentence all at once. 
	This should be faster, since we can return false early rather than evaluate each condition.
	'''
	# must be longer than a single character
	if len(s) <= 1:
		return False
		
	# must start with a capital letter
	if not s[0].isupper():
		return False
		
	# must not contain a semicolon (i.e., two sentences)
	if ';' in s:
		return False
		
	# commas and periods must not be preceded by spaces
	if ' ,' in s or ' .' in s:
		return False
	
	# if the number of quotation marks is not even
	if s.count('"') % 2 == 1:
		return False
	
	# no sentences with any finite form of 'be'
	if ' was ' in s or ' were ' in s or ' is ' in s or ' are ' in s:
		return False
	
	# must be less than 50 words
	if not len(s.split()) <= 50:
		return False
	
	# must consistent only of punctuation and english letters
	if not s.translate(str.maketrans('', '', string.punctuation)).isascii():
		return False
	
	if s[-1] == '.':
		# must not end with a . preceded by a capital letter (happens when splitting on middle names)
		if s[-2].isupper():
			return False
		
		# must not end with a . preceded by an abbreviation
		if s[-4:] in ['Mrs.', 'Ave.', 'Ltd.', 'Inc.']:
			return False
		
		if s[-3:] in ['Mr.', 'Dr.', 'Ms.', 'St.', 'Av.']:
			return False
		
		if s[-5:] in ['Prof.', 'Blvd.']:
			return False
		
	# must not contain a colon separating two word characters (occurs in references lists)
	if re.search(r'\w:\w', s):
		return False
	
	if not has_inflected_main_verb_with_non_expletive_non_acronym_subject(s):
		return False
	
	return True

def create_seq2seq_tense_dataset(
	dataset: str,
	dataset_args: tuple = None,
	dataset_kwargs: tuple = None,
	name: str = None,
	conditions: List[Callable] = None,
	splits: Dict[str,int] = dict(
		train 	= 100000,
		dev 	= 1000,
		test 	= 10000,
	),
	splits_funs: Dict[str,Callable] = None,
	splits_funs_args: Dict[str,Tuple] = None,
	splits_funs_kwargs: Dict[str,Dict] = None,
	metadata_fun: Callable = None,
	metadata_fun_args: Tuple = None,
	metadata_fun_kwargs: Dict = None,
) -> None:
	'''
	Create a dataset of sentences in pres to past and past to past pairs
	randomly pulled from huggingface datasets.
	Parsed using spaCy's core_en_web_trf parser
	The dataset is saved in a text file with one sentence per line.
	
		params:
			dataset (str)				: name of a huggingface dataset
			dataset_args (tuple) 		: additional arguments to pass to load_dataset for each dataset
			dataset_kwargs (dict)		: additional arguments to pass to load_dataset for each dataset
			name (str)					: what to name the dataset. if not specified, a default name based
										  on the huggingface name will be used
			conditions (List[callable])	: a list of functions to apply to each sentence.
										  all must be true for a sentence to be included
			metadata_fun (callable)		: used to get metadata for a sentences parsed with spaCy
			metadata_fun_args (Tuple)	: args for metadata_fun
			metadata_fun_kwargs (Dict)	: kwargs for metadata_fun
			splits (dict)				: mapping between split names and n_examples for that split
			splits_funs (dict)			: mapping between split names and additional functions to perform on the
										  sentence (parsed with core_en_web_trf)
			splits_funs_args (dict)		: mapping between split names and additional args to for splits_funs[split]
			splits_funs_kwargs (dict)	: additional arguments to pass to the function used on each example
										
	'''
	name 				= name if not name == None else dataset
	dataset_args 		= () if dataset_args is None else dataset_args
	dataset_kwargs 		= {} if dataset_kwargs is None else dataset_kwargs
	
	conditions 			= [] if conditions is None else conditions
	
	splits_funs 		= defaultdict(lambda: lambda *args, **kwargs: None) if splits_funs is None else splits_funs
	splits_funs_args 	= defaultdict(lambda: ()) if splits_funs_args is None else splits_funs_args
	splits_funs_kwargs 	= defaultdict(lambda: {}) if splits_funs_kwargs is None else splits_funs_kwargs
	
	metadata_fun 		= (lambda *args, **kwargs: {}) if metadata_fun is None else metadata_fun
	metadata_fun_args 	= () if metadata_fun_args is None else metadata_fun_args
	metadata_fun_kwargs = {} if metadata_fun_kwargs is None else metadata_fun_kwargs
	
	try:
		dataset = load_dataset(dataset, *dataset_args, **dataset_kwargs)
	except Exception:
		raise ValueError(f'Unable to load dataset {dataset} on huggingface!')
	
	nlp	= spacy.load('en_core_web_trf')
	exs	= [None for _ in range(sum(splits.values()))] # so we don't repeat sentences, even across datasets
	
	for split, n in splits.items():
		# preallocate
		new_dataset 	= [None for _ in range(n)]
		new_metadata 	= [None for _ in range(n)]
		n_chosen 		= 0
		
		# we don't just shuffle the dataset and choose the first n examples,
		# because some datasets contain multiple sentences per row. we want
		# n sentences, which means getting the row, and then splitting and getting a random (good)
		# sentence from that row. we also don't want repeats that are identical except for case
		with tqdm(total=n) as pbar:
			while n_chosen < n:
				ex 						=  get_random_sentence(dataset['train'], exclude=exs, conditions=conditions)
				parsed 					=  nlp(ex)
				new_dataset[n_chosen] 	=  {'translation': splits_funs[split](parsed, **splits_funs_kwargs[split])}
				new_metadata[n_chosen] 	=  metadata_fun(parsed, *metadata_fun_args, **metadata_fun_kwargs)	
				exs[n_chosen] 			=  ex
				n_chosen 				+= 1
				pbar.set_postfix(split=split)
				pbar.update(1)
		
		os.makedirs(os.path.join('data', name), exist_ok=True)
		print(f'Writing out dataset {name} ({split}).')
		with gzip.open(os.path.join('data', name, f'{name}_{split}.json.gz'), 'wt', encoding='utf-8') as out_file:
			for ex in tqdm(new_dataset):
				json.dump(ex, out_file, ensure_ascii=False)
				out_file.write('\n')
		
		print(f'Writing out metadata for {name} ({split}).')
		with gzip.open(os.path.join('data', name, f'{name}_{split}_metadata.json.gz'), 'wt', encoding='utf-8') as out_file:
			for m in tqdm(new_metadata):
				json.dump(m, out_file, ensure_ascii=False)
				out_file.write('\n')

def get_random_sentence(
	dataset: Dataset, 
	exclude: List[str] = None, 
	conditions: List[Callable] = None,
) -> str:
	'''
	Returns a random example from the dataset.
	
		params:
			dataset (Dataset)			: a Dataset to draw a random example from
			exclude (List(str))			: a list of strings to exclude.
										  useful if you want distinct examples
			conditions (list[callable])	: a list of functions to apply to a sentence.
										  all must be true for a sentence to be included
		
		returns:
			str 				: a random sentence pulled from the dataset
	'''
	conditions = [conditions] if not isinstance(conditions,list) else conditions
	
	def split_sentences(s: str, d: str = r'[\.!\?]') -> str:
		'''Splits string s into sentences, delimited by regex d.'''
		# deals with a problematic abbreviation
		if ' c. ' in s:
			return [''] 
		
		ss = re.split(f'({d} )', s)
		
		# merge adjacent delimeters back into the sentence
		it = iter(ss)
		ss = [f'{s1}{s2}' for s1, s2 in zip_longest(it, it, fillvalue='')]
		
		# remove extra spaces
		ss = [s.strip() for s in ss if s.strip()]
		
		# iterating is way faster than using re.sub
		for i, _ in enumerate(ss):
			while '  ' in ss[i]:
				ss[i] = ss[i].replace('  ', ' ')
		
		return ss
	
	e = ''
	while not e:
		# pick a random example
		# np.random.choice is sloooow with big lists
		r 	= int(round(random() * (len(dataset)-1),0))
		ex 	= split_sentences(dataset[r]['text'])
		# also exclude sentences with newlines, since it's not clear what to do about those
		ex 	= [s for s in ex if not s in exclude and not '\n' in s and all([c(s) for c in conditions])]
		
		# if there's anything left, save a sentence
		if ex:
			# get a random example from the retained sentences
			r = int(round(random() * (len(ex)-1),0))
			e = ex[r]
	
	return e
	
if __name__ == '__main__':
	
	create_seq2seq_tense_dataset()