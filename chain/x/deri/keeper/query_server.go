package keeper

import (
	"context"

	sdk "github.com/cosmos/cosmos-sdk/types"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/types"
)

// queryServer is the server API for Query service
// It implements the deri.Query service
type queryServer struct {
	Keeper
}

// NewQueryServerImpl returns an implementation of the QueryServer interface
// for the provided Keeper
func NewQueryServerImpl(keeper Keeper) types.QueryServer {
	return &queryServer{Keeper: keeper}
}

var _ types.QueryServer = queryServer{}

// Balance implements the Query/Balance RPC method
func (s queryServer) Balance(goCtx context.Context, req *types.QueryBalanceRequest) (*types.QueryBalanceResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	address, err := sdk.AccAddressFromBech32(req.Address)
	if err != nil {
		return nil, sdk.ErrInvalidAddress.Wrapf("invalid address: %s", req.Address)
	}

	balance := s.Keeper.GetBalance(ctx, address)

	return &types.QueryBalanceResponse{
		Balance: balance.String(),
	}, nil
}

// TotalSupply implements the Query/TotalSupply RPC method
func (s queryServer) TotalSupply(goCtx context.Context, req *types.QueryTotalSupplyRequest) (*types.QueryTotalSupplyResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	totalSupply := s.Keeper.GetTotalSupply(ctx)

	return &types.QueryTotalSupplyResponse{
		TotalSupply: totalSupply.String(),
	}, nil
}

// Params implements the Query/Params RPC method
func (s queryServer) Params(goCtx context.Context, req *types.QueryParamsRequest) (*types.QueryParamsResponse, error) {
	ctx := sdk.UnwrapSDKContext(goCtx)

	params, err := s.Keeper.GetParams(ctx)
	if err != nil {
		return nil, err
	}

	return &types.QueryParamsResponse{
		Params: params,
	}, nil
}
