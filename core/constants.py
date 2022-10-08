'''
constants used in spacyutils.py to
codify certain kinds of dependencies
and make up for some deficiencies of
pattern.en
'''
from typing import (
	Set, Dict, List, 
	Tuple, Callable, Union
)

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

# must not contain a punctuation sandwiched
# by two letters---however, this string EXCLUDES
# the apostrophe, which is okay
EXCLUSION_REGEXES: Set[str] = {
	r'\w[!"#$%&()*+,-./:;<=>?@[\\\]^_`{|}~]\w'
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
	'PROPN',
}

# mostly wh-words
SUBJ_EXCL_TAGS: Set[str] = {
	'WP',
	'WD',
	'WDT',
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
	# we don't have a corresponding entry for this
	# in the present tense, because it will be parsed
	# as the past tense of 'find'
	'founded': {
		'singular': {'present': 'founds'},
		'plural'  : {'present': 'found'}, 
	},
	'leaves': {
		'any': 		{'past': 'left'},
	},
	'leave': {
		'any': 		{'past': 'left'},
	},
	'left' : {
		'singular': {'present': 'leaves'},
		'plural'  : {'present': 'leave'},
	},
	'bears': {
		'any':		{'past': 'bore'},
	},
	'bear':  {
		'any':		{'past': 'bore'},
	},
	'bore':  {
		'singular': {'present': 'bears'},
		'plural'  : {'present': 'bear'},
	},
	# pattern.en doesn't correctly recognize that
	# this is already past tense, and produces "sanged"
	# it also think the past tense is (incorrectly)
	# 'sung' (the participle), instead of 'sang'
	'sang':  {
		'singular': {'present': 'sings'},
		'plural': 	{'present': 'sing'},
		'any':		{'past':    'sang'},
	},
	'sing':  {
		'any':		{'past': 'sang'},
	},
	'sings': {
		'any':		{'past': 'sang'},
	},
	# there is special logic to deal with
	# the fact that this depends on transitivity
	# and meaning in the spacyutils.EDoc class
	'lay':   {
		'singular': {'present': 'lays'},
		'plural':	{'present': 'lay'},
		'any':		{'past': 'laid'},
	},
	'lays':  {
		'singular': {'present': 'lays'},
		'plural': 	{'present': 'lay'},
		'any':		{'past': 'laid'},
	},
	'laid':  {
		'singular': {'present': 'lays'},
		'plural':	{'present': 'lay'},
		'any':		{'past': 'laid'},
	},
	'escapes': {
		'any':	    {'past': 'escaped'},
	},
	'escape': {
		'any': 		{'past': 'escaped'},
	},
	'escaped': {
		'singular': {'present': 'escapes'},
		'plural':	{'present': 'escape'},
		'any':		{'past': 'escaped'},
	},
	'paid': {
		'singular': {'present': 'pays'},
		'plural':   {'present': 'pay'},
		'any':		{'past': 'paid'},
	},
	'pay': {
		'any':		{'past': 'paid'},
	},
	'pays': {
		'any':		{'past': 'paid'},
	},
	'centered': {
		'any': 		{'past': 'centered'},
	},
	'center': {
		'any': 		{'past': 'centered'},
	},
	'centers': {
		'any': 		{'past': 'centered'},
	},
	'quit': {
		'any':		{'past': 'quit'},
	},
	'benefitted': {
		'any':		{'past': 'benefitted'},
	},
	'benefit': {
		'any':		{'past': 'benefitted'},
	},
	'benefits': {
		'any': 		{'past': 'benefitted'},
	},
	'addressed': {
		'any':		{'past': 'addressed'},
	},
	'address': {
		'any':		{'past': 'addressed'},
	},
	'addresses': {
		'any':		{'past': 'addressed'},
	},
	'paralleled': {
		'singular': {'present': 'parallels'},
		'plural':	{'plural': 'parallel'},
	},
	'parallel': {
		'any': 		{'past': 'paralleled'},
	},
	'parallels': {
		'any': 		{'past': 'paralleled'},
	},
	'sank': {
		'singular': {'present': 'sinks'},
		'plural': 	{'present': 'sink'},
		'any':		{'past': 'sank'},
	},
	'sink': {
		'any': 		{'past': 'sank'},
	},
	'sinks': {
		'any': 		{'past': 'sank'},
	},
	'penned':{
		'any':		{'past': 'penned'},
	},
	'pen': {
		'any':		{'past': 'penned'},
	},
	'pens': {
		'any': 		{'past': 'penned'},
	},
	'pleaded': {
		'any': 		{'past': 'pleaded'},
	},
	'plead': {
		'any':		{'past': 'pleaded'},
	},
	'pleads': {
		'any':		{'past': 'pleaded'},
	},
	'fit': {
		'any': 		{'past': 'fit'},
	},
	'cursed': {
		'any':		{'past': 'cursed'},
	},
	'curse': {
		'any':		{'past': 'cursed'},
	},
	'curses': {
		'any':		{'past': 'cursed'},
	},
	'sprang': {
		'singular': {'present': 'springs'},
		'plural': 	{'present': 'spring'},
		'any':		{'past': 'sprang'},
	},
	'spring': {
		'any':		{'past': 'sprang'},
	},
	'springs': {
		'any':		{'past': 'sprang'},
	},
	'swapped': {
		'any':		{'past': 'swapped'},
	},
	'swap': {
		'any':		{'past': 'swapped'},
	},
	'swaps': {
		'any':		{'past': 'swapped'},
	},
	'favored': {
		'singular': {'present': 'favors'},
		'plural': 	{'present': 'favor'},
	},
	'favor': {
		'any':		{'past': 'favored'},
	},
	'favors': {
		'any':		{'past': 'favored'},
	},
	'blessed': {
		'any':		{'past': 'blessed'},
	},
	'bless': {
		'any':		{'past': 'blessed'},
	},
	'blesses': {
		'any':		{'past': 'blessed'},
	},
	'brokered': {
		'any':		{'past': 'brokered'},
	},
	'broker': {
		'any':		{'past': 'brokered'},
	},
	'brokers': {
		'any':		{'past': 'brokered'},
	},
	'endeavored': {
		'singular': {'present': 'endeavors'},
		'plural':	{'present': 'endeavor'},
	},
	'endeavor': {
		'any':		{'past': 'endeavored'},
	},
	'endeavors': {
		'any':		{'past': 'endeavored'},
	},
	'heated': {
		'any':		{'past': 'heated'},
	},
	'heat': {
		'any':		{'past': 'heated'},
	},
	'heats': {
		'any':		{'past': 'heated'},
	},
	'shrank': {
		'singular': {'present': 'shrinks'},
		'plural':	{'present': 'shrink'},
		'any':		{'past': 'shrank'},
	},
	'shrink': {
		'any':		{'past': 'shrank'},
	},
	'shrinks': {
		'any':		{'past': 'shrank'}
	},
	'bet': {
		'any':		{'past': 'bet'},
	},
	'bets': {
		'any':		{'past': 'bet'},
	},
	'shutout': {
		'any':		{'past': 'shutout'},
	},
	'shutouts': {
		'any':		{'past': 'shutout'},
	},
	'bit': {
		'singular':	{'present': 'bites'},
		'plural':	{'present': 'bite'},
		'any':		{'past': 'bit'},
	},
	'bite': {
		'any':		{'past': 'bit'},
	},
	'bites': {
		'any':		{'past': 'bit'},
	},
	'bringest': {
		'any':		{'past': 'broughtest'},
	},
	'setup': {
		'any': 		{'past': 'setup'},
	},
	'setups': {
		'any':		{'past': 'setup'},
	},
	'mentored': {
		'singular': {'present': 'mentors'},
		'plural':	{'present': 'mentor'},
	},
	'mentor': {
		'any':		{'past': 'mentored'},
	},
	'mentors': {
		'any':		{'past': 'mentored'},
	},
	'wrapped': {
		'singular': {'present': 'wraps'},
		'plural':	{'present': 'wrap'},
		'any':		{'past': 'wrapped'},
	},
	'wraps': {
		'singular': {'present': 'wraps'},
		'plural':	{'present': 'wrap'},
		'any':		{'past': 'wrapped'},
	},
	'felled': {
		'singular': {'present': 'fells'},
		'plural': 	{'present': 'fell'},
	},
	'secret': {
		'any':		{'past': 'secreted'},
	},
	'secrets': {
		'any':		{'past': 'secreted'},
	},
	'teared': {
		'any':		{'past': 'teared'},
	}
}

WRONG_LEMMAS: Dict[str,str] = {
	'guested': 'guest',
	'remedied': 'remedy',
	'costarred': 'costar',
	'rebranded': 'rebrand',
	'bringest': 'bring',
	'broughtest': 'bring',
	'rerecorded': 'rerecord',
	'photobleached': 'photobleach',
	'photobleaches': 'photobleach',
	'bogged': 'bog',
	'recrossed': 'recross',
	'recrosses': 'recross',
	'gimballed': 'gimbal',
	'overdubbed': 'overdub',
	'homeschooled': 'homeschool',
	'restudies': 'restudy',
	'restudied': 'restudy',
	'rematches': 'rematch',
	'rematched': 'rematch',
	'lifeguarded': 'lifeguard',
	'focusses': 'focus',
	'focussed': 'focus',
	'trialled': 'trial',
	'trialed': 'trial',
	'redshirted': 'redshirt',
	'fulfilled': 'fulfill',
	'fulfils': 'fulfill',
	'fulfil': 'fulfill',
	# something special could be done for 
	# transitive 'secrete' vs. intransitive 'secret (away)'
	# but this is probably low frequency enough it doesn't matter
	# also 'tear/tore (transitive)' and 'tear/teared (up) (intransitive)'
	# as well as fall (intransitive) and fell (transitive)
	'installed': 'install',
	'enrolled': 'enroll',
	'got': 'get',
}

HOMOPHONOUS_VERBS: Dict[str,Dict[str,Dict[str,Dict[str,Union[str,Callable]]]]] = {
	'lay': {
		'singular': {'present': 'lies'}, 
		'plural': 	{'present': 'lie'},
		'condition': (lambda t: t.is_intransitive)
	},
	# TODO: exception for ccomp and prep = about,
	# treat like a transitive in these cases
	'lie': {
		'any': 		{'past': 'lay'},
		'condition': (
			lambda t: 
				t.is_intransitive and 
				not [
					to for to in t.children
					# handle 'lie that' and 'lie about' as usual,
					# even though they are intransitive
					if 	(to.dep_ == 'prep' and to.text == 'about') or
						(to.dep_ == 'ccomp')
				]
		)
	},
	'lies': {
		'any': 		{'past': 'lay'},
		'condition': (
			lambda t: 
				t.is_intransitive and 
				not [
					to for to in t.children
					# handle 'lie that' and 'lie about' as usual,
					# even though they are intransitive
					if 	(to.dep_ == 'prep' and to.text == 'about') or
						(to.dep_ == 'ccomp')
				]
		)
	},
	'secreted': {
		'singular': {'present': 'secrets'},
		'plural':	{'present': 'secret'},
		'condition':(
			lambda t: 
				any(
					to.dep_ == 'prt' and to.text == 'away' 
					for to in t.children
				)
		)
	},
	'tear': {
		'any':		{'past': 'teared'},
		'condition':(lambda t: t.is_intransitive),
	},
	'tears': {
		'any':		{'past': 'teared'},
		'condition':(lambda t: t.is_intransitive),
	},
	'fell': {
		'any':		{
			'past': 'felled',
			'present': 'fell',
		},
		'condition':(lambda t: t.is_transitive),
	}
}

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

PLURALS_WITH_NO_DETERMINERS: Set[str] = {
	'deer',
	'Deer',
	'fish',
	'Fish',
	'sheep',
	'Sheep',
	'species',
	'Species',
	'aircraft',
	'Aircraft',
	'barracks',
	'Barracks',
	'bison',
	'Bison',
	'binoculars',
	'Binoculars',
	'caribou',
	'Caribou',
	'cattle',
	'Cattle',
	'cod',
	'Cod',
	'elk',
	'Elk',
	'eyeglasses',
	'Eyeglasses',
	'goldfish',
	'Goldfish',
	'haddock',
	'Haddock',
	'halibut',
	'Halibut',
	'moose',
	'Moose',
	'pike',
	'Pike',
	'police',
	'Police',
	'premises',
	'Premises',
	'pliers',
	'Pliers',
	'reindeer',
	'Reindeer',
	'salmon',
	'Salmon',
	'scissors',
	'Scissors',
	'series',
	'Series',
	'shellfish',
	'Shellfish',
	'shrimp',
	'Shrimp',
	'spacecraft',
	'Spacecraft',
	'watercraft',
	'Watercraft',
	'squid',
	'Squid',
	'swine',
	'Swine',
	'tongs',
	'Tongs',
	'trout',
	'Trout',
	'tuna',
	'Tuna',
	'hovercraft',
	'Hovercraft',
	'offspring',
	'Offspring',
	'boar',
	'Boar',
	'buffalo',
	'Buffalo',
	'gallows',
	'Gallows',
	'insignia',
	'Insignia',
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
	'Another': {'Number': 'Sing'},
	'another': {'Number': 'sing'},
	'They': {'Number': 'Plur'},
	'they': {'Number': 'Plur'},
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
	# currently an edge case, marked as singular 
	# even when partitives. though a search shows 
	# that "neither of the two are" is way
	# more common than "neither of the two is", 
	# so maybe we want to add these ...
	# 'Neither', 
	# 'neither',
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

def word_is_number(s: str) -> bool:
	'''
	Returns true if the word can be
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