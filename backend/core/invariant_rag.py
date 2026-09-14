from typing import List, Dict, Any

class InvariantEngine:
    def __init__(self):
        # In-memory invariant vector store running compressed representations
        self.invariant_store: List[Dict[str, Any]] = []

    def ingest_specification(self, spec_markdown: str):
        """
        Parses structured Markdown specifications and extracts formal invariants.
        """
        for line in spec_markdown.splitlines():
            line = line.strip()
            if line.startswith("INVARIANT:"):
                raw_rule = line.replace("INVARIANT:", "").strip()
                self.invariant_store.append({
                    "raw": raw_rule,
                    "tokens": set(raw_rule.lower().split())
                })

    def query_invariants(self, context_tokens: List[str]) -> List[str]:
        """
        Returns relevant invariants based on lexical and structural overlap.
        """
        query_set = set(t.lower() for t in context_tokens)
        matched = []
        for item in self.invariant_store:
            if item["tokens"] & query_set:
                matched.append(item["raw"])
        return matched
