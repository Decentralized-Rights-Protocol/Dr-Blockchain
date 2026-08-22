package cli

import (
	"fmt"

	"github.com/spf13/cobra"

	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/cosmos/cosmos-sdk/client/tx"

	"github.com/Decentralized-Rights-Protocol/drp/x/deri/types"
)

func GetTxCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   types.ModuleName,
		Short: "$DeRi token transactions",
		Long: "Commands for interacting with the $DeRi token module.",
	}
	cmd.AddCommand(
		NewMintCmd(),
		NewBurnCmd(),
		NewTransferCmd(),
	)
	return cmd
}

func NewMintCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "mint [recipient] [amount] [reason] [activity-id] [verification-hash]",
		Short: "Mint $DeRi tokens",
		Args: cobra.ExactArgs(5),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientTxContext(cmd)
			if err != nil {
				return err
			}
			msg := types.NewMsgMint(args[0], args[2], args[3], args[4], sdk.NewIntFromString(args[1]))
			if err := msg.ValidateBasic(); err != nil {
				return err
			}
			return tx.GenerateOrBroadcastTxCLI(clientCtx, cmd.Flags(), msg)
		},
	}
	flags.AddTxFlagsToCmd(cmd)
	return cmd
}

func NewBurnCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "burn [amount] [reason]",
		Short: "Burn $DeRi tokens",
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientTxContext(cmd)
			if err != nil {
				return err
			}
			msg := types.NewMsgBurn(clientCtx.GetFromAddress().String(), args[1], sdk.NewIntFromString(args[0]))
			if err := msg.ValidateBasic(); err != nil {
				return err
			}
			return tx.GenerateOrBroadcastTxCLI(clientCtx, cmd.Flags(), msg)
		},
	}
	flags.AddTxFlagsToCmd(cmd)
	return cmd
}

func NewTransferCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "transfer [to] [amount]",
		Short: "Transfer $DeRi tokens",
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx, err := client.GetClientTxContext(cmd)
			if err != nil {
				return err
			}
			msg := types.NewMsgTransfer(clientCtx.GetFromAddress().String(), args[0], sdk.NewIntFromString(args[1]))
			if err := msg.ValidateBasic(); err != nil {
				return err
			}
			return tx.GenerateOrBroadcastTxCLI(clientCtx, cmd.Flags(), msg)
		},
	}
	flags.AddTxFlagsToCmd(cmd)
	return cmd
}