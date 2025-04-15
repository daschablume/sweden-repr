from collections import Counter
import re

import spacy


def load_models():
    try:
        nlp = spacy.load("en_core_web_trf")
        nlp_coref = spacy.load("en_coreference_web_trf")
        
        nlp_coref.replace_listeners("transformer", "coref", ["model.tok2vec"])
        nlp_coref.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])
        
        # add coreference components to the pipeline
        nlp.add_pipe("coref", source=nlp_coref)
        nlp.add_pipe("span_resolver", source=nlp_coref)
    except Exception as e:
        raise RuntimeError(f"Failed to load NLP models: {e}")
    
    return nlp, nlp_coref


NLP, NLP_COREF = load_models()


def get_coref_clusters(doc: spacy.tokens.doc.Doc) -> dict:
    return {
        key: val for key, val in doc.spans.items() 
        if re.match(r"coref_clusters_*", key)
    }


def find_span_positions(coref_clusters) -> dict:
    return {
        cluster: [(span.start, span.end, span.text) for span in spans]
        for cluster, spans in coref_clusters.items()
    }
    

def _get_head_noun(mention):
    doc = mention.doc[mention.start:mention.end]
    for token in list(doc)[::-1]:  # Search from end (head often last)
        if token.pos_ in {"NOUN", "PROPN"} and not token.text.lower() in {"we", "they", "it", "them"}:
            return token.lemma_.lower()
    return None


def _is_named_entity(mention):
    return any(ent.label_ in {"PERSON", "ORG", "NORP", "GPE", "DATE"} for ent in mention.ents)


def identify_entities(coref_clusters, cluster_spans) -> dict:
    representative_spans = {}

    for cluster_id, mentions in coref_clusters.items():
        span_texts = [(mention.text, mention.start, mention.end, _is_named_entity(mention), _get_head_noun(mention)) for mention in mentions]

        # Count full span and head noun frequencies
        span_counter = Counter(text for text, *_ in span_texts)
        head_counter = Counter(h for *_, h in span_texts if h)

        # Prefer named entities if unique and representative
        named_entities = [(text, start, end) for text, start, end, is_ne, _ in span_texts if is_ne]
        if named_entities:
            # Prefer shortest proper noun mention (e.g., "Aftonbladet")
            best_entity = min(named_entities, key=lambda x: len(x[0]))[0]
        else:
            # Fallback: most frequent head noun span (e.g., "camp site")
            best_span = max(span_texts, key=lambda x: (head_counter[x[4]] if x[4] else 0, -len(x[0])))
            best_entity = best_span[0]

        # Apply replacement
        original_spans = cluster_spans[cluster_id]
        adjusted_spans = [(start, end, best_entity) for start, end, _ in original_spans]
        representative_spans[cluster_id] = adjusted_spans

    return representative_spans
    

def replace_all_references_with_entities(doc, entity_spans):
    """
    Replace all references with their representative entities, preserving possessive forms.
    
    Args:
        doc (spacy.Doc): The spaCy document.
        entity_spans (dict): Dictionary mapping cluster IDs to lists of (start, end, entity) tuples.
        
    Returns:
        list: Tokens with references replaced by their representative entities.
    """
    tokens = [token.text for token in doc]        
    modifications = [(start, end, rep_name) for spans in entity_spans.values() for start, end, rep_name in spans if spans]       
    modifications.sort(key=lambda x: x[0], reverse=True)
    
    result_tokens = tokens.copy()
    
    for start, end, replacement in modifications:
        if start < len(result_tokens):
            result_tokens[start] = replacement
            
            for i in range(start+1, end):
                if i < len(result_tokens):
                    result_tokens[i] = ""
    
    return [tok for tok in result_tokens if tok.strip()]


def detokenize(tokens):
    out = ''
    i = 0
    no_space_before = {'.', ',', ':', ';', '?', '!', ')', ']', '’', "'s", "'re", "'ve", "'m", "'ll", "'d", "'t", '”', '”', '’', '’', "'", '‘'}
    no_space_after = {'(', '[', '“', '“', '"', "'", '‘'}
        
    while i < len(tokens):
        # merging of $ 
        if i + 1 < len(tokens) and tokens[i] == '$' and re.match(r'^\d{1,3}(,\d{3})*(\.\d+)?$', tokens[i+1]):
            merged = f"${tokens[i+1]}"
            if out and out[-1] not in no_space_after:
                out += ' '
            out += merged
            i += 2
            continue
        # Merge number + known unit (e.g., "3 G" -> "3G")
        known_units = {'G', 'GB', 'MB', 'MHz', 'GHz'}
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


def resolve(text: str) -> str:
    """
    Perform coreference resolution on the provided text.
    """
    doc = NLP(text)        
    coref_clusters = get_coref_clusters(doc)
    cluster_spans = find_span_positions(coref_clusters)
    entity_spans = identify_entities(coref_clusters, cluster_spans)
    resolved_tokens = replace_all_references_with_entities(doc, entity_spans)
    resolved_text = ' '.join(resolved_tokens)
    resolved_text = detokenize(resolved_tokens)    
    return resolved_text


def resolve_from_doc(doc: spacy.tokens.doc.Doc) -> str:
    '''
    The same as resolve(), but takes a Doc object as input -- for testing purposes.
    '''
    coref_clusters = get_coref_clusters(doc)
    cluster_spans = find_span_positions(coref_clusters)
    entity_spans = identify_entities(coref_clusters, cluster_spans)
    resolved_tokens = replace_all_references_with_entities(doc, entity_spans)
    resolved_text = detokenize(resolved_tokens)  
    return resolved_text
