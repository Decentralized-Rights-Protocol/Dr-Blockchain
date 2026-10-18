package cli

import (
	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/cosmos/cosmos-sdk/client/tx"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/version"
	"github.com/decentralized-rights-protocol/drp/chain/x/deri/types"
	"github.com/spf13/cobra"
)

func GetTxCmd() *cobra.Command {
	cmd := &cobra.Command{Use: types.ModuleName, Short: "$DeRi token transaction subcommands", DisableFlagParsing: true, SuggestionsMinimumDistance: 2, RunE: client.ValidateCmd}
	cmd.AddCommand(NewTransferCmd(), NewMintCmd(), NewBurnCmd())
	return cmd
}

func NewTransferCmd() *cobra.Command {
	return newTxCmd("transfer [from] [to] [amount]", "Transfer $DeRi tokens", 3, func(args []string) sdk.Msg {
		return types.NewMsgTransfer(args[0], args[1], args[2])
	})
}

func NewMintCmd() *cobra.Command {
	return newTxCmd("mint [to] [amount] [reason] [signer]", "Mint $DeRi tokens (disabled pending authority policy)", 4, func(args []string) sdk.Msg {
		return types.NewMsgMint(args[0], args[1], args[2], args[3])
	})
}

func NewBurnCmd() *cobra.Command {
	return newTxCmd("burn [from] [amount] [reason]", "Burn $DeRi tokens", 3, func(args []string) sdk.Msg {
		return types.NewMsgBurn(args[0], args[1], args[2])
	})
}

func newTxCmd(use, short string, count int, makeMsg func([]string) sdk.Msg) *cobra.Command {
	cmd := &cobra.Command{Use: use, Short: short, Args: cobra.ExactArgs(count), RunE: func(cmd *cobra.Command, args []string) error {
		ctx, err := client.GetClientTxContext(cmd)
		if err != nil {
			return err
		}
		msg := makeMsg(args)
		if err := msg.ValidateBasic(); err != nil {
			return err
		}
		return tx.GenerateOrBroadcastTxCLI(ctx, cmd.Flags(), msg)
	}}
	flags.AddTxFlagsToCmd(cmd)
	return cmd
}

func Version() *version.Info { return &version.Info{Name: "deri", Version: version.Version} }
