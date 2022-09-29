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

from tqdm import tqdm
from typing import *
from random import random
from datasets import load_dataset, Dataset
from itertools import zip_longest
from collections import defaultdict
from grammar_funs import *
from metadata_funs import *

def create_seq2seq_tense_dataset(
	dataset: str,
	dataset_args: tuple = None,
	dataset_kwargs: tuple = None,
	name: str = None,
	max_len: int = 50,
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
			max_len (int)				: the maximum number of words in a sentence in the dataset
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
	
	splits_funs 		= defaultdict(lambda: lambda *args, **kwargs: None) if splits_funs is None else splits_funs
	splits_funs_args 	= defaultdict(lambda: ()) if splits_funs_args is None else splits_funs_args
	splits_funs_kwargs 	= defaultdict(lambda: {}) if splits_funs_kwargs is None else splits_funs_kwargs
	
	metadata_fun 		= lambda *args, **kwargs: {} if metadata_fun is None else metadata_fun
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
				ex 						=  get_random_sentence(dataset['train'], exclude=exs, max_len=max_len)
				parsed 					=  nlp(ex)
				new_dataset[n_chosen] 	=  {'translation': splits_funs[split](parsed, **splits_funs_kwargs[split])}
				new_metadata[n_chosen] 	=  metadata_fun(parsed)	
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
			for m in tqdm(metadata):
				json.dump(m, out_file, ensure_ascii=False)
				out_file.write('\n')

def get_random_sentence(dataset: Dataset, exclude: List[str] = None, max_len: int = 50) -> str:
	'''
	Returns a random example from the dataset.
	
		params:
			dataset (Dataset)	: a Dataset to draw a random example from
			exclude (List(str))	: a list of strings to exclude.
								  useful if you want distinct examples
		
		returns:
			str 				: a random sentence pulled from the dataset
	'''
	def split_sentences(s: str, d: List[str] = r'[\.!\?]') -> str:
		'''Splits string s into sentences, delimited by regex d.'''
		ss = re.split(rf'({d} )', s)
		
		# merge adjacent delimeters back into the sentence
		it = iter(ss)
		ss = [f'{s1}{s2}' for s1, s2 in zip_longest(it, it, fillvalue='')]
		
		# remove extra spaces
		ss = [s.strip() for s in ss if s.strip()]
		
		return ss
	
	e = ''
	while not e:
		# pick a random example
		# np.random.choice is sloooow with big lists
		r 	= int(round(random() * (len(dataset)-1),0))
		ex 	= split_sentences(dataset[r]['text'])
		ex 	= [s for s in ex if not s in exclude and len(s.split()) <= 50]
		
		# if there's anything left, save a sentence
		if ex:
			# get a random example from the retained sentences
			r = int(round(random() * (len(ex)-1),0))
			e = ex[r]
	
	return e
	
if __name__ == '__main__':
	
	create_seq2seq_tense_dataset()
