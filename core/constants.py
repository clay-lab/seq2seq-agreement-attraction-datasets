'''
constants used in spacyutils.py to
codify certain kinds of dependencies
and make up for some deficiencies of
pattern.en
'''
from typing import Set, Dict, List, Tuple

from pattern.en import SG, PL
from pattern.en import PAST, PRESENT

from word2number import w2n

MIN_SENTENCE_LENGTH_IN_CHARS: int = 2
MAX_SENTENCE_LENGTH_IN_WORDS: int = 50

EXCLUSION_STRINGS: Set[str] = {
	';', 
	'"', 
	' ,', 
	' .',
	'/',
	"' ",
	'\\',
	'_',
	'\n',
	'.com',
	'.gov',
	'.edu',
	'.net',
	'@',
	'#',
	'^',
	'*',
	'+',
	'~',
	'`',
	'<',
	'>',
	'{',
	'}',
	'[',
	']',
	'|'
}

# must not contain a colon surrounded by two word characters
# (occurs in references lists)
EXCLUSION_REGEXES: Set[str] = {
	r'\w:\w',
	r'\w\.\w'
}

VALID_SENTENCE_ENDING_CHARS: Set[str] = {
	'.',
	'?',
	'!'
}

DELIMITERS: Set[Tuple[str]] = {
	('(', ')'),
	('[', ']'),
	('{', '}')
}

SUBJ_DEPS: Set[str] = {
	"csubj", 
	"csubjpass", 
	"attr", 
	"nsubj", 
	"nsubjpass"
}

OBJ_DEPS: Set[str] = {
	"cobj", 
	"nobj",
	"dobj",
}

NOUN_POS_TAGS: Set[str] = {
	'NOUN',
	'PRON',
	'PROPN'
}

SUBJ_EXCL_TAGS: Set[str] = {
	'WD',
	'WDT'
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

CONJUGATE_MAP: Dict[str,Dict[str,Dict[str,str]]] = {
	'founded': {
		'singular': {'present': 'founds'},
		'plural'  : {'present': 'found'}, 
	},
}

def word_is_number(s: str) -> bool:
	'''
	Return true if the word can be
	converted to a number, else False.
	'''
	try:
		w2n.word_to_num(s)
		return True
	except ValueError:
		try:
			float(s.replace(',', ''))
			return True
		except ValueError:
			pass
		
		return False

ORDINALS: Set[str] = {
	'Second',
	'second',
	'Third',
	'third',
	'Fourth',
	'fourth',
	'Fifth',
	'fifth',
	'Sixth',
	'sixth',
	'Seventh',
	'seventh',
	'Eighth',
	'eighth',
	'Ninth',
	'ninth',
	'Tenth',
	'tenth',
	'Eleventh',
	'eleventh',
	'Twelvth',
	'twelvth',
	'Thirteenth',
	'thirteenth',
	'Fourteenth',
	'fourteenth',
	'Fifteenth',
	'fifteenth',
	'Sixteenth',
	'sixteenth',
	'Seventeenth',
	'seventeenth',
	'Eighteenth',
	'eighteenth',
	'Nineteenth',
	'nineteenth',
	'Twentieth',
	'twentieth',
	'Thirtieth',
	'thirtieth',
	'Fourtieth',
	'fourtieth',
	'Fiftieth',
	'fiftieth',
	'Sixtieth',
	'sixtieth',
	'Seventieth',
	'seventieth',
	'Eightieth',
	'eightieth',
	'Nintieth',
	'nintieth',
	'Hundredth',
	'hundredth',
	'Thousandth',
	'thousandth',
	'Millionth',
	'millionth',
	'Billionth',
	'billionth',
	'Trillionth',
	'trillionth',
	'Quadrillionth',
	'quadrillionth',
	'Quintillionth',
	'quintillionth',
	'Sextillionth',
	'sextillionth',
	'Septillionth',
	'septillionth',
	'Octillionth',
	'octillionth',
	'Nonillionth',
	'nonillionth'
}

# spaCy doesn't assign the right morphs to these words
INCORRECT_MORPHS: Dict[str,Dict[str,str]] = {
	'was' : {'Number': 'Sing'},
	'were': {'Number': 'Plur'},
	'is'  : {'Number': 'Sing'},
	'are' : {'Number': 'Plur'},
	'Many': {'Number': 'Plur'},
	'many': {'Number': 'Plur'},
	'Much': {'Number': 'Sing'},
	'much': {'Number': 'Sing'},
	'You' : {'Number': 'Plur'},
	'you' : {'Number': 'Plur'},
	'Each': {'Number': 'Sing'},
	'each': {'Number': 'Sing'},
	'Both': {'Number': 'Plur'},
	'both': {'Number': 'Plur'},
	'Few' : {'Number': 'Plur'},
	'few' : {'Number': 'Plur'},
	# for all/most/more/last, this is overridden when
	# it is used as a partitive
	# this will not always be right, but 
	# when we don't have the actual referent
	# it's the best we can guess
	'All' : {'Number': 'Plur'},
	'all' : {'Number': 'Plur'},
	'Most': {'Number': 'Plur'},
	'most': {'Number': 'Plur'},
	'More': {'Number': 'Plur'},
	'more': {'Number': 'Plur'},
	'Last': {'Number': 'Sing'},
	'last': {'Number': 'Sing'},
	'A'   : {'Number': 'Sing'},
	'a'   : {'Number': 'Sing'},
	'Several':{'Number': 'Plur'},
	'several':{'Number': 'Plur'},
	'That': {'Number': 'Sing'},
	'that': {'Number': 'Sing'},
	**{ordinal: {'Number': 'Sing'} for ordinal in ORDINALS},
}

INCORRECT_MORPHS_PRESENT_TENSE: Dict[str,Dict[str,str]] = {
	'say': {'Number': 'Plur'},
	'have':{'Number': 'Plur'},
	'remain':{'Number': 'Plur'},
}

# partitives are things where the head noun of the subject
# is NOT what the verb is supposed to agree with
# note that this does not necessarily cover all actual partitives
PARTITIVES_WITH_OF: Set[str] = {
	'Some',
	'some',
}

# partitives that optionally take of
# e.g., all (of) the people (plur),
# all (of) the water (sing)
PARTITIVES_OPTIONAL_OF: Set[str] = {
	'All',
	'all',
	'Most',
	'most',
	'More',
	'more',
	# unlike other ordinals, first can
	# be singular or plural
	'First',
	'first',
	'Last',
	'last'
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
	*PARTITIVES_WITH_OF,
	*PARTITIVES_OPTIONAL_OF,
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

# spaCy has problems with some prefixes
# it thinks they're subjects
VERB_PREFIXES: Set[str] = {
	'co',
}