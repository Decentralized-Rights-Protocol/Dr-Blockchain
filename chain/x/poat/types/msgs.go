// Package types — PoAT message types.
package types

import (
	"crypto/sha256"
	"encoding/base32"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"strings"

	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
)

var base32NoPadding = base32.StdEncoding.WithPadding(base32.NoPadding)

const (
	TypeMsgSubmitActivityProof = "submit_activity_proof"
	TypeMsgRevokeActivityProof = "revoke_activity_proof"
)

var _ sdk.Msg = &MsgSubmitActivityProof{}
var _ sdk.Msg = &MsgRevokeActivityProof{}

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
	addr, err := sdk.AccAddressFromBech32(msg.Submitter)
	if err != nil {
		panic(err)
	}
	return []sdk.AccAddress{addr}
}

func (msg *MsgSubmitActivityProof) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Submitter); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid submitter address: %s", err)
	}
	if err := ValidateCID(msg.CommitmentCID); err != nil {
		return sdkerrors.ErrInvalidRequest.Wrapf("invalid commitment_cid: %v", err)
	}
	if err := ValidateProofType(msg.ProofType); err != nil {
		return sdkerrors.ErrInvalidRequest.Wrap(err.Error())
	}
	if err := ValidateMetadataHash(msg.MetadataHash); err != nil {
		return sdkerrors.ErrInvalidRequest.Wrap(err.Error())
	}
	return nil
}

func NewMsgRevokeActivityProof(authority, proofID, reason string) *MsgRevokeActivityProof {
	return &MsgRevokeActivityProof{
		Authority: authority,
		ProofID:   proofID,
		Reason:    reason,
	}
}

func (msg *MsgRevokeActivityProof) Route() string { return RouterKey }
func (msg *MsgRevokeActivityProof) Type() string  { return TypeMsgRevokeActivityProof }

func (msg *MsgRevokeActivityProof) GetSigners() []sdk.AccAddress {
	addr, err := sdk.AccAddressFromBech32(msg.Authority)
	if err != nil {
		panic(err)
	}
	return []sdk.AccAddress{addr}
}

func (msg *MsgRevokeActivityProof) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Authority); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid authority address: %s", err)
	}
	if len(msg.ProofID) != 64 {
		return sdkerrors.ErrInvalidRequest.Wrap("proof_id must be a 32-byte hexadecimal identifier")
	}
	if _, err := hex.DecodeString(msg.ProofID); err != nil {
		return sdkerrors.ErrInvalidRequest.Wrap("proof_id must be hexadecimal")
	}
	if len(strings.TrimSpace(msg.Reason)) == 0 || len(msg.Reason) > 256 {
		return sdkerrors.ErrInvalidRequest.Wrap("reason must contain 1 to 256 bytes")
	}
	return nil
}

// ValidateProofType restricts proof categories to a stable, bounded identifier.
func ValidateProofType(value string) error {
	if len(value) == 0 || len(value) > 64 {
		return fmt.Errorf("proof_type must contain 1 to 64 characters")
	}
	for i, r := range value {
		valid := r >= 'a' && r <= 'z' || r >= '0' && r <= '9' || r == '-' || r == '_' || r == '.'
		if !valid || (i == 0 && !(r >= 'a' && r <= 'z')) {
			return fmt.Errorf("invalid proof_type identifier")
		}
	}
	return nil
}

func ValidateMetadataHash(value string) error {
	if len(value) != 64 {
		return fmt.Errorf("metadata_hash must be a 32-byte SHA-256 hex digest")
	}
	decoded, err := hex.DecodeString(value)
	if err != nil || len(decoded) != 32 {
		return fmt.Errorf("metadata_hash must be hexadecimal")
	}
	return nil
}

// ValidateCID checks CIDv1 base32 framing only; it does not verify evidence content.
func ValidateCID(value string) error {
	if len(value) < 10 || len(value) > 256 || value[0] != 'b' {
		return fmt.Errorf("CID must be a bounded CIDv1 base32 string")
	}
	raw, err := base32NoPadding.DecodeString(strings.ToUpper(value[1:]))
	if err != nil {
		return fmt.Errorf("CID is not valid base32")
	}
	version, n := binary.Uvarint(raw)
	if n <= 0 || version != 1 {
		return fmt.Errorf("CID version must be 1")
	}
	raw = raw[n:]
	codec, n := binary.Uvarint(raw)
	if n <= 0 || codec == 0 {
		return fmt.Errorf("CID codec is invalid")
	}
	raw = raw[n:]
	hashCode, n := binary.Uvarint(raw)
	if n <= 0 || hashCode == 0 {
		return fmt.Errorf("CID multihash code is invalid")
	}
	raw = raw[n:]
	digestLen, n := binary.Uvarint(raw)
	if n <= 0 || digestLen == 0 || digestLen > 128 {
		return fmt.Errorf("CID multihash digest length is invalid")
	}
	raw = raw[n:]
	if uint64(len(raw)) != digestLen {
		return fmt.Errorf("CID multihash digest length does not match payload")
	}
	return nil
}

// BuildProofID derives a deterministic, domain-separated ID from signed submission fields.
func BuildProofID(submitter, cid, metadataHash string) string {
	sum := sha256.Sum256([]byte("drp/poat/v1\x00" + submitter + "\x00" + cid + "\x00" + metadataHash))
	return hex.EncodeToString(sum[:])
}
