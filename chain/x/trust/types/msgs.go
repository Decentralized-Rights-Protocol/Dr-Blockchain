package types

import (
	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
)

const TypeMsgUpdateTrustState = "update_trust_state"

var _ sdk.Msg = &MsgUpdateTrustState{}

// MsgUpdateTrustState allows an authorised party to update a participant's trust state.
// Initially only governance or a designated oracle can invoke this.

func (msg *MsgUpdateTrustState) Route() string { return RouterKey }
func (msg *MsgUpdateTrustState) Type() string  { return TypeMsgUpdateTrustState }
func (msg *MsgUpdateTrustState) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Authority)
	return []sdk.AccAddress{addr}
}
func (msg *MsgUpdateTrustState) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgUpdateTrustState) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Authority); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid authority: %s", err)
	}
	if _, err := sdk.AccAddressFromBech32(msg.Address); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid address: %s", err)
	}
	return nil
}
