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
PARTITIVES: Set[str] = {
	'Some',
	'some',
}

# these are partitives when they have an indefinite
# determiner. Otherwise, they are normal nouns
PARTITIVES_WITH_INDEFINITE_ONLY: Set[str] = {
	'amount',
	'group',
	'lot',
	'number',
	'quantity',
	'ton',
}

ALL_PARTITIVES: Set[str] = {
	*PARTITIVES,
	*PARTITIVES_WITH_INDEFINITE_ONLY
}

# maps some deps to others for purposes
# of recording distractor structures
STRUCTURE_MAP: Dict[str,str] = {
	'prep': 'PP',
	'pcomp': 'PP',
	'relcl': 'RC',
	'acl': 'CC', 
}

# list of valid distractor structures
DISTRACTOR_STRUCTURES: Set[str] = {
	'CP',
	'PP',
}