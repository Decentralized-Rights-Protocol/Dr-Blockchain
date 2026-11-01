from src.core.protocol.consensus.bls_threshold import BLSConsensus


def test_quorum_requires_unique_valid_positive_votes():
    consensus = BLSConsensus(total_elders=4, threshold=3)
    proposal = consensus.propose_block("elder_0", {"height": 1, "txs": ["a"]})
    assert proposal is not None

    # Negative votes are authenticated, but cannot contribute to a commit quorum.
    assert consensus.vote_on_proposal("elder_0", proposal.block_hash, False) is not None
    assert consensus.vote_on_proposal("elder_1", proposal.block_hash, True) is not None
    assert consensus.vote_on_proposal("elder_2", proposal.block_hash, True) is not None
    assert consensus.collect_threshold_signature(proposal.block_hash) is None

    assert consensus.vote_on_proposal("elder_3", proposal.block_hash, True) is not None
    certificate = consensus.collect_threshold_signature(proposal.block_hash)
    assert certificate is not None
    assert certificate.threshold_met is True
    assert certificate.participants == ["elder_1", "elder_2", "elder_3"]
    assert consensus.verify_threshold_signature(proposal.block_hash, certificate)
    assert consensus.get_consensus_status()["bls_aggregation"] is False

    certificate.verification_proof = b"{}"
    assert not consensus.verify_threshold_signature(proposal.block_hash, certificate)


def test_duplicate_or_conflicting_round_vote_is_rejected():
    consensus = BLSConsensus(total_elders=2, threshold=2)
    proposal = consensus.propose_block("elder_0", {"height": 1})
    assert proposal is not None
    assert consensus.vote_on_proposal("elder_1", proposal.block_hash, True) is not None
    assert consensus.vote_on_proposal("elder_1", proposal.block_hash, True) is None
    assert consensus.vote_on_proposal("elder_1", proposal.block_hash, False) is None


def test_tampered_signature_does_not_count():
    consensus = BLSConsensus(total_elders=2, threshold=2)
    proposal = consensus.propose_block("elder_0", {"height": 1})
    assert proposal is not None
    vote = consensus.vote_on_proposal("elder_1", proposal.block_hash, True)
    assert vote is not None
    vote.signature = b"invalid"
    assert consensus.collect_threshold_signature(proposal.block_hash) is None


def test_unknown_proposal_and_invalid_threshold_are_rejected():
    consensus = BLSConsensus(total_elders=2, threshold=2)
    assert consensus.collect_threshold_signature("unknown") is None
    for invalid_threshold in (0, 1, 3):
        try:
            BLSConsensus(total_elders=2, threshold=invalid_threshold)
        except ValueError:
            pass
        else:
            raise AssertionError("non-supermajority or oversized threshold must fail")
