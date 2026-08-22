package cli

import (
	"github.com/spf13/cobra"

	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/cosmos/cosmos-sdk/client/tx"
	"github.com/cosmos/cosmos-sdk/version"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/types"
)

// GetTxCmd returns the transaction commands for the deri module
func GetTxCmd() *cobra.Command {
	txCmd := &cobra.Command{
		Use:                        types.ModuleName,
		Short:                      "$DeRi token transaction subcommands",
		DisableFlagParsing:        true,
		SuggestionsMinimumDistance: 2,
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientTxContext(cmd)
			if err != nil {
				return err
			}

			return clientCtx.PrintOutputTemplate(GetTxCmd().UsageTemplate())
		},
	}

	txCmd.AddCommand(
		NewTransferCmd(),
		NewMintCmd(),
		NewBurnCmd(),
	)

	return txCmd
}

// NewTransferCmd returns the command for transferring $DeRi tokens
func NewTransferCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "transfer [from] [to] [amount]",
		Short: "Transfer $DeRi tokens to another account",
		Long: `Transfer $DeRi tokens from one account to another.

Amount is in uderi (1 deri = 1,000,000 uderi).

Examples:
  drpd tx deri transfer <from> <to> 1000000
  drpd tx deri transfer <from> <to> 1000000 --from=<key-name> --chain-id=<chain-id>`,
		Args: cobra.ExactArgs(3),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientTxContext(cmd)
			if err != nil {
				return err
			}

			// Parse arguments
			from := args[0]
			to := args[1]
			amount := args[2]

			// Create message
			msg := types.NewMsgTransfer(from, to, amount)

			// Validate message
			if err := msg.ValidateBasic(); err != nil {
				return err
			}

			// Build and sign transaction
			return tx.GenerateOrBroadcastTxCLI(clientCtx, cmd.Flags(), msg)
		},
	}

	flags.AddTxFlagsToCmd(cmd)
	return cmd
}

// NewMintCmd returns the command for minting $DeRi tokens
// This is restricted to authorized module accounts
func NewMintCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "mint [to] [amount] [reason] [signer]",
		Short: "Mint new $DeRi tokens (authorized only)",
		Long: `Mint new $DeRi tokens to an account.

This is a restricted operation that can only be called by authorized module accounts.
Amount is in uderi (1 deri = 1,000,000 uderi).

Examples:
  drpd tx deri mint <to> 1000000 "reward" <reward-module-address>
  drpd tx deri mint <to> 1000000 "initial_distribution" <gov-module-address> --from=<key-name> --chain-id=<chain-id>`,
		Args: cobra.ExactArgs(4),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientTxContext(cmd)
			if err != nil {
				return err
			}

			// Parse arguments
			to := args[0]
			amount := args[1]
			reason := args[2]
			signer := args[3]

			// Create message
			msg := types.NewMsgMint(to, amount, reason, signer)

			// Validate message
			if err := msg.ValidateBasic(); err != nil {
				return err
			}

			// Build and sign transaction
			return tx.GenerateOrBroadcastTxCLI(clientCtx, cmd.Flags(), msg)
		},
	}

	flags.AddTxFlagsToCmd(cmd)
	return cmd
}

// NewBurnCmd returns the command for burning $DeRi tokens
func NewBurnCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "burn [from] [amount] [reason]",
		Short: "Burn $DeRi tokens",
		Long: `Burn $DeRi tokens from an account.

Amount is in uderi (1 deri = 1,000,000 uderi).

Examples:
  drpd tx deri burn <from> 1000000 "fee_payment"
  drpd tx deri burn <from> 1000000 "token_removal" --from=<key-name> --chain-id=<chain-id>`,
		Args: cobra.ExactArgs(3),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientTxContext(cmd)
			if err != nil {
				return err
			}

			// Parse arguments
			from := args[0]
			amount := args[1]
			reason := args[2]

			// Create message
			msg := types.NewMsgBurn(from, amount, reason)

			// Validate message
			if err := msg.ValidateBasic(); err != nil {
				return err
			}

			// Build and sign transaction
			return tx.GenerateOrBroadcastTxCLI(clientCtx, cmd.Flags(), msg)
		},
	}

	flags.AddTxFlagsToCmd(cmd)
	return cmd
}

// GetQueryCmd returns the query commands for the deri module
func GetQueryCmd() *cobra.Command {
	queryCmd := &cobra.Command{
		Use:                        types.ModuleName,
		Short:                      "Query commands for the deri module",
		DisableFlagParsing:        true,
		SuggestionsMinimumDistance: 2,
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}

			return clientCtx.PrintOutputTemplate(GetQueryCmd().UsageTemplate())
		},
	}

	queryCmd.AddCommand(
		NewQueryBalanceCmd(),
		NewQueryTotalSupplyCmd(),
		NewQueryParamsCmd(),
	)

	return queryCmd
}

// NewQueryBalanceCmd returns the command for querying an account's balance
func NewQueryBalanceCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "balance [address]",
		Short: "Query $DeRi token balance",
		Long:  "Query the $DeRi token balance of an account.",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}

			address := args[0]

			// Create query request
			req := &types.QueryBalanceRequest{
				Address: address,
			}

			// Query the balance
			queryClient := types.NewQueryClient(clientCtx)
			resp, err := queryClient.Balance(cmd.Context(), req)
			if err != nil {
				return err
			}

			// Print the response
			return clientCtx.PrintOutput(resp)
		},
	}

	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}

// NewQueryTotalSupplyCmd returns the command for querying the total supply
func NewQueryTotalSupplyCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "total-supply",
		Short: "Query total $DeRi supply",
		Long:  "Query the total supply of $DeRi tokens.",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}

			// Create query request
			req := &types.QueryTotalSupplyRequest{}

			// Query the total supply
			queryClient := types.NewQueryClient(clientCtx)
			resp, err := queryClient.TotalSupply(cmd.Context(), req)
			if err != nil {
				return err
			}

			// Print the response
			return clientCtx.PrintOutput(resp)
		},
	}

	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}

// NewQueryParamsCmd returns the command for querying the module parameters
func NewQueryParamsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "params",
		Short: "Query deri module parameters",
		Long:  "Query the parameters of the deri module.",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientQueryContext(cmd)
			if err != nil {
				return err
			}

			// Create query request
			req := &types.QueryParamsRequest{}

			// Query the parameters
			queryClient := types.NewQueryClient(clientCtx)
			resp, err := queryClient.Params(cmd.Context(), req)
			if err != nil {
				return err
			}

			// Print the response
			return clientCtx.PrintOutput(resp)
		},
	}

	flags.AddQueryFlagsToCmd(cmd)
	return cmd
}

// Version returns the module version information
func Version() *version.Info {
	return version.NewInfo("deri", version.Version, "cosmos-sdk", "0.0.1", "")
}
