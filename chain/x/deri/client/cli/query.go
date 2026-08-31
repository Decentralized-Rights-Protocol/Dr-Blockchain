package cli

import (
	"github.com/spf13/cobra"

	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/flags"

	"github.com/Decentralized-Rights-Protocol/drp/x/deri/types"
)

func GetQueryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   types.ModuleName,
		Short: "Query $DeRi token state",
		Long: "Query commands for the $DeRi token module.",
	}
	cmd.AddCommand(
		NewQueryBalanceCmd(),
		NewQuerySupplyCmd(),
	)
	return cmd
}

func NewQueryBalanceCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "balance [address]",
		Short: "Query $DeRi balance",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}
			queryClient := types.NewQueryClient(clientCtx)
			resp, err := queryClient.Balance(context.Background(), &types.QueryBalanceRequest{Address: args[0]})
			if err != nil {
				return err
			}
			return clientCtx.PrintOutput(resp)
		},
	}
	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}

func NewQuerySupplyCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "supply",
		Short: "Query $DeRi total supply",
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}
			queryClient := types.NewQueryClient(clientCtx)
			resp, err := queryClient.Supply(context.Background(), &types.QuerySupplyRequest{})
			if err != nil {
				return err
			}
			return clientCtx.PrintOutput(resp)
		},
	}
	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}