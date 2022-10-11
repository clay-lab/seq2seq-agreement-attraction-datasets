import sys
import argparse

from core.dataset_maker import create_datasets_from_config

parser = argparse.ArgumentParser()
parser.add_argument(
	'-d', '--debug', default=False, action='store_true',
	help='Whether to enter debug mode on startup.'
)

parser.add_argument(
	'-o', '--only', default=None,
	help='Which datasets in config to generate by name. Default (None) generates all.'
)

if __name__ == '__main__':
	args = parser.parse_args()
	if not args.debug:
		if isinstance(args.only,str):
			args.only = args.only.split(',')
		
		create_datasets_from_config(only=args.only)
	else:
		from core.spacyutils import nlp
		from core.constants import *
		from core.language_funs.en.grammar_funs import *
		from pattern.en import (
			SG, PL,
			PAST, PRESENT, INFINITIVE,
			conjugate, singularize, pluralize
		)
		breakpoint()