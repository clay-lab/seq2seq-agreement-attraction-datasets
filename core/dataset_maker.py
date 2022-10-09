# dataset maker
#
# use to make a corpus of random examples from huggingface datasets
# it is NOT recommended that you run this locally unless you feel
# like you have a lot of extra disk space you'd like to fill up
import os
import re
import gc
import sys
import json
import gzip
import spacy
import random
import logging
import traceback

from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from typing import List, Callable, Tuple, Dict, Set
from datasets import load_dataset, Dataset
from collections import defaultdict, Counter

from .spacyutils import nlp

logging.basicConfig(encoding='utf-8', level=logging.INFO)
log = logging.getLogger(__name__)

split_sentences = spacy.load(
	'en_core_web_trf', 
	disable=['transformer', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer', 'ner']
)
split_sentences.add_pipe('sentencizer')

# after how many examples should we dump to disk?
# DUMP_FREQ: int = 5000

# what metadata should we not print?
# this is a list of keys in the metadata dict
# to exclude from printing (because there are
# too many categories to be informative, etc.)
DONT_PRINT: Set[str] = {
	'pos_sequence',
	'tag_sequence',
	'src_history',
	'tgt_history',
}

def create_seq2seq_dataset(
	dataset: str,
	dataset_args: tuple = None,
	dataset_kwargs: tuple = None,
	name: str = None,
	conditions_fun: Callable = None,
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
	# dump_freq: int = DUMP_FREQ,
) -> None:
	'''
	Create a dataset for seq2seq models
	randomly pulled from huggingface datasets.
	Parsed using spaCy's core_en_web_trf parser
	The dataset is saved in a text file with one sentence per line.
	
		params:
			dataset (str)				: name of a huggingface dataset
			dataset_args (tuple) 		: additional arguments to pass to load_dataset for each dataset
			dataset_kwargs (dict)		: additional arguments to pass to load_dataset for each dataset
			name (str)					: what to name the dataset. if not specified, a default name based
										  on the huggingface name will be used
			conditions_fun (callable)	: a function to apply to each sentence.
										  must return an EDoc or False.
			metadata_fun (callable)		: used to get metadata for a sentences parsed with spaCy
			metadata_fun_args (Tuple)	: args for metadata_fun
			metadata_fun_kwargs (Dict)	: kwargs for metadata_fun
			splits (dict)				: mapping between split names and n_examples for that split
			splits_funs (dict)			: mapping between split names and additional functions to perform on the
										  sentence (parsed with core_en_web_trf)
			splits_funs_args (dict)		: mapping between split names and additional args to for splits_funs[split]
			splits_funs_kwargs (dict)	: additional arguments to pass to the function used on each example
							
	'''
	name 				= name if name is not None else dataset
	dataset_args 		= () if not dataset_args else dataset_args
	dataset_kwargs 		= {} if not dataset_kwargs else dataset_kwargs
	
	conditions_fun 		= (lambda s: nlp(s)) if conditions_fun is None else conditions_fun
	
	splits_funs 		= defaultdict(lambda: lambda s, *args, **kwargs: {'text': str(s)}) if not splits_funs else splits_funs
	splits_funs_args 	= defaultdict(lambda: ()) if not splits_funs_args else splits_funs_args
	splits_funs_kwargs 	= defaultdict(lambda: {}) if not splits_funs_kwargs else splits_funs_kwargs
	
	metadata_fun 		= (lambda *args, **kwargs: {}) if not metadata_fun else metadata_fun
	metadata_fun_args 	= () if not metadata_fun_args else metadata_fun_args
	metadata_fun_kwargs = {} if not metadata_fun_kwargs else metadata_fun_kwargs
	
	try:
		dataset = load_dataset(dataset, *dataset_args, **dataset_kwargs)
	except Exception:
		raise ValueError(f'Unable to load dataset {dataset} on huggingface!')
	
	for split, n in splits.items():
		# preallocate
		new_dataset 	= [None for _ in range(n)]
		new_metadata 	= [None for _ in range(n)]
		
		file_name 		= os.path.join('data', name, f'{name}_{split}.json.gz')
		metadata_name 	= os.path.join('data', name, f'{name}_{split}_metadata.json.gz')
		
		# how often to update the progress bar
		miniters = max(round(n/1000),1)
		
		# we don't just shuffle the dataset and choose the first n examples,
		# because some datasets contain multiple sentences per row. we want
		# n sentences, which means getting the row, and then splitting and getting a random (good)
		# sentence from that row. we also don't want repeats that are identical except for case
		with logging_redirect_tqdm():		
			for i in tqdm(range(n), postfix=f'{split=}', miniters=miniters):
				ex = ''
				while not ex:
					ex = get_random_parsed_sentence(dataset['train'], conditions_fun=conditions_fun)
					try:
						pair = splits_funs[split](ex, *splits_funs_args[split], **splits_funs_kwargs[split])
						new_dataset[i] = {'translation': {k: str(v) for k, v in pair.items()}}
						new_metadata[i] = metadata_fun(pair, *metadata_fun_args, **metadata_fun_kwargs)
					except KeyboardInterrupt:
						sys.exit('User terminated program.')
					except Exception as e:
						log.warning(f'Example "{ex}" ran into an error!:\n\n')
						log.warning(traceback.format_exc())
						log.warning('\n\n')
						ex = ''
						pass
		
		if 'prefix' in new_dataset[0]['translation']:
			prefixes = Counter([e['translation']['prefix'] for e in new_dataset])
			total = sum(prefixes.values())
			pad_len = max(len(str(k)) for k in prefixes)
			pad_len2 = len(str(total))
			log.info(
				f'\n\nPr. of each prefix ({split}):\n\t' + 
				'\n\t'.join([
					f'{k:>{pad_len}}: {v/total:.04f} ({v:>{pad_len2}}/{total})'
					for k, v in sorted(prefixes.items(), key=lambda p: (-p[1], p[0]))
				]) + 
				'\n'
			)
		
		os.makedirs(os.path.join('data', name), exist_ok=True)
		log.info(f'Writing out dataset {name} ({split}).')
		with gzip.open(file_name, 'wt', encoding='utf-8') as out_file:
			for ex in tqdm(new_dataset, miniters=miniters):
				json.dump(ex, out_file, ensure_ascii=False)
				out_file.write('\n')
		
		for k in [k for k in new_metadata[0] if not k in DONT_PRINT]:
			all_ks = Counter([m[k] for m in new_metadata])
			total = sum(all_ks.values())
			pad_len = max(len(str(k)) for k in all_ks)
			pad_len2 = len(str(total))
			log.info(
				f'\n\nPr. of each {k} ({split}):\n\t' + 
				'\n\t'.join([
					f'{k:>{pad_len}}: {v/total:.04f} ({v:>{pad_len2}}/{total})' 
					for k, v in sorted(all_ks.items(), key=lambda p: (-p[1], p[0]))
				]) + 
				'\n'
			)	
		
		log.info(f'Writing out metadata for {name} ({split}).')
		with gzip.open(metadata_name, 'wt', encoding='utf-8') as out_file:
			for m in tqdm(new_metadata, miniters=miniters):
				json.dump(m, out_file, ensure_ascii=False)
				out_file.write('\n')
		
		log.info('\n\n')

def get_random_parsed_sentence(
	dataset: Dataset, 
	conditions_fun: Callable = None,
) -> str:
	'''
	Generates a random example from the dataset.
	
		params:
			dataset (Dataset)			: a Dataset to draw a random example from
			conditions_fun (Callable)	: a function to apply to a sentence that can filter
										  out unwanted examples. in case the sentence
										  passes all checks, it should return the parsed sentence
										  as an EDoc, else False
		
		returns:
			EDoc 						: a random sentence pulled from the dataset, parsed
	'''
	e = ''
	nrows = len(dataset)-1
	while not e:
		# pick a random example/page
		r  = int(round(random.random() * nrows,0))
		ex = dataset[r]['text']
		
		# adding the strip here because spaCy can't deal with leading spaces or trailing spaces well
		ex = [str(s).strip() for s in split_sentences(dataset[r]['text']).sents]
		
		# get a random sentence first and then check
		# because most sentences will meet our criteria
		# this way we don't parse all of them. 
		# this should speed things up considerably
		r2 = int(round(random.random() * (len(ex)-1),0))
		s  = ex[r2]
		
		# replace nbsp
		s = s.replace(chr(160), ' ')
		
		# spaCy doesn't handle extra spaces well
		while '  ' in s:
			s = s.replace('  ', ' ')
		
		if (s := conditions_fun(s)):
			e = s
		
	return e

def create_datasets_from_config(
	config: Dict[str,List] = None, 
	**kwargs
) -> None:
	'''
	Create and then combine tense datasets for each combination of languages in config.keys().
	
	:param config: Dict[str,List]: passed to create_datasets
	:param kwargs: passed to create_tense_datasets, 
				   combine_language_datasets_for_tense,
				   and create_mt5_scripts
	 			   (useful to set overwrite=True)
	
	:outputs: see outputs of create_tense_datasets and combine_language_datasets_for_tense.
	'''
	config = load_config(config) if config is None or isinstance(config,str) else config
		
	for dataset in config['sources']:
		dataset_args 	= config['sources'][dataset].get('dataset_args', [])
		dataset_kwargs 	= config['sources'][dataset].get('dataset_kwargs', {})
		
		for name in config['sources'][dataset]['names']:
			log.info(f'Creating datasets for {name} using {dataset} (args={dataset_args}, kwargs={dataset_kwargs})')
			
			# unpack the config
			conditions_fun		= config['sources'][dataset]['names'][name].get('conditions_fun', lambda s: nlp(s))
			splits 				= config['sources'][dataset]['names'][name]['splits']
			splits_funs 		= config['sources'][dataset]['names'][name]['splits_funs']
			splits_funs_args 	= config['sources'][dataset]['names'][name].get('splits_funs_args', {})
			splits_funs_kwargs 	= config['sources'][dataset]['names'][name].get('splits_funs_kwargs', {})
			metadata_fun 		= config['sources'][dataset]['names'][name]['metadata_fun']
			metadata_fun_args 	= config['sources'][dataset]['names'][name].get('metadata_fun_args', [])
			metadata_fun_kwargs = config['sources'][dataset]['names'][name].get('metadata_fun_kwargs', {})
			# dump_freq 			= config['sources'][dataset]['names'][name].get('dump_freq', DUMP_FREQ)
							
			# if we're loading from a file, we have to store these as strings,
			# so we need to import the actual objects
			if isinstance(conditions_fun, str):
				module = conditions_fun.rsplit('.', 1)[0]
				exec(f'import {module}')
				conditions_fun = eval(conditions_fun)
		
			for split in splits_funs:
				if isinstance(splits_funs[split], str):
					module = splits_funs[split].rsplit('.', 1)[0]
					exec(f'import {module}')
					splits_funs[split] = eval(splits_funs[split])
			
			if isinstance(metadata_fun, str):
				module = metadata_fun.rsplit('.', 1)[0]
				exec(f'import {module}')
				metadata_fun = eval(metadata_fun)	
			
			create_seq2seq_dataset(
				dataset=dataset,
				dataset_args=dataset_args,
				dataset_kwargs=dataset_kwargs,
				name=name,
				conditions_fun=conditions_fun,
				splits=splits,
				splits_funs=splits_funs,
				splits_funs_args=splits_funs_args,
				splits_funs_kwargs=splits_funs_kwargs,
				metadata_fun=metadata_fun,
				metadata_fun_args=metadata_fun_args,
				metadata_fun_kwargs=metadata_fun_kwargs,
				# dump_freq=dump_freq,
			)
			
			log.info('')
	
	create_t5_scripts(config, **kwargs)

def create_t5_scripts(
	config: Dict = None, 
	overwrite: bool = False
) -> None:
	'''
	Creates finetuning and eval scripts for the passed config for t5.
	
	:params config: (List[str]): a config
	:params overwrite: bool: whether to overwrite existing scripts
	
	If no argument is passed, attempt to load the language ids from a file ./data/config.json
	'''	
	script = '\n'.join([
		'#!/bin/bash',
		'',
		'#SBATCH --job-name=T5-base-finetune-tense-[TRAIN_LANG]',
		'#SBATCH --output=joblogs/%x_%j.txt',
		'#SBATCH --nodes=1',
		'#SBATCH --cpus-per-task=1',
		'#SBATCH --mem=30GB',
		'#SBATCH --time=10:00:00',
		'#SBATCH --gpus=v100:1',
		'#SBATCH --partition=gpu',
		'#SBATCH --mail-type=END,FAIL,INVALID_DEPEND',
		'',
		'module load CUDA',
		'module load cuDNN',
		'module load miniconda',
		'',
		'source activate /gpfs/gibbs/project/frank/ref4/conda_envs/py38-agratt',
		'',
		'python core/run_seq2seq.py \\',
		"	--model_name_or_path 't5-base' \\",
		'	--do_train \\',
		'	--task translation_src_to_tgt \\',
		'	--train_file data/[TRAIN_LANG]/[TRAIN_LANG]_train.json.gz \\',
		'	--validation_file data/[DEV_LANG]/[DEV_LANG]_dev.json.gz \\',
		'	--output_dir outputs/t5-finetuning-[TRAIN_LANG]-bs128/ \\',
		'	--per_device_train_batch_size=4 \\',
		'	--gradient_accumulation_steps=32 \\',
		'	--per_device_eval_batch_size=16 \\',
		'	--overwrite_output_dir \\',
		'	--predict_with_generate \\',
		'	--num_train_epochs 10.0'
	]) + '\n'
	
	eval_script = script.replace('finetune', 'eval')
	eval_script = eval_script.replace('--do_train \\', '--do_learning_curve \\')
	eval_script = eval_script.replace('[DEV_LANG]', '[TEST_LANG]')
	eval_script = re.sub(r'_dev(\.|_)', '_test\\1', eval_script)
	eval_script = eval_script.replace('--per_device_train_batch_size=4', '--per_device_train_batch_size=8')
	eval_script = eval_script.replace('	--gradient_accumulation_steps=32 \\\n', '')
	eval_script = eval_script.replace('\n	--num_train_epochs 10.0', '')
	
	config 	= load_config() if config is None else config
	langs 	= [tuple(pair) for pair in config['pairs']] if 'pairs' in config else []
	
	# create directories if not existant
	os.makedirs(os.path.join('scripts', 'finetune'), exist_ok=True)
	os.makedirs(os.path.join('scripts', 'eval'), exist_ok=True)
	
	# create the scripts for each language and pair of languages
	for lang in langs:
		lang_ft_script = script
		lang_ev_script = eval_script
		
		train_lang 		= lang[0]
		dev_lang 		= lang[0]
		test_lang 		= lang[1]
		
		file_name 		= '_'.join(lang) if lang[0] != lang[1] else lang[0]
		
		if os.path.isfile(os.path.join('data', train_lang, f'{train_lang}_train.json.gz')):
			print(f'Creating scripts for {" -> ".join(lang)}')
			# if the langs are not the same, we do not need to create a separate tuning script, only a separate eval script
			if (
				lang[0] == lang[1] and 
				os.path.isfile(os.path.join('data', dev_lang, f'{dev_lang}_dev.json.gz'))
			):
				lang_ft_script = lang_ft_script.replace('[TRAIN_LANG]', train_lang)
				lang_ft_script = lang_ft_script.replace('[DEV_LANG]', dev_lang)
				if not os.path.exists(os.path.join('scripts', 'finetune', f'finetune_t5_{file_name}_bs128.sh')) or overwrite:
					with open(os.path.join('scripts', 'finetune', f'finetune_t5_{file_name}_bs128.sh'), 'wt') as out_file:
						out_file.write(lang_ft_script)
			
			# if os.path.isfile(os.path.join('data', test_lang, f'{test_lang}_test.json.gz')):
			lang_ev_script = lang_ev_script.replace('[TRAIN_LANG]', train_lang)
			lang_ev_script = lang_ev_script.replace('[TEST_LANG]', test_lang)
			if not os.path.exists(os.path.join('scripts', 'eval', f'eval_t5_{file_name}_bs128.sh')) or overwrite:
				with open(os.path.join('scripts', 'eval', f'eval_t5_{file_name}_bs128.sh'), 'wt') as out_file:
					out_file.write(lang_ev_script)

def load_config(path: 'str or Pathlike' = None) -> Dict[str,List]:
	'''
	Loads a dataset creation config file from disk.
	
	:param path: str or Pathlike: the path to the config file.
						   If no path is provided, attempt to load
						   ./data/config.json as the config.
	'''
	if path is None:
		path = os.path.join('data', 'config.json')
	
	with open(path, 'rt', encoding='utf-8') as in_file:
		config = json.load(in_file)
	
	return config
