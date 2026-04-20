// Package types — DRP evidence module messages.
//
// Message invariants:
//   - MsgAnchorEvidence never carries raw evidence content.
//   - All sensitive data stays in IPFS, referenced by CID.
//   - The chain only records the commitment envelope.
package types

import (
	"fmt"

	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
)

const (
	TypeMsgAnchorEvidence = "anchor_evidence"
	TypeMsgRevokeEvidence = "revoke_evidence"
)

var _ sdk.Msg = &MsgAnchorEvidence{}
var _ sdk.Msg = &MsgRevokeEvidence{}

// MsgAnchorEvidence anchors an IPFS CID commitment on-chain.
//
// The submitter must have pinned the evidence to IPFS before calling this
// message.  The chain will store only the CID and hashes — never the content.
type MsgAnchorEvidence struct {
	// Submitter is the bech32 address of the anchoring party.
	Submitter string `json:"submitter"`
	// CID is the IPFS content identifier of the evidence bundle (CIDv1).
	CID string `json:"cid"`
	// ContentHash is the hex-encoded SHA-256 of the raw evidence bytes.
	ContentHash string `json:"content_hash"`
	// MetadataHash is the hex-encoded SHA-256 of the metadata JSON envelope.
	MetadataHash string `json:"metadata_hash"`
	// EvidenceType categorises this evidence for routing and filtering.
	EvidenceType string `json:"evidence_type"`
}

// Proto interface stubs (will be replaced by proto-generated code).
func (*MsgAnchorEvidence) ProtoMessage()             {}
func (m *MsgAnchorEvidence) Reset()                  { *m = MsgAnchorEvidence{} }
func (m *MsgAnchorEvidence) String() string          { return fmt.Sprintf("%+v", *m) }

func NewMsgAnchorEvidence(submitter, cid, contentHash, metaHash, evidenceType string) *MsgAnchorEvidence {
	return &MsgAnchorEvidence{
		Submitter:    submitter,
		CID:          cid,
		ContentHash:  contentHash,
		MetadataHash: metaHash,
		EvidenceType: evidenceType,
	}
}

func (msg *MsgAnchorEvidence) Route() string { return RouterKey }
func (msg *MsgAnchorEvidence) Type() string  { return TypeMsgAnchorEvidence }
func (msg *MsgAnchorEvidence) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Submitter)
	return []sdk.AccAddress{addr}
}
func (msg *MsgAnchorEvidence) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgAnchorEvidence) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Submitter); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid submitter: %s", err)
	}
	if msg.CID == "" {
		return ErrInvalidCID
	}
	if msg.ContentHash == "" {
		return ErrEmptyContentHash
	}
	if msg.MetadataHash == "" {
		return ErrEmptyMetadataHash
	}
	return nil
}

// MsgRevokeEvidence revokes an anchored evidence commitment.
// Only the original submitter or a governance-authorised address may revoke.
type MsgRevokeEvidence struct {
	Authority    string `json:"authority"`
	CommitmentID string `json:"commitment_id"`
	Reason       string `json:"reason"`
}

// Proto interface stubs (will be replaced by proto-generated code).
func (*MsgRevokeEvidence) ProtoMessage()             {}
func (m *MsgRevokeEvidence) Reset()                  { *m = MsgRevokeEvidence{} }
func (m *MsgRevokeEvidence) String() string          { return fmt.Sprintf("%+v", *m) }

func (msg *MsgRevokeEvidence) Route() string { return RouterKey }
func (msg *MsgRevokeEvidence) Type() string  { return TypeMsgRevokeEvidence }
func (msg *MsgRevokeEvidence) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Authority)
	return []sdk.AccAddress{addr}
}
func (msg *MsgRevokeEvidence) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgRevokeEvidence) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Authority); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid authority: %s", err)
	}
	if msg.CommitmentID == "" {
		return sdkerrors.ErrInvalidRequest.Wrap("commitment_id must not be empty")
	}
	return nil
}
