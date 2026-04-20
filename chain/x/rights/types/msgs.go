package types

import (
	sdk "github.com/cosmos/cosmos-sdk/types"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
)

const TypeMsgSubmitRightsProposal = "submit_rights_proposal"

var _ sdk.Msg = &MsgSubmitRightsProposal{}

// MsgSubmitRightsProposal submits a DRP rights-focused governance proposal.
type MsgSubmitRightsProposal struct {
	Proposer        string         `json:"proposer"`
	Title           string         `json:"title"`
	Description     string         `json:"description"`
	RightsCategory  RightsCategory `json:"rights_category"`
	EvidenceCID     string         `json:"evidence_cid,omitempty"`
	ImpactStatement string         `json:"impact_statement,omitempty"`
}

func (msg *MsgSubmitRightsProposal) Route() string { return RouterKey }
func (msg *MsgSubmitRightsProposal) Type() string  { return TypeMsgSubmitRightsProposal }
func (msg *MsgSubmitRightsProposal) GetSigners() []sdk.AccAddress {
	addr, _ := sdk.AccAddressFromBech32(msg.Proposer)
	return []sdk.AccAddress{addr}
}
func (msg *MsgSubmitRightsProposal) GetSignBytes() []byte {
	return sdk.MustSortJSON(ModuleCdc.MustMarshalJSON(msg))
}
func (msg *MsgSubmitRightsProposal) ValidateBasic() error {
	if _, err := sdk.AccAddressFromBech32(msg.Proposer); err != nil {
		return sdkerrors.ErrInvalidAddress.Wrapf("invalid proposer: %s", err)
	}
	if msg.Title == "" {
		return ErrInvalidProposalTitle
	}
	if len(msg.Title) > 140 {
		return sdkerrors.ErrInvalidRequest.Wrap("title exceeds 140 characters")
	}
	if len(msg.Description) > 1000 {
		return sdkerrors.ErrInvalidRequest.Wrap("description exceeds 1000 characters")
	}
	return nil
}
