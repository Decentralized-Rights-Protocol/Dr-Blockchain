package types

import (
	"fmt"

	"github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/errors"
)

type MsgMint struct {
	Recipient        string
	Amount          types.Int
	Reason          string
	ActivityID      string
	VerificationHash string
}

func NewMsgMint(recipient, reason, activityID, verificationHash string, amount types.Int) *MsgMint {
	return &MsgMint{
		Recipient:        recipient,
		Amount:          amount,
		Reason:          reason,
		ActivityID:      activityID,
		VerificationHash: verificationHash,
	}
}

func (msg *MsgMint) Route() string { return RouterKey }
func (msg *MsgMint) Type() string { return "mint_deri" }
func (msg *MsgMint) GetSigners() []types.AccAddress {
	addr, _ := types.AccAddressFromBech32(msg.Recipient)
	return []types.AccAddress{addr}
}
func (msg *MsgMint) GetSignBytes() []byte {
	return types.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgMint) ValidateBasic() error {
	if _, err := types.AccAddressFromBech32(msg.Recipient); err != nil {
		return errors.Wrapf(errors.ErrInvalidAddress, "invalid recipient: %v", err)
	}
	if !msg.Amount.IsPositive() {
		return errors.Wrap(errors.ErrInvalidRequest, "mint amount must be positive")
	}
	return nil
}

type MsgBurn struct {
	Sender  string
	Amount types.Int
	Reason string
}

func NewMsgBurn(sender, reason string, amount types.Int) *MsgBurn {
	return &MsgBurn{Sender: sender, Amount: amount, Reason: reason}
}

func (msg *MsgBurn) Route() string { return RouterKey }
func (msg *MsgBurn) Type() string { return "burn_deri" }
func (msg *MsgBurn) GetSigners() []types.AccAddress {
	addr, _ := types.AccAddressFromBech32(msg.Sender)
	return []types.AccAddress{addr}
}
func (msg *MsgBurn) GetSignBytes() []byte {
	return types.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgBurn) ValidateBasic() error {
	if _, err := types.AccAddressFromBech32(msg.Sender); err != nil {
		return errors.Wrapf(errors.ErrInvalidAddress, "invalid sender: %v", err)
	}
	if !msg.Amount.IsPositive() {
		return errors.Wrap(errors.ErrInvalidRequest, "burn amount must be positive")
	}
	return nil
}

type MsgTransfer struct {
	From   string
	To     string
	Amount types.Int
}

func NewMsgTransfer(from, to string, amount types.Int) *MsgTransfer {
	return &MsgTransfer{From: from, To: to, Amount: amount}
}

func (msg *MsgTransfer) Route() string { return RouterKey }
func (msg *MsgTransfer) Type() string { return "transfer_deri" }
func (msg *MsgTransfer) GetSigners() []types.AccAddress {
	addr, _ := types.AccAddressFromBech32(msg.From)
	return []types.AccAddress{addr}
}
func (msg *MsgTransfer) GetSignBytes() []byte {
	return types.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgTransfer) ValidateBasic() error {
	if _, err := types.AccAddressFromBech32(msg.From); err != nil {
		return errors.Wrapf(errors.ErrInvalidAddress, "invalid from: %v", err)
	}
	if _, err := types.AccAddressFromBech32(msg.To); err != nil {
		return errors.Wrapf(errors.ErrInvalidAddress, "invalid to: %v", err)
	}
	if !msg.Amount.IsPositive() {
		return errors.Wrap(errors.ErrInvalidRequest, "transfer amount must be positive")
	}
	return nil
}