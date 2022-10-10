import sys

from core.dataset_maker import create_datasets_from_config

if __name__ == '__main__':
	if not sys.argv[-1] in ['-d', '--debug']:
		create_datasets_from_config()
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