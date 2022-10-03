'''
constants used in spacyutils.py to
codify certain kinds of dependencies
and make up for some deficiencies of
pattern.en
'''
from typing import Set, Dict, List

from pattern.en import SG, PL
from pattern.en import PAST, PRESENT

SUBJ_DEPS: Set[str] = {
	"csubj", 
	"csubjpass", 
	"attr", 
	"nsubj", 
	"nsubjpass"
}

OBJ_DEPS: Set[str] = {
	"cobj", 
	"nobj"
}

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

# cases that pattern.en doesn't handle correctly
SINGULARIZE_MAP: Dict[str,str] = {
	'these': 'this',
	'those': 'that',
	'all': 'every', # works well enough, some edge cases (i.e., 'all the') will break
}

PLURALIZE_MAP: Dict[str,str] = {
	'the': 'the', # pattern.en does 'thes' lol
}

# spaCy doesn't assign the right morphs to these words
INCORRECT_MORPHS: Dict[str,Dict[str,str]] = {
	'was' : {'Number': 'Sing'},
	'were': {'Number': 'Plur'},
	'is'  : {'Number': 'Sing'},
	'are' : {'Number': 'Plur'},
}

# partitives are things where the head noun of the subject
# is NOT what the verb is supposed to agree with
# note that this does not necessarily cover all actual partitives
PARTITIVES: List[str] = [
	'Some',
	'some',
]
