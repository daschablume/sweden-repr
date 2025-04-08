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
    

def identify_entities(coref_clusters, cluster_spans) -> dict:
    """
    Identify named entities in coreference clusters 
    and map each cluster to its representative entity spans.

    Args:
        coref_clusters (dict): Dictionary of coreference clusters.
        cluster_spans (dict): Dictionary of span positions for each cluster.

    Returns:
        dict: Dictionary mapping cluster IDs to representative entity spans.
    """
    representative_spans = {}
    for cluster_id, mentions in coref_clusters.items():
        ent_texts = []
        for mention in mentions:
            for ent in mention.ents:
                ent_texts.append((ent.text, ent.label_))

        # Step 2: Count label frequencies
        label_counts = Counter(label for _, label in ent_texts)
        if not label_counts:
            print(f'Skipping empty cluster: {cluster_id=}, mentions={mentions}')
            continue
        most_common_label = label_counts.most_common(1)[0][0]

        # Step 3: Filter by most common label and pick the longest text
        candidates = [text for text, label in ent_texts if label == most_common_label]
        best_entity = max(candidates, key=len)

        original_spans = cluster_spans[cluster_id]
        adjusted_spans = []
        for start, end, _ in original_spans:
            adjusted_spans.append((start, end, best_entity))
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
    modifications = []
    
    for spans in entity_spans.values():
        if not spans:
            continue

        for start, end, rep_name in spans:
            is_possessive = False
            
            # NB: sometimes adds possesive to the proper noun -- but the possesive
            # belonged to the previous token in the span;
            # Example: One of Sweden’s biggest  papers, Aftonbladet => Aftonbladet's
            for i in range(start, end+1):
                if i < len(doc) and doc[i].text in ["'s", "’s"]:
                    is_possessive = True
                if is_possessive:
                    replacement = rep_name + "'s"
                    break
                else:
                    replacement = rep_name
        
            modifications.append((start, end, replacement))
    
    modifications.sort(key=lambda x: x[0], reverse=True)
    
    result_tokens = tokens.copy()
    
    for start, end, replacement in modifications:
        if start < len(result_tokens):
            result_tokens[start] = replacement
            
            for i in range(start+1, end):
                if i < len(result_tokens):
                    result_tokens[i] = ""
            
            # If this was a possessive form, remove the separate possessive marker
            if end < len(result_tokens) and result_tokens[end] in ["'s", "'", "s", "’s"]:
                if replacement.endswith("'s"):
                    result_tokens[end] = ""
    
    return [tok for tok in result_tokens if tok]


def clean_text(resolved_tokens):
    resolved_text = ""
    for i, token in enumerate(resolved_tokens):
        # Don't add space before punctuation or after opening brackets
        if (i > 0 and token in '.,!?:;)]}\'\"') or (i > 0 and resolved_tokens[i-1] in '([{\'\"'):
            resolved_text += token
        else:
            resolved_text += " " + token if i > 0 else token
    
    # Clean up any remaining multiple spaces
    cleaned = re.sub(r" {2,}", " ", resolved_text)
    # Fix spaces around hyphens, apostrophes, etc.
    cleaned = re.sub(r"\s*([''“”’-])\s*", r"\1", cleaned).strip(' \n')
    return cleaned


def resolve(text: str) -> str:
    """
    Perform coreference resolution on the provided text.
    """
    doc = NLP(text)        
    coref_clusters = get_coref_clusters(doc)
    cluster_spans = find_span_positions(coref_clusters)
    entity_spans = identify_entities(coref_clusters, cluster_spans)
    resolved_tokens = replace_all_references_with_entities(doc, entity_spans)
    resolved_text = clean_text(resolved_tokens)    
    return resolved_text


def resolve_from_doc(doc: spacy.tokens.doc.Doc) -> str:
    '''
    The same as resolve(), but takes a Doc object as input -- for testing purposes.
    '''
    coref_clusters = get_coref_clusters(doc)
    cluster_spans = find_span_positions(coref_clusters)
    entity_spans = identify_entities(coref_clusters, cluster_spans)
    resolved_tokens = replace_all_references_with_entities(doc, entity_spans)
    resolved_text = clean_text(resolved_tokens)
    return resolved_text
