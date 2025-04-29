from maverick_resolve import get_canonical_mention, find_nonoverlapping_spans

assert get_canonical_mention(
    ['Ukraine ’s hetman', 'Ukraine ’s hetman Ivan Mazepa', 'Ivan Mazepa']
) == 'Ivan Mazepa'

assert get_canonical_mention([
    'Ukraine',
    'Ukraine ’s',
    'its',
    'the nation ’s',
    'the nation',
    'Ukraine'
]) == "Ukraine"

assert get_canonical_mention(
    ['The 150 or so Swedes who live in Ukraine', 'They']
) == 'The 150 or so Swedes who live in Ukraine'

assert get_canonical_mention([
    'Chumak',
    'Chumak , a food processing business started by two Swedes , two Swedish banks and the Tetra Pak packaging giant',
    'a food processing business started by two Swedes , two Swedish banks and the Tetra Pak packaging giant',
    'Chumak']
) == "Chumak"

assert get_canonical_mention(
    ['Olle Tholander',
    'Olle Tholander , general director of Ericsson in Ukraine',
    'general director of Ericsson in Ukraine',
    'Olle Tholander',
    'Olle Tholander , general director of Ericsson in Ukraine , who has previously worked in Japan and England',
    'Tholander']
) == 'Olle Tholander'

assert get_canonical_mention([
    'his',
    'Tomas Transtromer',
    'Tomas Transtromer , Sweden ’s most famous poet',
    'Sweden ’s most famous poet',
    'Tomas'
]) == 'Tomas Transtromer'

assert get_canonical_mention([
    'The Nobel Prize in literature',
    'the prize',
    'prize',
    'the literature prize',
    'the prize',
    'the literature prize'
]) == 'The Nobel Prize in literature'

assert get_canonical_mention(['Internet speeds', 'they']) == 'Internet speeds'

assert get_canonical_mention([
    'Eurovision',
    'the contest',
    'The show ’s',
    'it',
    'its',
    'Eurovision ’s',
    'Eurovision , one of the world ’s longest - running television programmes',
    'one of the world ’s longest - running television programmes',
]) == 'Eurovision'


# this is based solely on the length; maybe it's better to have a longer entity if it's not a NER?
# need more data
assert get_canonical_mention(['a free trade agreement', 'The agreement']) == 'The agreement'

llist = [
    (11, 11),
    (62, 63),
    (122, 122),
    (165, 165),
    (174, 174),
    (197, 197),
    (201, 201),
    (217, 219),
    (268, 268),
    (309, 309),
    (318, 318)
]
assert find_nonoverlapping_spans(llist) == llist

assert find_nonoverlapping_spans(((62, 64), (62, 66), (65, 66))) == [(62, 66)]

