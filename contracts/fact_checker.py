# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class FactCheckerOracle(gl.Contract):
    """
    Decentralized Multi-Source AI Fact-Checking Oracle.
    Evaluates assertions across multiple web sources with contract-side invariant 
    validation, claim-ID reuse protection, and structured consensus state management.
    """
    total_claims: u256
    claims_text: TreeMap[str, str]
    claims_verdict: TreeMap[str, str]
    claims_status: TreeMap[str, str]
    claims_sources_count: TreeMap[str, u256]

    def __init__(self):
        self.total_claims = u256(0)

    @gl.public.write
    def verify_claim(self, claim_id: str, claim_text: str, source_urls: list[str]) -> str:
        """
        Fetches evidence across multiple independent web sources, enforces strict consensus
        validation, and stores structured verification state under validator agreement.
        """
        # Protect stored attestations from claim-ID reuse
        if self.claims_status.get(claim_id, "") != "":
            raise Exception(f"Claim ID '{claim_id}' already exists. Overwriting stored attestations is forbidden.")

        # Contract-side input validation
        if len(source_urls) < 1 or len(source_urls) > 3:
            raise Exception("Must supply between 1 and 3 source URLs for cross-referencing")

        if len(claim_text.strip()) < 10:
            raise Exception("Claim text is too short to evaluate")

        def multi_source_evaluation() -> str:
            evidence_blocks = []

            # Fetch and sanitize web pages across all sources
            for idx, url in enumerate(source_urls):
                # Clean stray brackets or quotes from input URL
                clean_url = str(url).strip().strip("[]\"'")
                
                raw_text = gl.nondet.web.render(clean_url)
                snippet = raw_text[:1500].strip()
                evidence_blocks.append(f"[Source {idx + 1}: {clean_url}]\n{snippet}")

            combined_evidence = "\n\n".join(evidence_blocks)

            prompt = f"""
            You are a strict, impartial fact-checking oracle engine.
            Compare the Target Claim against the provided Web Evidence from multiple sources.

            Target Claim: "{claim_text}"

            Web Evidence:
            {combined_evidence}

            Respond ONLY with one of the following exact strings:
            VERIFIED_TRUE
            VERIFIED_FALSE
            INCONCLUSIVE
            """

            response = gl.nondet.exec_prompt(prompt).strip().upper()

            # Ensure response matches standard consensus enums
            if "VERIFIED_TRUE" in response:
                return "VERIFIED_TRUE"
            elif "VERIFIED_FALSE" in response:
                return "VERIFIED_FALSE"
            elif "INCONCLUSIVE" in response:
                return "INCONCLUSIVE"
            else:
                raise ValueError("LLM response did not contain a valid verdict enum")

        # Reach consensus across network validators using strict equivalence
        consensus_verdict = gl.eq_principle.strict_eq(multi_source_evaluation)

        # Record structured contract state
        self.claims_text[claim_id] = claim_text
        self.claims_verdict[claim_id] = consensus_verdict
        self.claims_status[claim_id] = "RESOLVED"
        self.claims_sources_count[claim_id] = u256(len(source_urls))
        self.total_claims = self.total_claims + u256(1)

        return consensus_verdict

    @gl.public.view
    def get_claim_verdict(self, claim_id: str) -> str:
        """Retrieves the verdict of a processed claim."""
        return self.claims_verdict.get(claim_id, "CLAIM_NOT_FOUND")

    @gl.public.view
    def get_claim_status(self, claim_id: str) -> str:
        """Retrieves the lifecycle status of a claim."""
        return self.claims_status.get(claim_id, "UNRESOLVED")

    @gl.public.view
    def get_total_claims(self) -> u256:
        """Returns total claims registered on-chain."""
        return self.total_claims
