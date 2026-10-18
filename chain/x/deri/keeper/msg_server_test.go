package keeper

import (
	"context"
	"testing"

	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/decentralized-rights-protocol/drp/chain/x/deri/types"
)

func TestMintAuthorityFailsClosed(t *testing.T) {
	if (Keeper{}).IsAuthorizedMinter(sdk.Context{}, sdk.AccAddress([]byte("12345678901234567890"))) {
		t.Fatal("minting authorized before a policy exists")
	}
}

func TestMessageValidationBeforeStateAccess(t *testing.T) {
	server := NewMsgServerImpl(Keeper{})
	// No SDK context or store: invalid messages must be rejected before unwrapping.
	if _, err := server.Transfer(context.Background(), nil); err == nil {
		t.Fatal("nil transfer accepted")
	}
	if _, err := server.Mint(context.Background(), nil); err == nil {
		t.Fatal("nil mint accepted")
	}
	if _, err := server.Burn(context.Background(), nil); err == nil {
		t.Fatal("nil burn accepted")
	}
	address := sdk.AccAddress([]byte("12345678901234567890")).String()
	if _, err := server.Transfer(context.Background(), types.NewMsgTransfer(address, address, "-1")); err == nil {
		t.Fatal("negative transfer accepted")
	}
	if _, err := server.Burn(context.Background(), types.NewMsgBurn(address, "0", "test")); err == nil {
		t.Fatal("zero burn accepted")
	}
	if _, err := server.Mint(context.Background(), types.NewMsgMint(address, "1", "test", "invalid")); err == nil {
		t.Fatal("invalid signer accepted")
	}
}
