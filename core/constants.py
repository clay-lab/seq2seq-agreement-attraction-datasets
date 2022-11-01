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
from pattern.en import PAST, PRESENT, INFINITIVE

from word2number import w2n

MIN_SENTENCE_LENGTH_IN_CHARS: int = 2
MAX_SENTENCE_LENGTH_IN_WORDS: int = 50
MIN_SENTENCE_LENGTH_IN_WORDS: int = 3

SPACE_CHARS: Set[str] = {
	chr(8202),
	chr(8198),
	chr(8239),
	chr(8201),
	chr(8197),
	chr(160),
	chr(8200),
	chr(8196),
	chr(8194),
	chr(8199),
	chr(8195),
}

EXCLUSION_STRINGS: Set[str] = {
	';', 
	'"',
	"'",
	' ,', 
	' .',
	'/',
	"' ",
	'\\',
	'_',
	'\n',
	'\t',
	'.com',
	'.gov',
	'.edu',
	'.net',
	'@',
	'#',
	'%',
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
	'|',
	# account for missing apostrophes with contractions
	' m ',
	' re ',
	' s ',
	' d ',
	' ve ',
	' ll ',	
	' t ',
	" t've ",
	" d've ",
	" ll've ",
	'himthat',
	'hilself',
	'unitsalso',
	'Americansskirmished',
}

# must not contain a punctuation sandwiched
# by two letters---we are intentionally excluding
# apostrophes, since they lead to difficulties with inflecting
# the verb. also no punctuations two in a row
# also no things that occur only
EXCLUSION_REGEXES: Set[str] = {
	r'\w[!\'"#$%&()*+,-./:;<=>?@[\\\]^_`{|}~]\w',
	r'[!\'"#$%&()*+,-./:;<=>?@[\\\]^_`{|}~]{2}',
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
	"nsubjpass",
	"expl",
}

OBJ_DEPS: Set[str] = {
	"cobj", 
	"nobj",
	"dobj",
}

DET_TAGS: Set[str] = {
	'DT',
	'JJ', # many,
	'JJR', # fewer,
	'CD', # numbers
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
	'PST': PAST,
	'Pst': PAST,
	'pst': PAST,
	'PRESENT': PRESENT,
	'Present': PRESENT,
	'present': PRESENT,
	'PRES': PRESENT,
	'Pres': PRESENT,
	'pres': PRESENT,
	'INF': INFINITIVE,
	'Inf': INFINITIVE,
	'inf': INFINITIVE,
	'INFINITIVE': INFINITIVE,
	'Infinitive': INFINITIVE,
	'infinitive': INFINITIVE,
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

# things that pattern.en gets wrong.
# also, we don't force US English here, but in cases
# where a form is ambiguous, we prefer it
CONJUGATE_MAP: Dict[str,Dict[str,Dict[str,str]]] = {
	# we don't have a corresponding entry for this
	# in the present tense, because it will be parsed
	# as the past tense of 'find'
	'founded': {
		'singular': {'present': 'founds'},
		'plural': 	{'present': 'found'},
		'any': 		{'past': 'founded'},
	},
	'founds': {
		'singular': {'present': 'founds'},
		'plural': 	{'present': 'found'},
		'any':		{
			'past': 'founded',
			'infinitive': 'found',
		},
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
		'any':		{'infinitive': 'leave'},
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
		'any':		{
			'past':    'sang',
			'infinitive': 'sang',
		},
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
		'any':		{
			'past': 'laid',
			'infinitive': 'lay',
		},
	},
	'laid':  {
		'singular': {'present': 'lays'},
		'plural':	{'present': 'lay'},
		'any':		{
			'past': 'laid',
			'infinitive': 'lay',
		},
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
		'any':		{
			'past': 'escaped',
			'infinitive': 'escape',
		},
	},
	'paid': {
		'singular': {'present': 'pays'},
		'plural':   {'present': 'pay'},
		'any':		{
			'past': 'paid',
			'infinitive': 'pay',
		},
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
	'quitted': {
		'any':		{'past': 'quit'},
	},
	'quit': {
		'any':		{'past': 'quit'},
	},
	'quits': {
		'any':		{'past': 'quit'},
	},
	# 'benefited': {
	# 	'any':		{'past': 'benefitted'},
	# },
	# 'benefitted': {
	# 	'any':		{'past': 'benefitted'},
	# },
	# 'benefit': {
	# 	'any':		{'past': 'benefitted'},
	# },
	# 'benefits': {
	# 	'any': 		{'past': 'benefitted'},
	# },
	'addressed': {
		'any':		{'past': 'addressed'},
	},
	'address': {
		'any':		{'past': 'addressed'},
	},
	'addresses': {
		'any':		{'past': 'addressed'},
	},
	'Addressed': {
		'any':		{'past': 'addressed'},
	},
	'Address': {
		'any':		{'past': 'addressed'},
	},
	'Addresses': {
		'any':		{'past': 'addressed'},
	},
	'paralleled': {
		'singular': {'present': 'parallels'},
		'plural':	{'plural': 'parallel'},
		'any':		{'infinitive': 'parallel'},
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
		'any':		{
			'past': 'sank',
			'infinitive': 'sink',
		},
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
		'any':		{
			'past': 'sprang',
			'infinitive': 'spring',
		},
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
		'any':		{'infinitive': 'favor'},
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
		'any':		{'infinitive': 'endeavor'},
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
		'any':		{
			'past': 'shrank',
			'infinitive': 'shrink',
		},
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
		'any':		{
			'past': 'bit',
			'infinitive': 'bite',
		},
	},
	'bite': {
		'any':		{'past': 'bit'},
	},
	'bites': {
		'any':		{'past': 'bit'},
	},
	'bringest': {
		'any': {
			'past': 'broughtest',
			'infinitive': 'bring'
		},
	},
	'bringeth': {
		'any':		{'infinitive': 'bring'},
	},
	'broughtest': {
		'any': 		{'infinitive': 'bring'},
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
		'any':		{'infinitive': 'mentor'},
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
		'any':		{
			'past': 'wrapped',
			'infinitive': 'wrap',
		},
	},
	'wraps': {
		'singular': {'present': 'wraps'},
		'plural':	{'present': 'wrap'},
		'any':		{
			'past': 'wrapped',
			'infinitive': 'wrap'
		},
	},
	'felled': {
		'singular': {'present': 'fells'},
		'plural': 	{'present': 'fell'},
		'any':		{'infinitive': 'fell'},
	},
	'secret': {
		'any':		{'past': 'secreted'},
	},
	'secrets': {
		'any':		{'past': 'secreted'},
	},
	'teared': {
		'any':		{'past': 'teared'},
	},
	'spirited': {
		'singular': {'present': 'spirits'},
		'plural':	{'present': 'spirit'},
		'any':		{'infinitive': 'spirit'},
	},
	'spirits': {
		'any':		{'past': 'spirited'},
	},
	'spirit': {
		'any':		{'past': 'spirited'},
	},
	'sped': {
		'singular': {'present': 'speeds'},
		'plural': 	{'present': 'speed'},
		'any':		{
			'past': 'sped',
			'infinitive': 'speed',
		},
	},
	'siphoned': {
		'any':		{'past': 'siphoned'},
	},
	'siphons': {
		'any':		{'past': 'siphoned'},
	},
	'siphon': {
		'any':		{'past': 'siphoned'},
	},
	'rang': {
		'singular': {'present': 'rings'},
		'plural': 	{'present': 'ring'},
		'any':		{
			'past': 'rang',
			'infinitive': 'ring',
		},
	},
	'rings': {
		'any':		{'past': 'rang'},
	},
	'ring': {
		'any':		{'past': 'rang'},
	},
	'resubmitted': {
		'any':		{'past': 'resubmitted'},
	},
	'resubmits': {
		'any':		{'past': 'resubmitted'},
	},
	'resubmit': {
		'any':		{'past': 'resubmitted'},
	},
	'rediscovered': {
		'any': 		{'past': 'rediscovered'},
	},
	'rediscovers': {
		'any':		{'past': 'rediscovered'},
	},
	'rediscover': {
		'any':		{'past': 'rediscovered'},
	},
	'gripped': {
		'any':		{'past': 'gripped'},
	},
	'grips': {
		'any':		{'past': 'gripped'},
	},
	'grip': {
		'any':		{'past': 'gripped'},
	},
	'sprung': {
		'singular': {'present': 'springs'},
		'plural': 	{'present': 'spring'},
		'any':		{
			'past': 'sprang',
			'infinitive': 'spring',
		},
	},
	'quoted': {
		'any':		{'past': 'quoted'},
	},
	'quotes': {
		'any':		{'past': 'quoted'},
	},
	'quote': {
		'any':		{'past': 'quoted'},
	},
	'burned': {
		'any':		{'past': 'burned'},
	},
	'burns': {
		'any':		{'past': 'burned'},
	},
	'burn': {
		'any':		{'past': 'burned'},
	},
	'focusses': {
		'any': 		{
			'past': 'focused',
			'infinitive': 'focus',
		},
	},
	'focussed': {
		'any':		{'past': 'focused'},
	},
	'focused': {
		'plural':	{'present': 'focus'},
		'any':		{
			'past': 'focused',
			'infinitive': 'focus',
		},
	},
	'focuses': {
		'any':		{'past': 'focused'},
	},
	'focus': {
		'any':		{'past': 'focused'},
	},
	'fed': {
		'singular': {'present': 'feeds'},
		'plural': 	{'present': 'feed'},
		'any':		{
			'past': 'fed',
			'infinitive': 'feed',
		},
	},
	'feeds': {
		'singular': {'present': 'feeds'},
		'plural':	{'present': 'feed'},
		'any':		{'past': 'fed'},
	},
	'feed': {
		'singular': {'present': 'feeds'},
		'plural': 	{'present': 'feed'},
		'any':		{'past': 'fed'},
	},
	'recovered': {
		'singular': {'present': 'recovers'},
		'plural':	{'present': 'recover'},
		'any':		{'infinitive': 'recover'},
	},
	'willed': {
		'singular': {'present': 'wills'},
		'plural': 	{'present': 'will'},
	},
	'wills': {
		'singular': {'present': 'wills'},
		'plural': 	{'present': 'will'},
	},
	'will': {
		'singular': {'present': 'wills'},
		'plural': 	{'present': 'will'},
	},
	'towered': {
		'any':		{'past': 'towered'},
	},
	'towers': {
		'any':		{'past': 'towered'},
	},
	'tower': {
		'any':		{'past': 'towered'},
	},
	'spoiled': {
		'any':		{'past': 'spoiled'},
	},
	'spoils': {
		'any':		{'past': 'spoiled'},
	},
	'spoil': {
		'any': 		{'past': 'spoiled'},
	},
	'spelled': {
		'singular': {'present': 'spells'},
		'plural':	{'present': 'spell'},
		'any':		{'infinitive': 'spell'},
	},
	'spells': {
		'any':		{'past': 'spelled'},
	},
	'spell': {
		'any':		{'past': 'spelled'},
	},
	'smelled': {
		'any':		{'past': 'smelled'},
	},
	'smells': {
		'any':		{'past': 'smelled'},
	},
	'smell': {
		'any':		{'past': 'smelled'},
	},
	'slimmed': {
		'any':		{'past': 'slimmed'},
	},
	'slims': {
		'any':		{'past': 'slimmed'},
	},
	'slim': {
		'any':		{'past': 'slimmed'},
	},
	'onsold': {
		'singular': {'present': 'onsells'},
		'plural':	{'present': 'onsell'},
		'any':		{
			'past': 'onsold',
			'infinitive': 'onsell',
		},
	},
	'onsells': {
		'any':		{'past': 'onsold'},
	},
	'onsell': {
		'any':		{'past': 'onsold'},
	},
	'roped': {
		'singular': {'present': 'ropes'},
		'plural': 	{'present': 'rope'},
		'any':		{
			'past': 'roped',
			'infinitive': 'rope',
		},
	},
	'redrew': {
		'singular': {'present': 'redraws'},
		'plural': 	{'present': 'redraw'},
		'any':		{
			'past': 'redrew',
			'infinitive': 'redraw',
		},
	},
	'redraws': {
		'any': 		{'past': 'redrew'},
	},
	'redraw': {
		'any':		{'past': 'redrew'},
	},
	'reformed': {
		'singular':	{'present': 'reforms'},
		'plural': 	{'present': 'reform'},
		'any':		{'infinitive': 'reform'},
	},
	'neighbored': {
		'singular': {'present': 'neighbors'},
		'plural':	{'present': 'neighbor'},
		'any':		{'infinitive': 'neighbor'},
	},
	'neighbors': {
		'any':		{'past': 'neighbored'},
	},
	'neighbor': {
		'any':		{'past': 'neighbored'},
	},
	'delimited': {
		'plural': 	{'present': 'delimit'},
		'any':		{'infinitive': 'delimit'},
	},
	'delimits': {
		'plural': 	{'present': 'delimit'},
		'any':		{'infinitive': 'delimit'},
	},
	'delimit': {
		'any':		{'past': 	'delimited'},
	},
	'spilled': {
		'singular': {'present': 'spills'},
		'plural': 	{'present': 'spill'},
		'any':		{'infinitive': 'spill'},
	},
	'spills': {
		'any': 		{'past': 'spilled'},
	},
	'spill': {
		'any':		{'past': 'spilled'},
	},
	'bound': {
		'plural':	{'present': 'bind'},
		'any':		{'infinitive': 'bind'},
	},
	'binds': {
		'plural':	{'present': 'bind'},
		'any':		{'infinitive': 'bind'},
	},
	'bind': {
		'any':		{'past': 'bound'},
	},
	'enrolled': {
		'singular': {'present': 'enrolls'},
	},
	'enrolls': {
		'singular': {'present': 'enrolls'},
	},
	'enroll': {
		'singular': {'present': 'enrolls'},
	},
	'segued': {
		'singular': {'present': 'segues'},
		'plural':	{'present': 'segue'},
		'any':		{'infinitive': 'segue'},
	},
	'segues': {
		'any':		{'past': 'segued'},
	},
	'segue': {
		'any':		{'past': 'segued'},
	},
	'refueled': {
		'any':		{'past': 'refueled'}
	},
	'refuels': {
		'any':		{'past': 'refueled'},
	},
	'refuel': {
		'any':		{'past': 'refueled'},
	},
	'fueled': {
		'any':		{'past': 'fueled'}
	},
	'fuels': {
		'any':		{'past': 'fueled'},
	},
	'fuel': {
		'any':		{'past': 'fueled'},
	},
	'reconnoitered': {
		'any':		{'past': 'reconnoitered'},
	},
	'recoinnoiters': {
		'any':		{'past': 'reconnoitered'},
	},
	'recoinnoiter': {
		'any':		{'past': 'reconnoitered'},
	},
	'plugged': {
		'any':		{'past': 'plugged'},
	},
	'plugs': {
		'any':		{'past': 'plugged'},
	},
	'plug': {
		'any':		{'past': 'plugged'},
	},
	'modeled': {
		'singular': {'present': 'models'},
		'plural':	{'present': 'model'},
		'any':		{'infinitive': 'model'},
	},
	'models': {
		'any': 		{'past': 'modeled'},
	},
	'model': {
		'any': 		{'past': 'modeled'},
	},
	'flexed': {
		'singular': {'present': 'flexes'},
	},
	'flexes': {
		'singular': {'present': 'flexes'},
	},
	'flex': {
		'singular': {'present': 'flexes'},
	},
	'resorted': {
		'singular': {'present': 'resorts'},
		'plural': 	{'present': 'resort'},
		'any':		{'infinitive': 'resort'},
	},
	'tunneled': {
		'singular': {'present': 'tunnels'},
		'plural': 	{'present': 'tunnel'},
		'any':		{'infinitive': 'tunnel'},
	},
	'tunnels': {
		'any':		{'past': 'tunneled'},
	},
	'tunnel': {
		'any':		{'past': 'tunneled'},
	},
	'misspelled': {
		'singular': {'present': 'misspells'},
		'plural':	{'present': 'misspell'},
		'any':		{'infinitive': 'misspell'},
	},
	'misspells': {
		'any':		{'past': 'misspelled'},
	},
	'misspell': {
		'any':		{'past': 'misspelled'},
	},
	'dueled': {
		'any':		{'past': 'dueled'},
	},
	'duels': {
		'any':		{'past': 'dueled'},
	},
	'duel': {
		'any':		{'past': 'dueled'},
	},
	'cowrote': {
		'singular': {'present': 'cowrites'},
		'plural': 	{'present': 'cowrite'},
		'any':		{
			'past': 'cowrote',
			'infinitive': 'cowrite',
		},
	},
	'cowrite': {
		'any':		{'past': 'cowrote'},
	},
	'cowrites': {
		'any':		{'past': 'cowrote'},
	},
	'yodeled': {
		'singular': {'present': 'yodels'},
		'plural': 	{'present': 'yodel'},
		'any':		{'infinitive': 'yodel'},
	},
	'yodels': {
		'any':		{'past': 'yodeled'},
	},
	'yodel': {
		'any':		{'past': 'yodeled'},
	},
	'summon': {
		'any':		{'past': 'summoned'},
	},
	'summoned': {
		'any': 		{'infinitive': 'summon'},
	},
	'summons': {
		'any':		{'infinitive': 'summon'},
	},
	'reinterpreted': {
		'singular':	{'present': 'reinterprets'},
		'plural':	{'present': 'reinterpret'},
		'any':		{'infinitive': 'reinterpret'},
	},
	'reinterpret': {
		'any':		{'past': 'reinterpreted'},
	},
	'reinterprets': {
		'any':		{'past': 'reinterpreted'},
	},
	'regrew': {
		'singular': {'present': 'regrows'},
		'plural': 	{'present': 'regrow'},
		'any':		{
			'past': 'regrew',
			'infinitive': 'regrow',
		},
	},
	'regrow': {
		'any':		{'past': 'regrew'},
	},
	'regrows': {
		'any':		{'past': 'regrew'},
	},
	'penciled': {
		'singular': {'present': 'pencils'},
		'plural':	{'present': 'pencil'},
		'any':		{'infinitive': 'pencil'},
	},
	'pencil': {
		'any':		{'past': 'penciled'},
	},
	'pencils': {
		'any':		{'past': 'penciled'},
	},
	'gossiped': {
		'any':		{'past': 'gossiped'},
	},
	'gossips': {
		'any':		{'past': 'gossiped'},
	},
	'gossip': {
		'any':		{'past': 'gossiped'},
	},
	'funneled': {
		'singular': {'present': 'funnels'},
		'plural': 	{'present': 'funnel'},
		'any':		{'infinitive': 'funnel'},
	},
	'funnel': {
		'any':		{'past': 'funneled'},
	},
	'funnels': {
		'any':		{'past': 'funneled'},
	},
	'critiqued': {
		'singular': {'present': 'critiques'},
		'plural': 	{'present': 'critique'},
		'any':		{'infinitive': 'critique'},
	},
	'critiques': {
		'any': 		{'past': 'critiqued'},
	},
	'critique': {
		'any': 		{'past': 'critiqued'},
	},
	'colored': {
		'singular': {'present': 'colors'},
		'plural': 	{'present': 'color'},
		'any':		{'infinitive': 'color'},
	},
	'color': {
		'any':		{'past': 'colored'},
	},
	'colors': {
		'any':		{'past': 'colored'},
	},
	'counseled': {
		'singular': {'present': 'counsels'},
		'plural': 	{'present': 'counsel'},
		'any':		{'infinitive': 'counsel'},
	},
	'counsel': {
		'any': 		{'past': 'counseled'},
	},
	'counsels': {
		'any':		{'past': 'counseled'},
	},
	'leveled': {
		'singular': {'present': 'levels'},
		'plural': 	{'present': 'level'},
		'any':		{'infinitive': 'level'},
	},
	'levels': {
		'any':		{'past': 'leveled'},
	},
	'level': {
		'any':		{'past': 'leveled'},
	},
	'flied': {
		'plural':	{'present': 'fly'},
		'any':		{
			'past': 'flied',
			'infinitive': 'fly',
		},
	},
	'smites': {
		'any':		{'past': 'smote'},
	},
	'smite': {
		'any':		{'past': 'smote'},
	},
	'smote': {
		'singular': {'present': 'smites'},
		'plural': 	{'present': 'smite'},
		'any':		{'infinitive': 'smite'},
	},
	'reveled': {
		'singular': {'present': 'revels'},
		'plural': 	{'present': 'revel'},
		'any':		{'infinitive': 'revel'},
	},
	'revels': {
		'any':		{'past': 'reveled'},
	},
	'revel': {
		'any':		{'past': 'reveled'},
	},
	'rechristened': {
		'any':		{'past': 'rechristened'},
	},
	'rechristens': {
		'any':		{'past': 'rechristened'},
	},
	'rechristen': {
		'any':		{'past': 'rechristened'},
	},
	'inbreed': {
		'singular': {'present': 'inbreeds'},
		'plural': 	{'present': 'inbreed'},
		'any':		{
			'past': 'inbred',
			'infinitive': 'inbreed',
		},
	},
	'inbreeds': {
		'any': 		{'past': 'inbred'},
	},
	'inbred': {
		'singular': {'present': 'inbreeds'},
		'plural': 	{'present': 'inbreed'},
		'any':		{'infinitive': 'inbred'},
	},
	'homered': {
		'any':		{'past': 'homered'},
	},
	'homers': {
		'any':		{'past': 'homered'},
	},
	'homer': {
		'any':		{'past': 'homered'},
	},
	'emceed': {
		'any':		{'past': 'emceed'},
	},
	'emcees': {
		'any':		{'past': 'emceed'},
	},
	'emcee': {
		'any':		{'past': 'emceed'},
	},
	'fit': {
		'any':		{'past': 'fit'},
	},
	'fits': {
		'any':		{'past': 'fit'},
	},
	'dwelled': {
		'singular': {'present': 'dwells'},
		'plural':	{'present': 'dwell'},
		'any':		{'infinitive': 'dwell'},
	},
	'dwell': {
		'any':		{'past': 'dwelled'},
	},
	'dwells': {
		'any':		{'past': 'dwelled'},
	},
	'extols': {
		'plural': 	{'present': 'extol'},
		'any':		{'infinitive': 'extol'},
	},
	'extolled': {
		'plural':	{'present': 'extol'},
		'any':		{'infinitive': 'extol'},
	},
	'reconvened': {
		'singular': {'present': 'reconvenes'},
		'plural':	{'present': 'reconvene'},
		'any':		{
			'past': 'reconvened',
			'infinitive': 'reconvene',
		},
	},
	'lensed': {
		'singular': {'present': 'lenses'},
		'plural':	{'present': 'lense'},
		'any':		{'infinitive': 'lense'},
	},
	'frescoed': {
		'singular': {'present': 'frescoes'},
	},
	'fresco': {
		'singular': {'present': 'frescoes'},
	},
	'frescoes': {
		'plural': 	{'present': 'fresco'},
		'any':		{
			'past': 'frescoed',
			'infinitive': 'fresco',
		},
	},
	'fulfilled': {
		'singular': {'present': 'fulfills'},
	},
	'fulfill': {
		'singular': {'present': 'fulfills'},
	},
	'fulfills': {
		'singular': {'present': 'fulfills'},
	},
	'meshed': {
		'singular': {'present': 'meshes'},
	},
	'meshes': {
		'singular': {'present': 'meshes'},
	},
	'mesh': {
		'singular': {'present': 'meshes'},
	},
	'greenlit': {
		'singular': {'present': 'greenlights'},
		'plural': 	{'present': 'greenlight'},
		'any':		{
			'past': 'greenlit',
			'infinitive': 'greenlight',
		},
	},
	'countersued': {
		'singular': {'present': 'countersues'},
		'plural': 	{'present': 'countersue'},
		'any':		{'infinitive': 'countersue'},
	},
	'countersues': {
		'any':		{'past': 'countersued'},
	},
	'countersue': {
		'any':		{'past': 'countersued'},
	},
	'distilled': {
		'singular':	{'present': 'distills'},
		'plural':	{'present': 'distill'},
	},
	'distills': {
		'singular':	{'present': 'distills'},
	},
	'distill': {
		'singular':	{'present': 'distills'},
	},
	'rids': {
		'any':		{'past': 'rid'},
	},
	'rid': {
		'any':		{'past': 'rid'},
	},
	'uses': {
		'plural':	{'present': 'use'},
		'any':		{'infinitive': 'use'},
	},
	'use': {
		'any':		{'infinitive': 'use'},
	},
	'used': {
		'plural':	{'present': 'use'},
		'any':		{'infinitive': 'use'},
	},
	'refind': {
		'any':		{'past': 'refound'},
	},
	'refinds': {
		'any':		{'past': 'refound'},
	},
	'enthralled': {
		'singular': {'present': 'enthralls'},
	},
	'enthralls': {
		'singular': {'present': 'enthralls'},
	},
	'enthrall': {
		'singular': {'present': 'enthralls'},
	},
	'traveled': {
		'singular':	{'present': 'travels'},
		'plural':	{'present': 'travel'},
		'any':		{'infinitive': 'travel'},
	},
	'travels': {
		'any':		{'past': 'traveled'},
	},
	'travel': {
		'any':		{'past': 'traveled'},
	},
	'signaled': {
		'singular':	{'present': 'signals'},
		'plural':	{'present': 'signal'},
		'any':		{'infinitive': 'signal'},
	},
	'signals': {
		'any':		{'past': 'signaled'},
	},
	'signal': {
		'any':		{'past': 'signaled'},
	},
	'recreated': {
		'singular': {'present': 'recreates'},
		'plural':	{'present': 'recreate'},
	},
	'reserved': {
		'singular': {'present': 'reserves'},
		'plural': 	{'present': 'reserve'},
	},
	'quarreled': {
		'singular':	{'present': 'quarrels'},
		'plural':	{'present': 'quarrel'},
		'any':		{'infinitive': 'quarrel'},
	},
	'quarrels': {
		'any':		{'past': 'quarreled'},
	},
	'quarrel': {
		'any':		{'past': 'quarreled'},
	},
	'nectared': {
		'singular': {'present': 'nectars'},
		'plural':	{'present': 'nectar'},
		'any':		{'infinitive': 'nectar'},
	},
	'nectars': {
		'any':		{'past': 'nectared'},
	},
	'nectar': {
		'any':		{'past': 'nectared'},
	},
	'marveled': {
		'singular':	{'present': 'marvels'},
		'plural':	{'present': 'marvel'},
		'any':		{'infinitive': 'marvel'},
	},
	'marvels': {
		'any':		{'past': 'marveled'},
	},
	'marvel': {
		'any':		{'past': 'marveled'},
	},
	'labored': {
		'singular': {'present': 'labors'},
		'plural': 	{'present': 'labor'},
		'any':		{'infinitive': 'labor'},
	},
	'labors': {
		'any':		{'past': 'labored'},
	},
	'labor': {
		'any':		{'past':'labored'},
	},
	'labeled': {
		'singular': {'present': 'labels'},
		'plural': 	{'present': 'label'},
		'any':		{'infinitive': 'label'},
	},
	'labels': {
		'any':		{'past': 'labeled'},
	},
	'label': {
		'any':		{'past': 'labeled'},
	},
	'install': {
		'singular': {'present': 'installs'},
	},
	'installed': {
		'singular': {'present': 'installs'},
	},
	'equalled': {
		'singular': {'present': 'equals'},
		'plural': 	{'present': 'equal'},
		'any':		{'infinitive': 'equal'},
	},
	'dreamed': {
		'any':		{'past': 'dreamed'},
	},
	'dreams': {
		'any': 		{'past': 'dreamed'},
	},
	'dream': {
		'any':		{'past': 'dreamed'},
	},
	'ciliated': {
		'singular': {'present': 'ciliates'},
		'plural':	{'present': 'ciliate'},
		'any':		{'infinitive': 'ciliate'},
	},
	'chickened': {
		'any':		{'past': 'chickened'},
	},
	'chickens': {
		'any':		{'past': 'chickened'},
	},
	'chicken': {
		'any':		{'past': 'chickened'},
	},
	'cataloged': {
		'singular': {'present': 'catalogs'},
		'plural': 	{'present': 'catalog'},
		'any':		{'infinitive': 'catalog'},
	},
	'catalog': {
		'any':		{'past': 'cataloged'},
	},
	'catalogs': {
		'any':		{'past': 'cataloged'},
	},
	'bypass': {
		'singular':	{'present': 'bypasses'},
	},
	'bypassed': {
		'singular':	{'present': 'bypasses'},
	},
	'bypasses': {
		'singular': {'present': 'bypasses'},
	},
	'authored': {
		'singular': {'present': 'authors'},
		'plural':	{'present': 'author'},
		'any':		{'infinitive': 'author'},
	},
	'authors': {
		'any':		{'past': 'authored'},
	},
	'author': {
		'any':		{'past': 'authored'},
	},
	'coached': {
		'singular':	{'present': 'coaches'},
	},
	'coach': {
		'singular': {'present': 'coaches'},
	},
	'coaches': {
		'singular': {'present': 'coaches'},
	},
	'learned': {
		'any':		{'past': 'learned'},
	},
	'learn': {
		'any':		{'past': 'learned'},
	},
	'learns': {
		'any':		{'past': 'learned'},
	},
	'unraveled': {
		'singular':	{'present': 'unravels'},
		'plural': 	{'present': 'unravel'},
		'any':		{'infinitive': 'unravel'},
	},
	'unravels': {
		'any':		{'past': 'unraveled'},
	},
	'unravel': {
		'any':		{'past': 'unraveled'},
	},
	'spiraled': {
		'singular': {'present': 'spirals'},
		'plural': 	{'present': 'spiral'},
		'any':		{'infinitive': 'spiral'},
	},
	'spirals': {
		'any':		{'past': 'spiraled'},
	},
	'spiral': {
		'any':		{'past': 'spiraled'},
	},
	'leaned': {
		'singular': {'present': 'leans'},
		'plural': 	{'present': 'lean'},
		'any':		{'infinitive': 'lean'},
	},
	'leans': {
		'any':		{'past': 'leaned'},
	},
	'lean': {
		'any': 		{'past': 'leaned'},
	},
	'harbored': {
		'singular': {'present': 'harbors'},
		'plural': 	{'present': 'harbor'},
		'any':		{'infinitive': 'harbor'},
	},
	'harbor': {
		'any':		{'past': 'harbored'},
	},
	'harbors': {
		'any': 		{'past': 'harbored'},
	},
	'crossbred': {
		'singular': {'present': 'crossbreeds'},
		'plural': 	{'present': 'crossbreed'},
		'any':		{'infinitive': 'crossbreed'},
	},
	'crossbreeds': {
		'any':		{'past': 'crossbred'},
	},
	'crossbreed': {
		'singular': {'present': 'crossbreeds'},
		'plural': 	{'present': 'crossbreed'},
		'any':		{
			'past': 'crossbred',
			'infinitive': 'crossbreed',
		},
	},
	'canceled': {
		'singular': {'present': 'cancels'},
		'plural': 	{'present': 'cancel'},
		'any':		{'infinitive': 'cancel'},
	},
	'cancels': {
		'any':		{'past': 'canceled'},
	},
	'cancel': {
		'any':		{'past': 'canceled'},
	},
	'canned': {
		'singular': {'present': 'cans'},
		'plural': 	{'present': 'can'},
		'any':		{'past': 'canned'},
	},
	'cans': {
		'singular': {'present': 'cans'},
		'any':		{'past': 'canned'},
	},
	'surveilled': {
		'singular': {'present': 'surveils'},
		'plural': 	{'present': 'surveil'},
		'any':		{
			'past': 'surveiled',
			'infinitive': 'surveil',
		},
	},
	'surveil': {
		'any':		{'past': 'surveiled'},
	},
	'surveils': {
		'any':		{'past': 'surveiled'},
	},
	'rivaled': {
		'singular':	{'present': 'rivals'},
		'plural':	{'present': 'rival'},
		'any':		{'infinitive': 'rival'},
	},
	'rivals': {
		'any':		{'past': 'rivaled'},
	},
	'rival': {
		'any':		{'past': 'rivaled'},
	},
	'quarterbacked': {
		'singular': {'present': 'quarterbacks'},
		'plural': 	{'present': 'quarterback'},
		'any':		{
			'past':	'quarterbacked',
			'infinitive': 'quarterbacked',
		},
	},
	'underbilled': {
		'singular': {'present': 'underbills'},
		'plural': 	{'present': 'underbill'},
		'any':		{'infinitive': 'underbill'},
	},
	'channeled': {
		'singular': {'present': 'channels'},
		'plural': 	{'present': 'channel'},
		'any': 		{'infinitive': 'channel'},
	},
	'channels': {
		'any':		{'past': 'channeled'},
	},
	'channel': {
		'any':		{'past': 'channeled'},
	},
	'summited': {
		'singular': {'present': 'summits'},
		'plural': 	{'present': 'summit'},
		'any':		{'infinitive': 'summit'},
	},
	'summits': {
		'any':		{'past': 'summited'},
	},
	'summit': {
		'any':		{'past': 'summited'},
	},
	'wyed': {
		'singular': {'present': 'wyes'},
		'plural':	{'present': 'wye'},
		'any':		{
			'past': 'wyed',
			'infinitive': 'wye',
		},
	},
	'outspent': {
		'singular':	{'present': 'outspends'},
		'plural':	{'present': 'outspend'},
		'any':		{
			'past': 'outspent',
			'infinitive': 'outspend',
		},
	},
	'outspends': {
		'any':		{'past': 'outspent'},
	},
	'outspend': {
		'any':		{'past': 'outspent'},
	},
	'pastored': {
		'singular': {'present': 'pastors'},
		'plural':	{'present': 'pastor'},
		'any':		{'infinitive': 'pastor'},
	},
	'pastors': {
		'any':		{'past': 'pastored'},
	},
	'pastor': {
		'any':		{'past': 'pastored'},
	},
	'stank': {
		'singular': {'present': 'stinks'},
		'plural': 	{'present': 'stink'},
		'any':		{
			'past': 'stank',
			'infinitive': 'stink',
		},
	},
	'stinks': {
		'any':		{'past': 'stank'},
	},
	'stink': {
		'any':		{'past': 'stank'},
	},
	'totaled': {
		'singular': {'present': 'totals'},
		'plural':	{'present': 'total'},
		'any':		{'infinitive': 'total'},
	},
	'totals': {
		'any':		{'past': 'totaled'},
	},
	'total': {
		'any':		{'past': 'totaled'},
	},
	'lambaste': {
		'singular': {'present': 'lambastes'},
	},
	'lambastes': {
		'singular': {'present': 'lambastes'},
	},
	'lambasted': {
		'singular': {'present': 'lambastes'},
	},
	'reawakens': {
		'any': 		{'past': 'reawakened'},
	},
	'reawaken': {
		'any':		{'past': 'reawakened'},
	},
	'spotlighted': { # spotlighted is way more common than spotlit
		'any':		{'past': 'spotlighted'},
	},
	'spotlights': {
		'any':		{'past': 'spotlighted'},
	},
	'spotlight': {
		'any':		{'past': 'spotlighted'},
	},
	'broadcasts': {
		'any':		{'past': 'broadcast'},
	},
	'broadcast': {
		'any':		{'past': 'broadcast'},
	},
	'handmade': {
		'singular': {'present': 'handmakes'},
		'plural': 	{'present': 'handmake'},
		'any':		{
			'past': 'handmade',
			'infinitive': 'handmake',
		},
	},
	'handmakes': {
		'any':		{'past': 'handmade'},
	},
	'handmake': {
		'any':		{'past': 'handmade'},
	},
	'interfingered': {
		'any':		{'past': 'interfingered'},
	},
	'interfingers': {
		'any':		{'past': 'interfingered'},
	},
	'interfinger': {
		'any':		{'past': 'interfingered'},
	},
	'unzoned': {
		'singular': {'present': 'unzones'},
		'plural': 	{'present': 'unzone'},
		'any':		{
			'past': 'unzoned',
			'infinitive': 'unzone',
		},
	},
	'trialled': { # the one time it doesn't love doubled ls
		'singular': {'present': 'trials'},
		'plural': 	{'present': 'trial'},
		'any':		{
			'past': 'trialled',
			'infinitive': 'trial',
		},
	},
	'simulcasts': {
		'any':		{'past': 'simulcast'},
	},
	'simulcast': {
		'any':		{'past': 'simulcast'},
	},
	'unenrolled': {
		'singular': {'present': 'unenrolls'},
		'plural':	{'present': 'unenroll'},
		'any':		{'infinitive': 'unenroll'},
	},
	'hyped': {
		'singular': {'present': 'hypes'},
		'plural': 	{'present': 'hype'},
		'any':		{
			'past': 'hyped',
			'infinitive': 'hype',
		},
	},
	'forecast': {
		'any': 		{'past': 'forecast'},
	},
	'forecasts': {
		'any':		{'past': 'forecast'},
	},
	'remastered': {
		'any':		{'past': 'remastered'},
	},
	'remasters': {
		'any':		{'past': 'remastered'},
	},
	'remaster': {
		'any':		{'past': 'remastered'},
	},
	'wrought': {
		'singular': {'present': 'works'},
		'plural': 	{'present': 'work'},
		'any':	{
			'past': 'wrought',
			'infinitive': 'work',
		},
	},
	'discolored': {
		'singular': {'present': 'discolors'},
		'plural': 	{'present': 'discolor'},
		'any':		{'infinitive': 'discolor'},
	},
	'discolors': {
		'any':		{'past': 'discolored'},
	},
	'discolor': {
		'any':		{'past': 'discolored'},
	},
	'parceled': {
		'singular': {'present': 'parcels'},
		'plural': 	{'present': 'parcel'},
		'any':		{'infinitive': 'parcel'},
	},
	'parcels': {
		'any':		{'past': 'parceled'},
	},
	'parcel': {
		'any':		{'past': 'parceled'},
	},
	'stenciled': {
		'singular': {'present': 'stencils'},
		'plural': 	{'present': 'stencil'},
		'any':		{'infinitive': 'stencil'},
	},
	'stencils': {
		'any': 		{'past': 'stenciled'},
	},
	'stencil': {
		'any':		{'past': 'stenciled'},
	},
	'halts': {
		'plural': 	{'present': 'halt'},
		'any':		{'infinitive': 'halt'},
	},
	'halted': {
		'plural': 	{'present': 'halt'},
		'any':		{'infinitive': 'halt'},
	},
	'gelded': {
		'any':		{'past': 'gelded'},
	},
	'gelds': {
		'any':		{'past': 'gelded'},
	},
	'geld': {
		'any':		{'past': 'gelded'},
	},
	'crossovered': {
		'any':		{'past': 'crossovered'},
	},
	'crossovers': {
		'any':		{'past': 'crossovered'},
	},
	'crossover': {
		'any':		{'past': 'crossovered'},
	},
	'haltered': {
		'singular': {'present': 'halters'},
		'plural': 	{'present': 'halter'},
		'any':		{
			'past': 'haltered',
			'infinitive': 'halter',
		},
	},
	'halters': {
		'singular': {'present': 'halters'},
		'plural': 	{'present': 'halter'},
		'any':		{
			'past': 'haltered',
			'infinitive': 'halter',
		},
	},
	'halter': {
		'singular': {'present': 'halters'},
		'plural': 	{'present': 'halter'},
		'any':		{
			'past':	'haltered',
			'infinitive': 'halter',
		},
	},
	'wet': {
		'any':		{'past': 'wet'},
	},
	'wets': {
		'any':		{'past': 'wet'},
	},
	'upsprang': {
		'singular': {'present': 'upsprings'},
		'plural': 	{'present': 'upspring'},
		'any':		{
			'past': 'upsprang',
			'infinitive': 'upspring',
		},
	},
	'upsprings': {
		'any':		{'past': 'upsprang'},
	},
	'upspring': {
		'any':		{'past': 'upsprang'},
	},
	'counterargued': {
		'singular': {'present': 'counterargues'},
		'plural': 	{'present': 'counterargue'},
		'any':		{'infinitive': 'counterargue'},
	},
	'counterargues': {
		'any':		{'past': 'counterargued'},
	},
	'counterargue': {
		'any':		{'past': 'counterargued'},
	},
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
	'installed': 'install',
	'enrolled': 'enroll',
	'got': 'get',
	'resubmitted': 'resubmit',
	'reentered': 'reenter',
	'reconnected': 'reconnect',
	'reburied': 'rebury',
	'prepped': 'prep',
	'petered': 'peter',
	'overbilled': 'overbill',
	'minored': 'minor',
	'inclouded': 'incloud',
	'comped': 'comp',
	'cofounded': 'cofound',
	'bricked': 'brick',
	'blogged': 'blog',
	'deeded': 'deed',
	'shinnied': 'shinny',
	'remodelled': 'remodel',
	'reenvisioned': 'reenvision',
	'recommissioned': 'recommission',
	'powerbombed': 'powerbomb',
	'ingressed': 'ingress',
	'extoll': 'extol',
	'bidded': 'bid', # wrong in the dataset, but we'll fix the lemma
	'wove': 'weave',
	'slimmed': 'slim',
	'remixed': 'remix',
	'optioned': 'option',
	'interwove': 'interweave',
	'outgunned': 'outgun',
	'reused': 'reuse',
	'unwound': 'unwind',
	'overviewed': 'overview',
	'outsprinted': 'outsprint',
	'reoccupied': 'reoccupy',
	'reoccupies': 'reoccupy',
	'reenlisted': 'reenlist',
	'rechristened': 'rechristen',
	'preselected': 'preselect',
	'gusted': 'gust',
	'flied': 'fly', # used in "flied out"
	'chested': 'chest',
	'vectored': 'vector',
	'uncensored': 'uncensor',
	'stress': 'stress', # due to typo
	'misprojected': 'misproject',
	'misidentified': 'misidentify',
	'decisioned': 'decision',
	'cowrote': 'cowrite',
	'bless': 'bless', # misidentified as 'bles'
	'extolled': 'extol',
	'russified': 'russify',
	'russifies': 'russify',
	'relaunched': 'relaunch',
	'relaunches': 'relaunch',
	'refounded': 'refound',
	'enthralled': 'enthrall',
	'doublecrossed': 'doublecross',
	'doublecrosses': 'doublecross',
	'distilled': 'distill',
	'draghunted': 'draghunt',
	'outdueled': 'outduel',
	'surveilled': 'surveil',
	'retasked': 'retask',
	'readied': 'ready',
	'underbilled': 'underbill',
	'outspent': 'outspend',
	'mindmelded': 'mindmeld',
	'reinvested': 'reinvest',
	'pastored': 'pastor',
	'retweeted': 'retweet',
	'handmade': 'handmake',
	'rejigged': 'rejig',
	'interfingered': 'interfinger',
	'coauthored': 'coauthor',
	'deputied': 'deputy',
	'deputies': 'deputy',
	'efforted': 'effort',
	'unenrolled': 'unenroll',
	'photobombed': 'photobomb',
	'reteamed': 'reteam',
	'inflowed': 'inflow',
	'simulcasted': 'simulcast',
	'remastered': 'remaster',
	'backstabbed': 'backstab',
	'podiumed': 'podium',
	'inbounded': 'inbound',
	'dormed': 'dorm',
	'cordoned': 'cordon',
}

HOMOPHONOUS_VERBS: Dict[str,Dict[str,Dict[str,Dict[str,Union[str,Callable]]]]] = {
	'lay': {
		'singular': {'present': 'lies'}, 
		'plural': 	{'present': 'lie'},
		'any':		{'infinitive': 'lie'},
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
		'any':		{'infinitive': 'secret'},
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
		'singular': {'present': 'fells'},
		'plural': 	{'present': 'fell'},
		'any':		{
			'past': 'felled',
			'infinitive': 'fell',
		},
		'condition':(lambda t: t.is_transitive),
	},
	'speed': {
		'any': 		{'past': 'sped'},
		'condition': (lambda t: t.is_intransitive)
	},
	'speeds': {
		'any':		{'past': 'sped'},
		'condition': (lambda t: t.is_intransitive),
	},
	'can': {
		'any':		{'past': 'canned'},
		'condition': (lambda t: not t.is_aux),
	},
	'knewest': {
		'any':		{
			'present': 'knoweth',
			'past': 'knewest',
		},
		'condition': (
			lambda t: 
				t.subject.text.lower() == 'thou' 
				if not isinstance(t.subject,list) 
				else any(word.text.lower() == 'thou' for word in t.subject)
			)
	},
	'fit': {
		'any':		{'past': 'fitted'},
		'condition': (
				lambda t:
					any(word.text == 'out' for word in t.children)
			)
	},
	'fits': {
		'any':		{'past': 'fitted'},
		'condition': (
				lambda t:
					any(word.text == 'out' for word in t.children)
			)
	},
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

# determiners that spaCy parses as amods
AMOD_DETERMINERS: Set[str] = {
	'many',
	'Many',
	'few',
	'Few',
	'fewer',
	'Fewer'
}

# spaCy doesn't assign the right morphs to these words
INCORRECT_MORPHS: Dict[str,Dict[str,str]] = {
	'was' : {'Number': 'Sing'},
	'were': {'Number': 'Plur'},
	'is'  : {'Number': 'Sing'},
	'are' : {'Number': 'Plur'},
	'Many': {'Number': 'Plur'},
	'many': {'Number': 'Plur'},
	'Fewer': {'Number': 'Plur'},
	'fewer': {'Number': 'Plur'},
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
	'another': {'Number': 'Sing'},
	'They': {'Number': 'Plur'},
	'they': {'Number': 'Plur'},
	'Luxembourg': {'Number': 'Sing'},
	'Somewhere': {'Number': 'Sing'},
	'somewhere': {'Number': 'Sing'},
	'rhyme': {'Number': 'Sing'},
	'Rhyme': {'Number': 'Sing'},
	'Diverse': {'Number': 'Plur'},
	'diverse': {'Number': 'Plur'},
	'matte': {'Number': 'Sing'},
	'Matte': {'Number': 'Sing'},
	'theca': {'Number': 'Sing'},
	'Various': {'Number': 'Plur'},
	'various': {'Number': 'Plur'},
	'oneself': {'Case': 'Acc', 'Number': 'Sing', 'Person': '3', 'Reflex': 'Yes'},
	'thee': {'Number': 'Sing', 'Case': 'Acc', 'Person': '2'},
	'thou': {'Number': 'Sing', 'Case': 'Nom', 'Person': '2'},
	'Thou': {'Number': 'Sing', 'Case': 'Nom', 'Person': '2'},
	'shiurim': {'Number': 'Plur'},
	'Shiurim': {'Number': 'Plur'},
	'Heteroptera': {'Number': 'Plur'},
	'heteroptera': {'Number': 'Plur'},
	**{ordinal: {'Number': 'Sing'} for ordinal in ORDINALS},
}

# when adjectives are used as nouns, 
# some are associated with particular numbers (though not all)
# we look these up here
NUMBERS_FOR_ADJECTIVES_USED_AS_NOUNS: Dict[str,str] = {
	'needy': 'Plur',
	'disabled': 'Plur',
	'poor': 'Plur',
	'final': 'Sing',
	'other': 'Sing',
	'French': 'Plur',
	'straight': 'Sing',
	'secondary': 'Sing',
	'young': 'Plur',
	'moneyed': 'Plur',
	'ceramic': 'Sing',
	'occult': 'Sing',
	'fundamental': 'Sing',
	'wounded': 'Plur',
	'bankrupt': 'Plur',
	'common': 'Sing',
	'tributary': 'Sing',
	'unemployed': 'Plur',
	'infected': 'Plur',
	'programming': 'Sing',
	# "dead" is usually Plur, though not always. 
	# it's better to have this as the default, though
	'dead': 'Plur',
	'faithful': 'Plur',
}

INCORRECT_MORPHS_PRESENT_TENSE: Dict[str,Dict[str,str]] = {
	'say': {'Number': 'Plur'},
	'have': {'Number': 'Plur'},
	'remain': {'Number': 'Plur'},
}

# maps a partitive to the word used to
# introduce the real head
# in most cases, this will be 'of',
# but this overrides that
PARTITIVES_P_MAP: Set[str] = {
	'latest': ['in','of'],
	'newest': ['in','of'],
	'recent': ['in','of'],
}

# partitives are things where the head noun of the subject
# is NOT what the verb is supposed to agree with
# note that this does not necessarily cover all actual partitives
PARTITIVES_WITH_P: Set[str] = {
	'Some',
	'some',
	'Any',
	'any',
	'latest',
	'newest',
	'recent',
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
PARTITIVES_OPTIONAL_P: Set[str] = {
	'All',
	'all',
	'Half',
	'half',
	'Most',
	'most',
	'More',
	'more',
	# unlike other ordinals, first can
	# be singular or plural
	'First',
	'first',
	'Last',
	'last',
	'Any',
	'any',
	'Enough',
	'enough',
}

# these are partitives when they have an indefinite
# determiner. Otherwise, they are normal nouns
PARTITIVES_WITH_INDEFINITE_ONLY: Set[str] = {
	'amount',
	'group',
	'lot',
	'number', 
	# n.b. number and lot are weird: a number of ... 
	# is always plural (if used as a partitive)
	# but others here aren't
	'quantity',
	'ton',
	'series',
	'array',
}

ALL_PARTITIVES: Set[str] = {
	*PARTITIVES_WITH_P,
	*PARTITIVES_OPTIONAL_P,
	*PARTITIVES_WITH_INDEFINITE_ONLY
}

# maps some deps to others for purposes
# of recording distractor structures
STRUCTURE_MAP: Dict[str,str] = {
	'prep': 		'PP', # prepositional phrase
	'pcomp': 		'PP',
	'pobj': 		'PP', 
	'relcl': 		'RC', # relative clause
	'acl': 			'CC', # clausal complement (e.g., Paula, seeing him there, ...)
	'ccomp': 		'CC',
	'npadvmod': 	'AdvP', # preverbal adverbial modifier (The school each year goes...)
	'advmod': 		'AdvP', # adverbial modifier
	'advcl': 		'AdvP',
	'acomp':	 	'AdvP',
	'amod':			'AP',
	'appos': 		'ParenP',
	'parataxis': 	'ParenP',
	'cc': 			'ConjP', # all of them but that guy ...
	'quantmod':		'QP',
	'nummod':		'NumP',
}

# dependencies to exclude when determining agreement attraction
EXCLUDE_DEPS: Set[str] = {
	'nsubj',
	'xcomp',
	'agent',
	'dobj',
	'conj',
	'oprd',
	'dative',
	'nsubjpass', # due to misparses
	'attr',
	'dep', # due to misparses
	'punct', # non-restrictive clauses and some appositives
	'prt', # particles
	'mark', # spaCy says "marker" ???
	'nmod',
	'nummod',
	'quantmod',
	'compound', # these are part of the same noun phrase
}

# list of valid distractor structures
# DISTRACTOR_STRUCTURES: Set[str] = {
# 	'CP',
# 	'PP',
# }

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

Q_DO = dict(
	text 	= 'do',
	tag_ 	= 'VBP',
	pos_ 	= 'AUX',
	morph 	= 'Mood=Ind|Tense=Pres|VerbForm=Fin|Number=Plur',
	lemma_ 	= 'do',
	dep_ 	= 'aux',
)

INFLECTED_AUXES: Set[str] = {
	'be',
	'have',
	'get',
	'do',
}