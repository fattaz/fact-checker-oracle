# FactCheckerOracle: Consensus-Driven Web Fact-Checking Oracle

An Intelligent Contract built for the **GenLayer** protocol that verifies natural language claims against real-time web sources using consensus-enforced LLM execution.

## Overview

Traditional blockchain oracles are limited to deterministic, structured data feeds (like token price pairs). `FactCheckerOracle` leverages GenLayer's non-deterministic web fetching and native LLM capabilities to serve as an on-chain factual verification primitive.

When a user submits a claim along with a source URL, the contract:
1. Scrapes the web page content in plain text mode via `gl.nondet.web.render`.
2. Trims the payload to avoid context limits and passes it to an LLM evaluator (`gl.nondet.exec_prompt`).
3. Uses GenLayer's Equivalence Principle (`gl.eq_principle.strict_eq`) so all validators reach consensus on the JSON verdict before writing to storage.

## Use Cases

- **Prediction Markets:** Automatically settle scalar or outcome-based market questions based on news URLs.
- **Dispute Resolution:** Provide verifiable web evidence during protocol or DAO governance disputes.
- **Decentralized Journalism:** Timestamp and audit factual assertions against public source archives.

## Smart Contract Architecture

The contract is written in GenLayer Python (`py-genlayer`):

```python
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class FactCheckerOracle(gl.Contract):
    total_claims: u256
    claims: TreeMap[str, str]

    def __init__(self):
        self.total_claims = u256(0)

    @gl.public.write
    def verify_claim(self, claim_id: str, claim_text: str, source_url: str) -> str:
        def fetch_and_evaluate() -> str:
            page_text = gl.nondet.web.render(source_url, mode="text")
            trimmed_content = page_text[:2000]

            prompt = f"""
            Act as an impartial fact-checking auditor. 
            Determine whether the provided Web Content supports or contradicts the Target Claim.

            Target Claim: "{claim_text}"

            Web Content Snippet:
            ---
            {trimmed_content}
            ---

            Respond ONLY with a JSON object in this exact schema:
            {{"verdict": "VERIFIED_TRUE" | "VERIFIED_FALSE" | "INCONCLUSIVE", "confidence": "HIGH" | "MEDIUM" | "LOW"}}
            """

            response = gl.nondet.exec_prompt(prompt)
            return response.strip()

        consensus_verdict = gl.eq_principle.strict_eq(fetch_and_evaluate)
        self.claims[claim_id] = consensus_verdict
        self.total_claims = self.total_claims + u256(1)
        return consensus_verdict

    @gl.public.view
    def get_claim(self, claim_id: str) -> str:
        return self.claims.get(claim_id, "CLAIM_NOT_FOUND")

    @gl.public.view
    def get_total_claims(self) -> u256:
        return self.total_claims
```

## How to Test Run in GenStudio

1. Open [GenStudio](https://studio.genlayer.com/).
2. Paste the contract code into the editor and hit **Deploy**.
3. Execute `verify_claim` under **Public Write** methods:
   - `claim_id`: `"claim_001"`
   - `claim_text`: `"Python was created by Guido van Rossum."`
   - `source_url`: `"https://en.wikipedia.org/wiki/Python_(programming_language)"`
4. Query `get_claim("claim_001")` in **View Methods** to confirm the output verdict.
