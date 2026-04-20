// Package types — PoAT message types.
// These are scaffold structs. Protobuf types will replace them once
// proto/tx.proto files are generated.
package types

import (
	"fmt"

	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
)

const (
	TypeMsgSubmitActivityProof = "submit_activity_proof"
	TypeMsgRevokeActivityProof = "revoke_activity_proof"
)

var _ sdk.Msg = &MsgSubmitActivityProof{}
var _ sdk.Msg = &MsgRevokeActivityProof{}

// MsgSubmitActivityProof anchors an activity proof commitment on-chain.
// No raw activity data is included — only the IPFS CID and a metadata hash.
type MsgSubmitActivityProof struct {
	Submitter     string `json:"submitter"`
	CommitmentCID string `json:"commitment_cid"`
	ProofType     string `json:"proof_type"`
	MetadataHash  string `json:"metadata_hash"`
}

// Proto interface stubs (will be replaced by proto-generated code).
func (*MsgSubmitActivityProof) ProtoMessage()  {}
func (m *MsgSubmitActivityProof) Reset()       { *m = MsgSubmitActivityProof{} }
func (m *MsgSubmitActivityProof) String() string { return fmt.Sprintf("%+v", *m) }

func NewMsgSubmitActivityProof(submitter, cid, proofType, metaHash string) *MsgSubmitActivityProof {
	return &MsgSubmitActivityProof{
		Submitter:     submitter,
		CommitmentCID: cid,
		ProofType:     proofType,
		MetadataHash:  metaHash,
	}
}

func (msg *MsgSubmitActivityProof) Route() string { return RouterKey }
func (msg *MsgSubmitActivityProof) Type() string  { return TypeMsgSubmitActivityProof }
func (msg *MsgSubmitActivityProof) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Submitter)
	return []sdk.AccAddress{addr}
}
func (msg *MsgSubmitActivityProof) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Submitter); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid submitter address: %s", err)
	}
	if msg.CommitmentCID == "" {
		return sdkerrors.ErrInvalidRequest.Wrap("commitment_cid must not be empty")
	}
	if msg.MetadataHash == "" {
		return sdkerrors.ErrInvalidRequest.Wrap("metadata_hash must not be empty")
	}
	return nil
}

// MsgRevokeActivityProof allows an authorised party to revoke a proof.
type MsgRevokeActivityProof struct {
	Authority string `json:"authority"`
	ProofID   string `json:"proof_id"`
	Reason    string `json:"reason"`
}

func (*MsgRevokeActivityProof) ProtoMessage()  {}
func (m *MsgRevokeActivityProof) Reset()       { *m = MsgRevokeActivityProof{} }
func (m *MsgRevokeActivityProof) String() string { return fmt.Sprintf("%+v", *m) }

func NewMsgRevokeActivityProof(authority, proofID, reason string) *MsgRevokeActivityProof {
	return &MsgRevokeActivityProof{Authority: authority, ProofID: proofID, Reason: reason}
}

func (msg *MsgRevokeActivityProof) Route() string { return RouterKey }
func (msg *MsgRevokeActivityProof) Type() string  { return TypeMsgRevokeActivityProof }
func (msg *MsgRevokeActivityProof) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Authority)
	return []sdk.AccAddress{addr}
}
func (msg *MsgRevokeActivityProof) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Authority); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid authority address: %s", err)
	}
	if msg.ProofID == "" {
		return sdkerrors.ErrInvalidRequest.Wrap("proof_id must not be empty")
	}
	return nil
}
