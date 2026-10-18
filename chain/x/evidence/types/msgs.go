// Package types — DRP evidence module messages.
//
// Message invariants:
//   - MsgAnchorEvidence never carries raw evidence content.
//   - All sensitive data stays in IPFS, referenced by CID.
//   - The chain only records the commitment envelope.
package types

import (
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
