package types

import (
	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
)

const (
	TypeMsgIssueTrustStatus  = "issue_trust_status"
	TypeMsgRevokeTrustStatus = "revoke_trust_status"
)

var _ sdk.Msg = &MsgIssueTrustStatus{}

// MsgIssueTrustStatus issues a non-transferable trust status record.
type MsgIssueTrustStatus struct {
	Issuer      string      `json:"issuer"`
	Subject     string      `json:"subject"`
	StatusLevel StatusLevel `json:"status_level"`
	BasisCID    string      `json:"basis_cid"`
}

func (msg *MsgIssueTrustStatus) Route() string { return RouterKey }
func (msg *MsgIssueTrustStatus) Type() string  { return TypeMsgIssueTrustStatus }
func (msg *MsgIssueTrustStatus) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Issuer)
	return []sdk.AccAddress{addr}
}
func (msg *MsgIssueTrustStatus) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgIssueTrustStatus) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Issuer); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid issuer: %s", err)
	}
	if _, err := sdk.AccAddressFromBech32(msg.Subject); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid subject: %s", err)
	}
	return nil
}

// MsgRevokeTrustStatus revokes an existing status record.
type MsgRevokeTrustStatus struct {
	Authority string `json:"authority"`
	RecordID  string `json:"record_id"`
	Reason    string `json:"reason"`
}

var _ sdk.Msg = &MsgRevokeTrustStatus{}

func (msg *MsgRevokeTrustStatus) Route() string { return RouterKey }
func (msg *MsgRevokeTrustStatus) Type() string  { return TypeMsgRevokeTrustStatus }
func (msg *MsgRevokeTrustStatus) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Authority)
	return []sdk.AccAddress{addr}
}
func (msg *MsgRevokeTrustStatus) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgRevokeTrustStatus) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Authority); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid authority: %s", err)
	}
	if msg.RecordID == "" {
		return sdkerrors.ErrInvalidRequest.Wrap("record_id must not be empty")
	}
	return nil
}
