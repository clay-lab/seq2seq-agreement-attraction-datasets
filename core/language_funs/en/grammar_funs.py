import re
import sys
import string
import random
import logging
import traceback

from typing import Dict, Set, Union

from ..language_funs import string_conditions
from ...spacyutils import nlp, EDoc, flatten
from ...constants import *

log = logging.getLogger(__name__)

EN_STOP_STRINGS: Set[str] = {
	'-',
	':',
	*[str(n) for n in range(10)], # digits, 0–9
	'–', # ndash, separates numbers (which we don't want)
	'—', # mdash, can separate two independent sentences
	'(',
	')',
	'[',
	']',
	'{',
	'}', # delimiters do weird things with sentence structures
	'is in length', # missing measure
	'criterionif', # typo
	'out put', # typo
	'instalment', # typo
	'DThat', # typo
	' thevar ', # typo
	'thenproceeded',
}

# no things that only occur as prefixes
# if they are separated from the verb by
# a space. spaCy does weird things with
# these that we don't want. this will also
# exclude co as an abbreviation without a trailing
# period, but that's acceptable
EN_EXCLUDE_REGEXES: Set[str] = {
	r'(^|\s)(re|pre|co|dis|un|mis|mal)\s',
	r'(^|\s)(Re|Pre|Co|Dis|Un|Mis|Mal)\s',
}

EN_ABBREVIATIONS: Set[str] = {
	'Prof.',
	'Blvd.',
	'Mrs.',
	'Ave.',
	'Ltd.',
	'Inc.',
	'Mr.',
	'Dr.',
	'Ms.',
	'St.',
	'Av.',
	'no.',
	'No.',
	'approx.',
	'Approx.',
	'C.',
	'c.',
	'ca.',
	'Ca.',
	'Ps.',
	'ps.',
	'Col.',
	'col.',
	'Lt.',
	'lt.',
	'Gen.',
	'gen.',
	'Pvt.',
	'pvt.',
	'Pfc.',
	'pfc.',
	'Spc.',
	'spc.',
	'Cpl.',
	'cpl.',
	'Sgt.',
	'sgt.',
	'Sen.',
	'sen.',
	'Rep.',
	'rep.',
	'Ssg.',
	'ssg.',
	'Sfc.',
	'sfc.',
	'Msg.',
	'msg.',
	'Sgm.',
	'sgm.',
	'Csm.',
	'csm.',
	'Sma.',
	'sma.',
	'Cpt.',
	'Capt.',
	'cpt.',
	'capt.',
	'Maj.',
	'maj.',
	'Ltc.',
	'ltc.',
	'Bg.',
	'bg.',
	'Mg.',
	'mg.',
	'Ltg.',
	'ltg.',
	'Ga.',
	'ga.',
	'Brig.',
	'brig.',
	'Hon.',
	'hon.',
	'Nos.',
	'nos.',
	'Govt.',
	'govt.',
	'var.',
	'Var.',
	'Ste.',
	'ste.',
	'Vs.',
	'vs.',
	'Dir.',
	'dir.',
	'www.',
	'Fr.',
	'fr.',
	'Sr.',
	'sr.',
	'Vol.',
	'vol.',
	'Ft.',
	'ft.',
	'Ph.',
	'ph.',
	'oosp.',
	'Oosp.',
	'Dist.',
	'dist.',
	'Jr.',
	'jr.',
	'Subsp.',
	'subsp.',
	'Ul.',
	'ul.',
	'Po.',
	'po.',
	'Mfg.',
	'mfg.',
	'Ven.',
	'ven.',
	'Chr.',
	'chr.',
	'Rd.',
	'rd.',
	'Sci.',
	'sci.',
	'Univ.',
	'univ.',
	'Chr.',
	'chr.',
	'Cdr.',
	'cdr.',
	'Sc.',
	'sc.',
	'sp.',
	'Sp.',
	'Sts.',
	'sts.',
	'Rev.',
	'rev.',
	'ver.',
	'Ver.',
	'P.',
	'p.',
	'al.',
	'ibid.',
	'Incl.',
	'incl.',
	'Tr.',
	'tr.',
}

MISPARSED_AS_VERBS: Set[str] = {
	'swans', # this should be a noun, but spaCy has misparsed it
			 # as a verb in 'Trumpeter swans winter along the upper Stuart.'
	'it', # don't know, but clearly wrong
	'debouche', # french
	'o', # don't know, but it's clearly wrong
	'in', # don't know, but it's clearly wrong
	'erinnert', # german
	'erinnern', # german
	'braucht', # german
	'te', # german
	'up', # not actually wrong, but misparsed as the verb in "level up"
	'between',
	'entdeckted', # probably German?,
	'zieht', # german
	'werde', # german
	'orestes', # species name
	'ist', # german
	'coeloms', # ???
	'durchs', # german
	'gelebten', # german
	'wird', # german
	'migliori', # italian
	'gegen', # german
	'haben', # german
	'culminans', # species name
	'geklebt', # german
	'baute', # german
	'luridus',
	'og',
	'naped', # adj
}

COMMON_VERB_TYPOS: Set[str] = {
	'where', # from were
	'seee', # from seee
	'lieas', # from lies
	'a', # from are (only used if it's a verb, so no worries about determiners)
	'ia' # from is
	'vere', # from veer
	'prevee', # ????
	'tooj', # from took
	'wnt', # from want
	'wonn', # from won
	'competied', # from compete
	'competies', # from compete
	'competended', # no idea
	'competends',
	'competend',
	'thik', # for think
	'residens', # for reside
	'liesin', # for lies in
	'legendnto', # for ???
	'Its', # for It's
	'isis', # for is
	'comprices', # for comprises
	'cincludes', # for includes
	'buit', # for built
	'bidded', # for bid
	'wereFK', # for were
	'superwised', # for supervised
	'ses', # for sees
	'reregisted', # for reregistered
	'getup', # for get up
	'though', # for 'thought'
	'sung', # for 'sang'
	'funktions', # typo of function
	'funktion',
	'funktioned',
	'stupified', # typo of stupefy
	'stupify',
	'stupifies',
	'pretent', # pretend
	'pretents'
	'pretented',
	'discluded', # non-standard
	'discludes',
	'disclude',
	'discides', # descide
	'discide',
	'discided'
	'composee', # compose
	'composees',
	'composeed'
	'mispell', # misspell
	'mispells',
	'mispelled',
	'mispelt',
	'councils', # counsel
	'council',
	'councilled',
	'constitutie', # constitute
	'constituties',
	'constitutied',
	'studei', # study
	'studeis',
	'studeid', 
	'lise', # lies
	'iis', # is
	'solified', # solidify
	'solifies',
	'solify',
	'sered', # serve 
	'seres',
	'sere',
	'openin', # open
	'openins',
	'openined',
	'ive', # live
	'ived',
	'ives',
	'indroduce', # introduce
	'indroduces',
	'indroduced',
	'formd', # formed
	'envolves', # involve
	'envolve',
	'envolved',
	'enroutes', # not a verb
	'enrouted',
	'enroute',
	'devize', # devised
	'devizes',
	'devized',
	'cliched', # clinched
	'clich',
	'cliches',
	'benifted', # benefit
	'benifte',
	'beniftes',
	'tooks', # took
	'publisher', # published
	'its', # it's
	'employees', # employs
	'composeed', # composed
	'wons', # wins
	'shited', # shifted
	'quietened', # quieted
	'includeds', # included or includes
	'beings', # begins
	'being',
	'wss', # was
	'undergoe', # undergo
	'stoodout', # stood out
	'pubescens', # species name
	'os', # is
	'his', # is
	'exempiflied', # exemplify 
	'exempiflies',
	'exempifly',
	'cronicled', # chronicle
	'cronicles',
	'cronicle',
	'rippen', # ripen
	'rippens',
	'rippened',
	'rippenned',
	'fulfils', # fulfill
	'fulfil',
	'fulfiled',
	'signe', # signed
	'enrcircled', # encircle
	'enrcircle',
	'enrcircles',
	'withnessed', # witness
	'withnesses',
	'withness', 
	'wittnesed', # witness
	'wittnessed',
	'wittneses',
	'wittnesses',
	'wittnes'
	'wittnese',
	'wittness',
	'knewest', # too old
	'art',
	'broughtest',
	'knoweth',
	'bringest',
	'showscase', # showcase
	'showscased',
	'showscases',
	'rseignate', # resign?
	'rseignates',
	'rseignated',
	'mimick', # mimic
	'mimicks',
	'enquire', # inquire
	'enquires',
	'enquired',
	'clambe', # clamber/clam?
	'clamb',
	'clambs',
	'manufacturer', # manufacture
	'manufacturers',
	'manufacturered',
	'manufacturerred',
	'maddes', #???
	'madde', # made
	'feaured', # features
	'feaures',
	'we', # were?
	'throughs', # ???
	'throughed',
	'roled', # rolled?
	'role', 
	'reuss', # ???
	'consistes', # consist
	'consiste',
	'withs', # ??? 
	'withed',
	'with'
	'wase', # was
	'starrd', # starred
	'shrunk', # shrank
	'recaived', # received
	'recaives',
	'recaive',
	'diversied', # diversify
	'diversies',
	'diversy',
	'encompases', # encompass
	'encompased',
	'encompas',
	'showns', # showed
	'shown',
	'showned',
	'prophecied', # prophesy
	'prophecies',
	'prophecy',
	'inahabits', # inhabit
	'inahabited',
	'inahabitted',
	'inahabit',
	'ia', # is
	'old', # hold
	'olds',
	'eld'
	'hed', # had
	'filmmed', # film
	'filmms',
	'filmm',
	'despatches', # dispatch
	'despatch',
	'despatched',
	'waseducated', # was educated
	'meert', # meet
	'forbad', # forbade
	'seeme', # seem
	'seemes',
	'resemblies', # resemble
	'resemblie',
	'resemblied',
	'happeed', # happen
	'happees',
	'happee',
	'plaed', # play
	'descent', # descend
	'descents',
	'descented', 
	'pawne', # pawn
	'pawnes',
	'pas', # pass, was
	'haulted', # halt
	'haults',
	'hault',
	'spe', # spent
	'traveses', # traverse
	'travese',
	'travesed',
	'drow', # draw
	'drows', 
	'starr', # star
	'starrs',
	'asume', # assume
	'asumes',
	'asumed',
	'ar', # are
	'incloud', # include
	'inclouded',
	'inclouds',
	'resode', # reside
	'resoded',
	'resodes',
	'conductd', # conducted
	'showcast', # showcase
	'showcasts',
	'showcastd',
	'world', # worked
	'strived', # should be strove
}

BAD_VERB_LEMMAS: Set[str] = {
	'focu', # due to a typo of "focuses"
	'stupifie',
	'funktion',
	'scollop', # ???
	'disclude',
	'pretente',
	'council', # counsel
	'showscase', # showcase
	'rseignate', # resign?
	'plat', # plate?
	'madde', # made
	'feaure', # feature
	'evangalise', # evangelize
	'evangalize',
	'clambe', # clamber?
	'ate', # eat
	'we', # were?
	'through', # ???
	'withnesse',
	'wittnese',
	'outduele',
	'erinnern', # german
	'with', # ???
	'wase', # was
	'starrd', # starred
	'diversie',
	'old', # hold
	'he', # typo of had as hed
	'filmme',
	'despatch', # dispatch
	'waseducate', # typo
	'meert', # meet
	'forbad', # forbade
	'tricarinate', # an adjective
	'seeme', # seem
	'resemblie', # resemble
	# not actually bad, but it does 
	# weird things with its object in the
	# "definition" meaning (e.g.,
	# always singular, even if plural bc of use-mention
	# distinction. let's just avoid it)
	'mean',
	'happee', # happen
	'plae', # play
	'og',
	'luridu',
	'descent', # descend
	'pawne', # pawned
	'haulte', # halted
	'spe', # spent
	'travese', # traverse
	'thenproceede', # then proceeded
	'drow', # draw
	'starr', # star
	'asume', # assume
	'ar', # are
	'incloud', # include
	'resode', # reside
	'conductd', # conducted
	'showcast', # showcase
	'world', # worked
}

SALTS_WORDS: Set[str] = {
	'processing',
	'versions',
	'gaming',
	'breeding',
	'layer',
	'spec',
	'methyl',
	'section',
	'haven',
	'communications',
	'research',
	'wing',
	'percent',
	'sports',
	'tier',
	'regulation',
	'relations',
	'gram',
	'cent',
	'puff',
	'bytes',
	'commerce',
	'scan',
	'series',
	'health',
	'pause',
	'tech',
	'chrome',
	'phase',
	'projects',
	'liter',
	'nutrition',
	'sector',
	'byte',
	'podcast',
	'java',
	'noon',
	'science',
	'boarding',
	'levels',
	'biology',
	'beta',
	'miss',
	'styles',
	'pixel',
	'rave',
	'context',
	'security',
	'prints',
	'version',
	'flash',
	'rule',
	'jobs',
	'campus',
	'nature',
	'products',
	'nexus',
	'paragraph',
	'politics',
	'node',
	'lies',
	'bits',
	'justice',
	'ling',
	'harm',
	'terrorism',
	'lime',
	'class',
	'lore',
	'tick',
	'lace',
	'storage',
	'register',
	'spawn',
	'command',
	'circle',
	'counter',
	'sect',
	'life',
	'chief',
	'stairs',
	'site',
	'buff',
	'bench',
	'limits',
	'park',
	'moon',
	'stories',
	'lust',
	'compliance',
	'detail',
	'combat',
	'behavior',
	'mount',
	'sale',
	'blocks',
	'self',
	'generation',
	'chapter',
	'lane',
	'ridge',
	'properties',
	'performance',
	'display',
	'carbon',
	'mode',
	'control',
	'caliber',
	'micro',
	'development',
	'notes',
	'stress',
	'corn',
	'treatment',
	'trace',
	'production',
	'clips',
	'tones',
	'cases',
	'million',
	'shirts',
	'dollar',
	'paste',
	'rows',
	'fest',
	'ward',
	'blood',
	'pine',
	'venture',
	'foot',
	'header',
	'division',
	'member',
	'vent',
	'review',
	'thanks',
	'relative',
	'custom',
	'shift',
	'sections',
	'contact',
	'missions',
	'lambda',
	'poly',
	'girlfriend',
	'post',
	'mint',
	'base',
	'ping',
	'template',
	'source',
	'gall',
	'sync',
	'definition',
	'center',
	'punk',
	'radio',
	'camera',
	'writ',
	'ventures',
	'radius',
	'vantage',
	'description',
	'comments',
	'faith',
	'light',
	'dash',
	'population',
	'flame',
	'ghost',
	'fiction',
	'success',
	'monster',
	'fire',
	'mining',
	'chin',
	'slice',
	'stroke',
	'cycle',
	'rock',
	'piracy',
	'mouse',
	'brain',
	'rail',
	'flight',
	'prep',
	'board',
	'mouth',
	'cart',
}

SALTS_MISSING_WORDS: Set[str] = {
	'bits',
	'byte',
	'bytes',
	'caliber',
	'cart',
	'cent',
	'chrome',
	'fest',
	'java',
	'lambda',
	'ling',
	'liter',
	'lore',
	'lust',
	'methyl',
	'nexus',
	'noon',
	'paragraph',
	'pause',
	'ping',
	'piracy',
	'pixel',
	'poly',
	'prep',
	'puff',
	'radius',
	'rave',
	'shirts',
	'slice',
	'spawn',
	'spec',
	'sync',
	'template',
	'tick',
	'tones',
	'translation',
	'vantage',
	'vent',
}

SALTS_MISSING_MISSING_WORDS: Set[str] = {
	'chin',
	'header',
	'micro',
	'ventures',
	'writ',
}

SALTS_MISSING_MISSING_MISSING_WORDS: Set[str] = {
	'dash',
	'haven',
}

# the wikipedia dump removes measure words
# like, "The terrain occupies 464 acres adjacent to..."
# becomes "The terrain occupies adjacent to..."
# for whatever reason. spaCy parses these as weird objects
# let's exclude them
BAD_OBJECTS: Set[str] = {
	'about',
	'adjacent',
	'around',
	'the',
	'The',
	'over',
	'approximately',
	'came',
	'an',
	'to',
	'.',
	'in',
	'together',
	'between',
	'served',
	'former',
	'of',
	'detailed',
	'go',
	'additional',
	'traditional',
	'than',
	'whole', # not actually bad, but bad most of the time
	'terrible',
	'serial',
	'estimated',
	'as',
	'critical',
	'damaged',
	'diplomatic',
	'advanced',
	'famous',
	'advantageous', # advantages
	'youngman', # young man
	'wide',
	'ambitious', # ambitions
	'similar', # ungrammatical sentence
	'professional', # ungrammatical sentence
	'blackish', # ungrammatical sentence
	'numerous', # missing measure word
	'gestural', # adjective
	'been', # ungrammatical sentence
	'currently', # ungrammatical sentence
	'serial', # ungrammatical sentence
	'nearly', # measure word
}

POSTNOMINAL_ADJS: Set[str] = {
	'General', # attorney general
	'general',
	'public', # notary public
	'Public',
	'martial', # court martial
	'Martial',
	'Elect', # president elect
	'elect',
	'Major', # sergeant major
	'major',
	'total', # sum total
	'Total',
	'simple', # fee simple
	'Simple',
	'apparent', # heir apparent
	'Apparent',
	'politic', # body politic
	'Politic',
	'errant', # knight errant
	'Errant',
	'laureate', # poet laureate
	'Laureate',
	'Emeritus', # professor emeritus
	'emeritus',
	'Emerita', # professor emerita
	'emerita',
	'Emeriti', # professors emeriti
	'emeriti',
	'grata', # persona(e) non grata(e)
	'Grata'
	'gratae',
	'Gratae',
	'Vitae', # curriculum vitae
	'vitae',
	'noir', # film noir
	'Noir',
	'Royal', # battle royal(e)
	'royal',
	'Royale',
	'royale',
}

MAX_TRIES_TO_FIND_SUBJECT: int = 10

def en_string_conditions(s: str) -> Union[bool,str]:
	'''Conditions that strings of English must meet.'''
	if not string_conditions(s):
		return False
	
	# these characters lead to weird behavior
	# by spaCy
	if any(c in s for c in EN_STOP_STRINGS):
		return False
	
	# no period in the middle of a sentence.
	# this will remove sentences with abbreviations in the
	# middle, but it will make sure we don't get junk like
	# multiple sentences too
	if re.search(r'\.', s[:-1]):
		return False
	
	# must be ascii when punctuation is removed
	if not s.translate(s.maketrans('', '', string.punctuation)).isascii():
		return False
	
	# English-specific filters
	# if s[-1] in VALID_SENTENCE_ENDING_CHARS:
	# must not end with a punct preceded by a capital letter (happens when splitting on middle names)
	# we check that the sentence ends with '.', '!', or '?' already in the string conditions function above
	if s[-2].isupper():
		return False
	
	if any(s.endswith(f' {abb}') for abb in EN_ABBREVIATIONS):
		return False
	
	if any(re.search(regex, s) for regex in EN_EXCLUDE_REGEXES):
		return False
	
	return s

def basic_conditions(s: str, conjoined: bool = True) -> Union[bool,EDoc]:
	'''
	Basic conditions to clean up noisy data.
	The main idea is to make sure we are reasonably
	certain of getting a complete sentence that is 
	correctly parsed. It's not foolproof, but it works
	most of the time, and catches a lot of junk.
	'''
	s = en_string_conditions(s)
	
	if not s:
		return False
	
	# now we have to parse
	try:
		s = nlp(s)
		
		# bad deps contains generic dependencies
		# spaCy assigns to things when it doesn't know
		# what's going on. we want to exclude any sentence
		# with these, because it often means the sentence
		# is ungrammatical
		if any(t.dep_ in BAD_DEPS for t in s):
			return False
		
		# if the root is not a verb, we don't want it
		if not s.root_is_verb:
			return False
		
		# no unidentified words or foreign words
		if any(t.pos_ == 'X' or t.tag_ == 'FW' for t in s):
			return False
		
		# ungrammatical sentences using a gerund or infinitive as the main verb
		if not s.main_verb.can_be_inflected or s.main_verb.get_morph('VerbForm') == 'Inf':
			return False
		
		vs = s.main_clause_verbs
		# ungrammatical sentences without main verbs
		# or sentence fragments
		if not vs:
			return False
			
		# disallow conjoined verbs if option set
		if len(s.main_clause_verbs) > 1 and not conjoined:
			return False
		
		# main verb cannot start with a capital letter
		# no imperatives or polar questions
		if any(v.text[0].isupper() for v in vs):
			return False
		
		# disallow verbs with common typos
		if any(v.text in COMMON_VERB_TYPOS for v in vs):
			return False
		
		# spaCy has some trouble parsing certain rare verbs
		# 'Trumpeter swans winter along the upper Stuart.' parsed
		# 'swans' as the verb instead of winter
		if any(v.text in MISPARSED_AS_VERBS for v in vs):
			return False
		
		if any(v.lemma_ in BAD_VERB_LEMMAS for v in vs):
			return False
		
		# if there is no main subject, we don't want it
		if not s.has_main_subject:
			return False
		
		# if isinstance(s.main_subject,list):
		# 	if not any(t.pos_ in NOUN_POS_TAGS for t in s.main_subject):
		# 		return False
		# elif not s.main_subject.pos_ in NOUN_POS_TAGS:
		# 	return False
		
		# if isinstance(s.main_subject,list):
		# 	if any(t.tag_ in SUBJ_EXCL_TAGS for t in s.main_subject):
		# 		return False
		# elif s.main_subject.tag_ in SUBJ_EXCL_TAGS:
		# 	return False
		
		# subjects and objects must be nouns, if they exist
		su = flatten([v.subject for v in vs if v.subject is not None])
		o  = flatten([v.object for v in vs if v.object is not None])
		
		for subj in su[:]:
			if subj.text in ALL_PARTITIVES:
				su.append(s._get_partitive_head_noun(subj))
		
		su = flatten(su)
		su = [t for i, t in enumerate(su) if not t.i in [t2.i for t2 in su[:i]]]
		
		for obj in o[:]:
			if obj.text in ALL_PARTITIVES:
				o.append(s._get_partitive_head_noun(obj))
		
		o  = flatten(o)
		o  = [t for i, t in enumerate(o) if not t.i in [t2.i for t2 in o[:i]]]
		
		if any(t.pos_ not in NOUN_POS_TAGS for t in su + o):
			return False
		
		if any(t.tag_ in SUBJ_EXCL_TAGS for t in su):
			return False
		
		if any(t.text.lower() == 'the' for t in su + o):
			return False
		
		for t in su + o:
			try:
				float(t.text.replace(',', ''))
				return False
			except ValueError:
				pass
		
		# filter out stuff like "attorney(s) general", which parse "general" as the subject
		# even when the preceding noun is plural. this also catches some other stuff,
		# like "Major General", where general actually is the head, but that's fine
		if any(
			t.i != 0 and 
			t.text in POSTNOMINAL_ADJS and 
			s[t.i-1].pos_ in NOUN_POS_TAGS and 
			not s[t.i-1].text in POSTNOMINAL_ADJS for t in su
		):
			return False
		
		# if the main subject
		# can be converted to a floating
		# point number, exclude it
		# this leads to all kinds of weird behavior
		# try:
		# 	if isinstance(s.main_subject,list):
		# 		float(s.main_subject[0].text.replace(',', ''))
		# 	else:
		# 		float(s.main_subject.text.replace(',', ''))
			
		# 	return False
		# except ValueError:
		# 	pass
		
		# surprisingly frequent typo of 'they' -> 'the'
		# and missing subjects after 'the'
		# if isinstance(s.main_subject,list):
		# 	if s.main_subject[0].text.lower() == 'the':
		# 		return False
		# elif s.main_subject.text.lower() == 'the':
		# 		return False
		
		# if any of the main verbs cannot be inflected, we don't want it
		if any(not v.can_be_inflected for v in vs):
			return False
		
		# if the main verb is used to, it can be inflected (for questions)
		# but we don't want it because it can't be made present tense
		if any(
			(
				not v.is_aux and 
				v.text in ['use', 'used'] and
				any(t.dep_ == 'xcomp' for t in v.children)
			) or (
				v.is_aux and 
				v.head.text in ['use', 'used'] and 
				any(t.dep_ == 'xcomp' for t in v.head.children)
			)
			for v in vs
		):
			return False
		
		# a lot of these weird "The district covered about of Cambridge..."
		# show up. it's bizarre and consistently odd. I guess the measure
		# terms were removed from the dataset?
		if any(t for t in s if t.dep_ in OBJ_DEPS and t.text in BAD_OBJECTS):
			return False
		
		return s
	except KeyboardInterrupt:
		sys.exit(f'User terminated program on example "{s}".')	
	except Exception as e:
		log.warning(f'\n\nExample "{s}" ran into an error!:\n\n')
		log.warning(traceback.format_exc())
		log.warning('\n\n')
		return False

def has_interveners_and_number_agreement_conditions(s: str) -> Union[bool,EDoc]:
	'''Returns sentences with number agreement and interveners.'''
	log.info(f'\n\n{s}\n\n')
	s = basic_conditions(s)
	if s:
		try:
			v = s.main_verb
			# was and were show agreement in the past tense,
			# but otherwise no English verbs do
			if v.get_morph('Tense') == 'Past' and not v.lemma_ == 'be':
				return False
			
			# we want interveners that are associated with structures
			# we are not ignoring
			if not s.has_main_subject_verb_interveners:
				return False
			
			if not s.main_subject_verb_intervener_structures:
				return False
				
			if len(s.main_subject_verb_interveners) != len(s.main_subject_verb_intervener_structures):
				return False
			
			return s
		except KeyboardInterrupt:
			sys.exit(f'User terminated program on example "{s}".')
		except Exception as e:
			log.warning(f'\n\nExample "{s}" ran into an error!:\n\n')
			log.warning(traceback.format_exc())
			log.warning('\n\n')
			return False
	else:
		return False	

def no_dist_conditions(s: str, conjoined: bool = True) -> Union[bool,EDoc]:
	'''
	If the sentence satisfies basic conditions and
	has no distractor nouns, return the sentence.
	Else, return False.
	'''
	s = basic_conditions(s, conjoined)
	
	if not s:
		return False
		
	try:
		# if there are distractors, we don't want it for training
		if s.has_main_subject_verb_distractors:
			return False
		
		# check to make sure the sentences have the correct agreement
		for v in s.main_clause_verbs:
			# main clause verbs cannot be infinitives or gerunds
			if v.get_morph('VerbForm') == 'Inf' or v.tag_ == 'VBG':
				return False
			
			# step up through the tree to find the subject
			# that should agree with this verb
			subj = [t for t in v.children if t.dep_ in SUBJ_DEPS]
			if all(t.dep_ == 'attr' for t in subj):
				subj = []
			
			if len(subj) == 1:
				subj = subj[0]
			
			if not subj:
				next_v = v
				tries = 0
				while not next_v.subject:
					next_v = next_v.head
					tries += 1
					# usually this means the sentence
					# doesn't have a subject (because 
					# it's ungrammatical, a fragment, etc.)
					if tries > MAX_TRIES_TO_FIND_SUBJECT:
						return False
				
				subj = next_v.subject
			
			if not isinstance(subj,list):
				subj = [subj] if subj is not None else []
			
			for t in subj[:]:
				if t.text in ALL_PARTITIVES:
					p_head = s._get_partitive_head_noun(t)
					if isinstance(p_head, list):
						subj.extend(p_head)
					else:
						subj.append(p_head)
				
			# remove any duplicates
			deduped_subjs = [subj[0]]
			for t in subj:
				if not any(t.i == t2.i for t2 in deduped_subjs):
					deduped_subjs.append(t)
			
			subj = deduped_subjs
			
			if len(subj) > 1:
				s_n = s._get_list_noun_number(subj)
			else:
				s_n = subj[0].get_morph('Number')
			
			v_n = v.get_morph('Number')
			
			# ungrammatical sentence
			if s_n is not None and v_n is not None and s_n != v_n:
				return False
		
		return s
	except KeyboardInterrupt:
		sys.exit(f'User terminated program on example "{s}".')
	except Exception:
		log.warning(f'\n\nExample "{s}" ran into an error!:\n\n')
		log.warning(traceback.format_exc())
		log.warning('\n\n')
		return False

def question_conditions(s: str, conjoined: bool = True) -> Union[bool,EDoc]:
	'''
	No distractors, plus no presubject modifiers.
	Also main verbs must not be an aux. (We want do-support.)
	'''
	s = no_dist_conditions(s, conjoined)
	if not s:
		return False
	
	if not s.can_form_polar_question:
		return False
	
	vs = s.main_clause_verbs
	
	# we want do-support
	if any(v.is_aux for v in vs):
		return False
		
	# no negative sentences
	# we have to do weird things
	# with n't vs. not vs. cannot
	# that we'd rather just avoid
	if any(v.is_negative for v in vs):
		return False
	
	# we don't want agreement in the baseline sentence
	if any(v.lemma_ == 'be' for v in vs):
		return False
	
	# we want the main subject to be the first 
	# dependent of the verb in the sentence
	subject = s.main_subject
	if isinstance(subject,list):
		subject_position = min([t.i for t in subject])
	else:
		subject_position = subject.i
	
	if any(t.i < subject_position for t in s.main_verb.children):
		return False
	else:
		return s

def salts_conditions(s: str, words: Set[str] = SALTS_WORDS) -> Union[bool,str]:
	'''
	Sentences for the salts must have one
	of a number of predefined words to be
	useful. They must also meet the EN
	string conditions.
	'''
	if (
		words in [
			'SALTS_WORDS', 
			'SALTS_MISSING_WORDS', 
			'SALTS_MISSING_MISSING_WORDS',
			'SALTS_MISSING_MISSING_MISSING_WORDS',
		]
	):
		words = eval(words)
	
	s = en_string_conditions(s)
	if not s:
		return False
	
	# the salts words have to be after the first word
	# because they need to have a space before them in
	# RoBERTa
	split_s = set(s.translate(s.maketrans('', '', string.punctuation)).split()[1:])
	
	if not any(word in split_s for word in words):
		return False
	
	return s

def simple(s: str) -> Dict[str,EDoc]:
	'''Puts a sentence into a dict.'''
	return {'src': s}

def pres_or_past(s: EDoc, pres_p: float = 0.5) -> Dict:
	'''Generate a present tense or past tense pair, with p(past-to-pres) = pres_p.'''
	return present_pair(s) if random.random() < pres_p else past_pair(s)

def ques_or_past(s: EDoc, ques_p: float = 0.5) -> Dict:
	'''Generate a present tense or past tense pair, with p(past-to-pres) = pres_p.'''
	return question_pair(s) if random.random() < ques_p else past_pair(s)

def present_pair(s: EDoc) -> Dict:
	'''
	Get a pair of sentenecs where the source is 
	past tense and the target is present tense.
	''' 
	return {
		'src': s.make_main_verb_past_tense(),
		'prefix': 'pres',
		'tgt': s.make_main_verb_present_tense()	
	}

def question_pair(s: EDoc) -> Dict:
	'''
	Get a pair of sentenecs where the source is 
	past tense and the target is present tense.
	''' 
	return {
		'src': s.make_main_verb_past_tense(),
		'prefix': 'ques_pres',
		'tgt': s.make_main_verb_present_tense().make_sentence_polar_question()
	}

def past_pair(s: EDoc) -> Dict:
	'''
	Get a pair of sentences where the 
	source and target are in past tense.
	'''
	s = s.make_main_verb_past_tense()
	
	return {
		'src': s,
		'prefix': 'past',
		'tgt': s
	}

def pres_or_past_no_pres_dist(s: EDoc, pres_p: float = 0.5) -> Dict:
	'''
	Get a pair of sentences where the
	source is in past tense, the target
	may be in present (p=pres_p) tense
	or past tense. If the target is
	in present tense, all will be renumbered
	so that they are no longer distractors.
	
	However, you should _probably_ not being using
	this, since it will not necessarily renumber
	all distractors correctly (i.e., proper nouns).
	Instead, filter out sentences with distractors
	to begin with, which will ensure accuracy.
	'''
	d = pres_or_past(s=s, pres_p=pres_p)
	
	if d['prefix'] == 'pres':
		d['tgt'] = d['tgt'].auto_renumber_main_subject_verb_distractors()
	
	return d
