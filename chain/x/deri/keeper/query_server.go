package keeper

import (
	"context"

	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/Decentralized-Rights-Protocol/drp/x/deri/types"
)

type QueryServer struct {
	Keeper
}

func NewQueryServerImpl(keeper Keeper) types.QueryServer {
	return &QueryServer{Keeper: keeper}
}

func (qs QueryServer) Balance(goCtx context.Context, req *types.QueryBalanceRequest) (*types.QueryBalanceResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)
	addr, err := sdk.AccAddressFromBech32(req.Address)
	if err != nil {
		return nil, err
	}
	balance := qs.Keeper.GetBalance(ctx, addr)
	return &types.QueryBalanceResponse{Balance: balance.String()}, nil
}

func (qs QueryServer) Supply(goCtx context.Context, req *types.QuerySupplyRequest) (*types.QuerySupplyResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)
	totalSupply := qs.Keeper.GetTotalSupply(ctx)
	return &types.QuerySupplyResponse{TotalSupply: totalSupply.String(), CirculatingSupply: totalSupply.String()}, nil
}