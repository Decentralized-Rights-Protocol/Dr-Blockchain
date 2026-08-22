package types

import (
	"fmt"

	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
)

// Msg types for the deri module
const (
	TypeMsgTransfer = "transfer"
	TypeMsgMint    = "mint"
	TypeMsgBurn    = "burn"
)

// MsgTransfer defines a message to transfer $DeRi tokens
// Implements Msg interface
type MsgTransfer struct {
	From   string `json:"from" yaml:"from"`
	To     string `json:"to" yaml:"to"`
	Amount string `json:"amount" yaml:"amount"` // in uderi
}

// NewMsgTransfer creates a new MsgTransfer
func NewMsgTransfer(from, to, amount string) *MsgTransfer {
	return &MsgTransfer{
		From:   from,
		To:     to,
		Amount: amount,
	}
}

// Route implements Msg
func (msg *MsgTransfer) Route() string {
	return RouterKey
}

// Type implements Msg
func (msg *MsgTransfer) Type() string {
	return TypeMsgTransfer
}

// ValidateBasic implements Msg
func (msg *MsgTransfer) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.From); err != nil {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidAddress, "invalid from address: %s", msg.From)
	}
	if _, err := sdk.AccAddressFromBech32(msg.To); err != nil {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidAddress, "invalid to address: %s", msg.To)
	}
	if msg.Amount == "" {
		return sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, "amount cannot be empty")
	}
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidRequest, "invalid amount: %s", msg.Amount)
	}
	if amount.LT(sdk.NewInt(1)) {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidRequest, "amount must be positive: %s", msg.Amount)
	}
	return nil
}

// GetSignBytes implements Msg
func (msg *MsgTransfer) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}

// GetSigners implements Msg
func (msg *MsgTransfer) GetSigners() []sdk.AccAddress {
	from, err := sdk.AccAddressFromBech32(msg.From)
	if err != nil {
		panic(err)
	}
	return []sdk.AccAddress{from}
}

// MsgMint defines a message to mint $DeRi tokens
// Only callable by authorized modules (not directly by users)
// Implements Msg interface
type MsgMint struct {
	To      string `json:"to" yaml:"to"`
	Amount  string `json:"amount" yaml:"amount"` // in uderi
	Reason  string `json:"reason" yaml:"reason"` // e.g., "reward", "initial_distribution"
	Signer  string `json:"signer" yaml:"signer"` // module account that authorized this
}

// NewMsgMint creates a new MsgMint
func NewMsgMint(to, amount, reason, signer string) *MsgMint {
	return &MsgMint{
		To:     to,
		Amount: amount,
		Reason: reason,
		Signer: signer,
	}
}

// Route implements Msg
func (msg *MsgMint) Route() string {
	return RouterKey
}

// Type implements Msg
func (msg *MsgMint) Type() string {
	return TypeMsgMint
}

// ValidateBasic implements Msg
func (msg *MsgMint) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.To); err != nil {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidAddress, "invalid to address: %s", msg.To)
	}
	if msg.Amount == "" {
		return sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, "amount cannot be empty")
	}
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidRequest, "invalid amount: %s", msg.Amount)
	}
	if amount.LT(sdk.NewInt(1)) {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidRequest, "amount must be positive: %s", msg.Amount)
	}
	if msg.Reason == "" {
		return sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, "reason cannot be empty")
	}
	if msg.Signer == "" {
		return sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, "signer cannot be empty")
	}
	return nil
}

// GetSignBytes implements Msg
func (msg *MsgMint) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}

// GetSigners implements Msg
func (msg *MsgMint) GetSigners() []sdk.AccAddress {
	signer, err := sdk.AccAddressFromBech32(msg.Signer)
	if err != nil {
		panic(err)
	}
	return []sdk.AccAddress{signer}
}

// MsgBurn defines a message to burn $DeRi tokens
// Implements Msg interface
type MsgBurn struct {
	From   string `json:"from" yaml:"from"`
	Amount string `json:"amount" yaml:"amount"` // in uderi
	Reason string `json:"reason" yaml:"reason"`
}

// NewMsgBurn creates a new MsgBurn
func NewMsgBurn(from, amount, reason string) *MsgBurn {
	return &MsgBurn{
		From:   from,
		Amount: amount,
		Reason: reason,
	}
}

// Route implements Msg
func (msg *MsgBurn) Route() string {
	return RouterKey
}

// Type implements Msg
func (msg *MsgBurn) Type() string {
	return TypeMsgBurn
}

// ValidateBasic implements Msg
func (msg *MsgBurn) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.From); err != nil {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidAddress, "invalid from address: %s", msg.From)
	}
	if msg.Amount == "" {
		return sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, "amount cannot be empty")
	}
	amount, ok := sdk.NewIntFromString(msg.Amount)
	if !ok {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidRequest, "invalid amount: %s", msg.Amount)
	}
	if amount.LT(sdk.NewInt(1)) {
		return sdkerrors.Wrapf(sdkerrors.ErrInvalidRequest, "amount must be positive: %s", msg.Amount)
	}
	if msg.Reason == "" {
		return sdkerrors.Wrap(sdkerrors.ErrInvalidRequest, "reason cannot be empty")
	}
	return nil
}

// GetSignBytes implements Msg
func (msg *MsgBurn) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}

// GetSigners implements Msg
func (msg *MsgBurn) GetSigners() []sdk.AccAddress {
	from, err := sdk.AccAddressFromBech32(msg.From)
	if err != nil {
		panic(err)
	}
	return []sdk.AccAddress{from}
}

// RegisterLegacyAminoCodec registers the legacy amino codec
func RegisterLegacyAminoCodec(cdc *sdk.LegacyAmino) {
	cdc.RegisterConcrete(&MsgTransfer{}, "drp/deri/MsgTransfer", nil)
	cdc.RegisterConcrete(&MsgMint{}, "drp/deri/MsgMint", nil)
	cdc.RegisterConcrete(&MsgBurn{}, "drp/deri/MsgBurn", nil)
}

// ModuleCdc defines the codec for the deri module
var ModuleCdc = sdk.NewLegacyAmino()

func init() {
	RegisterLegacyAminoCodec(ModuleCdc)
}

// GetMsgTypeURL returns the type URL for a message type
func GetMsgTypeURL(msg sdk.Msg) string {
	switch m := msg.(type) {
	case *MsgTransfer:
		return "/drp.deri.MsgTransfer"
	case *MsgMint:
		return "/drp.deri.MsgMint"
	case *MsgBurn:
		return "/drp.deri.MsgBurn"
	default:
		return fmt.Sprintf("unknown message type: %T", m)
	}
}
