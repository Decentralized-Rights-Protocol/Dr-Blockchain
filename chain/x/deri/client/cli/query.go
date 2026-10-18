package cli

import (
	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/decentralized-rights-protocol/drp/chain/x/deri/types"
	"github.com/spf13/cobra"
)

func GetQueryCmd() *cobra.Command {
	cmd := &cobra.Command{Use: types.ModuleName, Short: "Query $DeRi token state", DisableFlagParsing: true, RunE: client.ValidateCmd}
	cmd.AddCommand(NewQueryBalanceCmd(), NewQueryTotalSupplyCmd(), NewQueryParamsCmd())
	return cmd
}

func NewQueryBalanceCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use: "balance [address]", Short: "Query $DeRi balance", Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}
			resp, err := types.NewQueryClient(ctx).Balance(cmd.Context(), &types.QueryBalanceRequest{Address: args[0]})
			if err != nil {
				return err
			}
			return ctx.PrintProto(resp)
		},
	}
	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}

func NewQueryTotalSupplyCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use: "total-supply", Aliases: []string{"supply"}, Short: "Query total $DeRi supply", Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}
			resp, err := types.NewQueryClient(ctx).TotalSupply(cmd.Context(), &types.QueryTotalSupplyRequest{})
			if err != nil {
				return err
			}
			return ctx.PrintProto(resp)
		},
	}
	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}

// NewQuerySupplyCmd preserves the earlier CLI constructor with the canonical RPC.
func NewQuerySupplyCmd() *cobra.Command { return NewQueryTotalSupplyCmd() }

func NewQueryParamsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use: "params", Short: "Query DeRi parameters", Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}
			resp, err := types.NewQueryClient(ctx).Params(cmd.Context(), &types.QueryParamsRequest{})
			if err != nil {
				return err
			}
			return ctx.PrintProto(resp)
		},
	}
	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}
