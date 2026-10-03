# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

class FactCheckerOracle(gl.Contract):
    """
    Decentralized Multi-Source AI Fact-Checking Oracle.
    Evaluates assertions across multiple web sources with contract-side invariant 
    validation and structured consensus state management.
    """
    total_claims: u256
    claims_text: TreeMap[str, str]
    claims_verdict: TreeMap[str, str]
    claims_confidence: TreeMap[str, u256]
    claims_status: TreeMap[str, str]
    claims_sources_count: TreeMap[str, u256]

    def __init__(self):
        self.total_claims = u256(0)

    @gl.public.write
    def verify_claim(self, claim_id: str, claim_text: str, source_urls: list[str]) -> str:
        """
        Fetches evidence across multiple independent web sources, enforces strict JSON schema
        validation, and stores structured verification state under validator consensus.
        """
        # Contract-side input validation
        if len(source_urls) < 1 or len(source_urls) > 3:
            raise Exception("Must supply between 1 and 3 source URLs for cross-referencing")

        if len(claim_text.strip()) < 10:
            raise Exception("Claim text is too short to evaluate")

        def multi_source_evaluation() -> str:
            evidence_blocks = []

            # Fetch and sanitize web pages across all sources
            for idx, url in enumerate(source_urls):
                raw_text = gl.nondet.web.render(url, mode="text")
                snippet = raw_text[:1500].strip()
                evidence_blocks.append(f"[Source {idx + 1}: {url}]\n{snippet}")

            combined_evidence = "\n\n".join(evidence_blocks)

            prompt = f"""
            You are a strict, impartial fact-checking oracle engine.
            Compare the Target Claim against the provided Web Evidence from multiple sources.

            Target Claim: "{claim_text}"

            Web Evidence:
            {combined_evidence}

            Output Guidelines:
            1. Evaluate whether evidence supports or contradicts the claim.
            2. Provide a confidence rating between 0 and 100.
            3. You MUST respond with ONLY a valid JSON object using this exact structure:
            {{
                "verdict": "VERIFIED_TRUE" | "VERIFIED_FALSE" | "INCONCLUSIVE",
                "confidence": <integer from 0 to 100>,
                "summary": "<one sentence explanation>"
            }}
            """

            response = gl.nondet.exec_prompt(prompt).strip()

            # Clean potential markdown formatting from LLM response
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # Schema validation inside non-deterministic block
            try:
                parsed = json.loads(response)
            except Exception:
                raise ValueError("LLM failed to output valid JSON")

            verdict = parsed.get("verdict", "")
            if verdict not in ["VERIFIED_TRUE", "VERIFIED_FALSE", "INCONCLUSIVE"]:
                raise ValueError("Invalid verdict field in LLM response")

            confidence = int(parsed.get("confidence", -1))
            if confidence < 0 or confidence > 100:
                raise ValueError("Invalid confidence score in LLM response")

            return json.dumps({
                "verdict": verdict,
                "confidence": confidence,
                "summary": str(parsed.get("summary", ""))
            })

        # Reach consensus across network validators using strict equivalence
        consensus_json = gl.eq_principle.strict_eq(multi_source_evaluation)
        parsed_consensus = json.loads(consensus_json)

        # Record structured contract state
        self.claims_text[claim_id] = claim_text
        self.claims_verdict[claim_id] = parsed_consensus["verdict"]
        self.claims_confidence[claim_id] = u256(parsed_consensus["confidence"])
        self.claims_status[claim_id] = "RESOLVED"
        self.claims_sources_count[claim_id] = u256(len(source_urls))
        self.total_claims = self.total_claims + u256(1)

        return consensus_json

    @gl.public.view
    def get_claim_verdict(self, claim_id: str) -> str:
        """Retrieves the verdict of a processed claim."""
        return self.claims_verdict.get(claim_id, "CLAIM_NOT_FOUND")

    @gl.public.view
    def get_claim_confidence(self, claim_id: str) -> u256:
        """Retrieves the confidence score (0-100) of a processed claim."""
        return self.claims_confidence.get(claim_id, u256(0))

    @gl.public.view
    def get_claim_status(self, claim_id: str) -> str:
        """Retrieves the lifecycle status of a claim."""
        return self.claims_status.get(claim_id, "UNRESOLVED")

    @gl.public.view
    def get_total_claims(self) -> u256:
        """Returns total claims registered on-chain."""
        return self.total_claims
