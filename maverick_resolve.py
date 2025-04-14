import re

import pandas as pd
import spacy


NLP = spacy.load("en_core_web_sm")


def get_canonical_mention(cluster: list) -> str:
    """
    Given a coreference cluster, return the best entity.
    """

    candidates = []
    for mention in cluster:
        doc = NLP(mention)

        person_entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        is_clean_person = len(person_entities) > 0 and " ".join(person_entities) == mention.strip()

        has_org = any(ent.label_ == "ORG" for ent in doc.ents)
        has_gpe = any(ent.label_ == "GPE" for ent in doc.ents)
        
        # downvote if it consists only of pronouns
        not_pronoun = True
        if len(doc) == 1 and (doc[0].tag_ == 'PRP' or doc[0].tag_ == 'PRP$'):
            not_pronoun = False

        score = (
            is_clean_person,
            has_org,
            has_gpe,
            not_pronoun,
            -len(mention.split())  # shorter mentions preferred
        )

        candidates.append((score, mention))

    # sort by score and return the best candidate
    candidates.sort(reverse=True)
    return candidates[0][1] if candidates else ""


def _is_the_same(cluster: list):
    for i in range(len(cluster)-1):
        if cluster[i] != cluster[i + 1]:
            return False
    else:
        return True


def _is_the_same_span(span1: tuple, span2: tuple) -> bool:
    start1, end1 = span1
    start2, end2 = span2

    if start1 == start2:
        return True

    if end1 == end2:
        return True

    return False


def find_nonoverlapping_spans(spans: tuple) -> list:
    '''
    Sometimes entities are clusterized into a few entities:
    Ukrainian Hetman Ivan Mazepa => 
        [Ukrainian hetman, Ukrainian hetman Ivan Mazepa, Ivan Mazepa].
    This function merges such spans into one span.
    '''
    unique_spans = []
    p1, p2 = 0, 1
    span1, span2 = spans[p1], spans[p2]
    start_, end_ = span1[0], span1[1]
    while p2 < len(spans):
        span1, span2 = spans[p1], spans[p2]
        if _is_the_same_span(span1, span2):
            end_ = span2[1]
        else:
            unique_spans.append((start_, end_))
            start_, end_ = span2
        p2 += 1
        p1 += 1
    unique_spans.append((start_, end_))
    return unique_spans


def detokenize(tokens):
    out = ''
    i = 0
    no_space_before = {
        '!', "'", "'d", "'ll", "'m", "'re", "'s", "'t", "'ve", ')',
        ',', '.', ':', ';', '?', ']', '‘', '’', '”'
    }
    no_space_after = {'"', "'", '(', '[', '‘', '“'}
        
    while i < len(tokens):
        # merging of $ 
        if i + 1 < len(tokens) and tokens[i] == '$' and re.match(
                r'^\d{1,3}(,\d{3})*(\.\d+)?$', tokens[i+1]):
            merged = f"${tokens[i+1]}"
            if out and out[-1] not in no_space_after:
                out += ' '
            out += merged
            i += 2
            continue
        # Merge number + known unit (e.g., "3 G" -> "3G")
        known_units = {'G', 'MB', 'MHz', 'GHz'}
        if i + 1 < len(tokens) and re.match(r'^\d+$', tokens[i]) and tokens[i+1] in known_units:
            merged = f"{tokens[i]}{tokens[i+1]}"
            if out and out[-1] not in no_space_after:
                out += ' '
            out += merged
            i += 2
            continue

        # Merge contractions like "are n't" -> "aren't"
        contraction_suffixes = {"n't", "'re", "'ve", "'ll", "'d", "'m", "'s", "'t"}
        if i + 1 < len(tokens) and tokens[i+1].replace('’', "'") in contraction_suffixes:
            merged = f"{tokens[i]}{tokens[i+1]}"
            if out and out[-1] not in no_space_after:
                out += ' '
            out += merged
            i += 2
            continue

        # Merge hyphenated words
        if i + 2 < len(tokens) and tokens[i+1] == '-' and tokens[i].isalpha() and tokens[i+2].isalpha():
            merged = f"{tokens[i]}-{tokens[i+2]}"
            if out and out[-1] not in no_space_after:
                out += ' '
            out += merged
            i += 3
            continue

        token = tokens[i]
        if i > 0:
            if token not in no_space_before and tokens[i-1] not in no_space_after:
                out += ' '
        out += token
        i += 1

    out = out.replace(r'&amp;', '&').replace('& amp;', '&')
    return out


def resolve(output: dict) -> str:
    '''
    Takes in a dictionary from maverick's predict() method which constists of 
    a list of tokens, a list of clusters of token text, and a list of clusters of
    corresponding spans. Picks the best entity in the cluster and replaces all the 
    other entities with that entity for that particular cluster.
    '''

    token_id2replacement = {}

    tokens = output['tokens']
    clusters = output['clusters_token_text']
    spans_of_spans = output['clusters_token_offsets']
    for cluster, spans in zip(clusters, spans_of_spans):
        # don't do anything with clusters like ['trade', 'trade']
        if _is_the_same(cluster):
            continue
        best_entity = get_canonical_mention(cluster)
        unique_spans = find_nonoverlapping_spans(spans)
        for span in unique_spans:
            is_possesive = False
            start, end = span
            # if "Ivan Mazepa" (the best entity) is already in 
            # "Ukraine ’s hetman Ivan Mazepa", no need to change anything 
            if best_entity in  ' '.join(tokens[start: end + 1]):
                continue
            if tokens[end] in ["’s", "'s"]:
                is_possesive = True
            token_id2replacement[start] = best_entity
            # make a possesive form
            if start == end and (tokens[start] in [
                "its", "their", "hers", "his", "our"
            ]):
                token_id2replacement[start] = best_entity + "'s"
            start += 1
            while start <= end:
                token_id2replacement[start] = ""
                start += 1
            if is_possesive:
                token_id2replacement[end] = "'s"

    new_tokens = []
    for ind, token in enumerate(tokens):
        if ind in token_id2replacement:
            new_token = token_id2replacement[ind]
            if not new_token.strip():
                continue
            new_tokens.append(new_token)
        else:
            new_tokens.append(token)

    return detokenize(new_tokens)
