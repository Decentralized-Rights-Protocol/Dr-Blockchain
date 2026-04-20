package types

import "time"

// RightsCategory classifies the rights domain of a proposal.
type RightsCategory string

const (
	RightsCategoryEducation   RightsCategory = "education"
	RightsCategoryHealthcare  RightsCategory = "healthcare"
	RightsCategoryHumanitarian RightsCategory = "humanitarian"
	RightsCategoryPrivacy     RightsCategory = "privacy"
	RightsCategoryDignity     RightsCategory = "dignity"
	RightsCategoryOther       RightsCategory = "other"
)

// RightsProposalStatus mirrors the standard governance proposal lifecycle.
type RightsProposalStatus int32

const (
	RightsProposalStatusNil       RightsProposalStatus = 0
	RightsProposalStatusDeposit   RightsProposalStatus = 1
	RightsProposalStatusVoting    RightsProposalStatus = 2
	RightsProposalStatusPassed    RightsProposalStatus = 3
	RightsProposalStatusRejected  RightsProposalStatus = 4
	RightsProposalStatusFailed    RightsProposalStatus = 5
)

// RightsProposal is a DRP-specific governance proposal with rights context.
//
// It carries additional metadata that standard gov proposals lack:
//   - RightsCategory: which rights domain is affected.
//   - EvidenceCID: IPFS CID of supporting evidence (optional but encouraged).
//   - ImpactStatement: a brief human-readable impact description.
//     NOTE: This is stored on-chain. Keep it short and non-sensitive.
type RightsProposal struct {
	// ID is the unique proposal identifier (auto-incremented).
	ID uint64 `json:"id"`

	// Proposer is the bech32 address of the proposal submitter.
	Proposer string `json:"proposer"`

	// Title is a short title for the proposal (max 140 chars, no PII).
	Title string `json:"title"`

	// Description is a longer description (max 1000 chars, no PII).
	Description string `json:"description"`

	// RightsCategory is the primary rights domain of this proposal.
	RightsCategory RightsCategory `json:"rights_category"`

	// EvidenceCID optionally links to an anchored evidence commitment (x/evidence CID).
	// Empty string means no evidence anchor.
	EvidenceCID string `json:"evidence_cid,omitempty"`

	// ImpactStatement is a brief statement of how this proposal affects rights.
	ImpactStatement string `json:"impact_statement,omitempty"`

	// Status is the current proposal status.
	Status RightsProposalStatus `json:"status"`

	// SubmittedAt is the block time of proposal submission.
	SubmittedAt time.Time `json:"submitted_at"`

	// VotingEndTime is when the voting period closes.
	VotingEndTime time.Time `json:"voting_end_time"`
}
