// Package cmd provides the root CLI command for the drpd binary.
package cmd

import (
	"errors"
	"io"
	"os"

	dbm "github.com/cometbft/cometbft-db"
	cmtlog "github.com/cometbft/cometbft/libs/log"
	"github.com/spf13/cobra"

	"github.com/cosmos/cosmos-sdk/baseapp"
	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/config"
	"github.com/cosmos/cosmos-sdk/client/debug"
	"github.com/cosmos/cosmos-sdk/client/keys"
	"github.com/cosmos/cosmos-sdk/client/pruning"
	"github.com/cosmos/cosmos-sdk/client/rpc"
	"github.com/cosmos/cosmos-sdk/client/snapshot"
	"github.com/cosmos/cosmos-sdk/server"
	serverconfig "github.com/cosmos/cosmos-sdk/server/config"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/module"
	"github.com/cosmos/cosmos-sdk/version"
	authcmd "github.com/cosmos/cosmos-sdk/x/auth/client/cli"
	authtypes "github.com/cosmos/cosmos-sdk/x/auth/types"
	banktypes "github.com/cosmos/cosmos-sdk/x/bank/types"
	"github.com/cosmos/cosmos-sdk/x/crisis"
	genutilcli "github.com/cosmos/cosmos-sdk/x/genutil/client/cli"
	genutiltypes "github.com/cosmos/cosmos-sdk/x/genutil/types"

	"github.com/decentralized-rights-protocol/drp/chain/app"
)

// DefaultNodeHome is the default home directory for the drpd binary.
// Overridable with the --home flag or DRPD_HOME env var.
const DefaultNodeHome = app.DefaultNodeHome

// NewRootCmd creates the root command for drpd, registering all sub-commands.
func NewRootCmd() (*cobra.Command, app.EncodingConfig) {
	encodingConfig := app.MakeEncodingConfig()
	sdk.DefaultBondDenom = app.BondDenom

	initClientCtx := client.Context{}.
		WithCodec(encodingConfig.Marshaler).
		WithInterfaceRegistry(encodingConfig.InterfaceRegistry).
		WithTxConfig(encodingConfig.TxConfig).
		WithLegacyAmino(encodingConfig.Amino).
		WithInput(os.Stdin).
		WithAccountRetriever(authtypes.AccountRetriever{}).
		WithHomeDir(DefaultNodeHome).
		WithViper("DRPD")

	rootCmd := &cobra.Command{
		Use:   "drpd",
		Short: "DRP — Decentralized Rights Protocol sovereign L1 node",
		Long: `drpd is the daemon and CLI for the Decentralized Rights Protocol.

DRP is a sovereign Cosmos SDK / CometBFT L1 blockchain focused on:
  - Proof-of-Activity (PoAT): verifiable contribution without identity exposure
  - Proof-of-Status (PoST): non-transferable trust status evolution
  - IPFS-anchored evidence commitments (on-chain CID/hash only)
  - Rights-aware governance

Chain ID  : drp-testnet-1
Bond denom: udrp
`,
		PersistentPreRunE: func(cmd *cobra.Command, _ []string) error {
			clientCtx, err := client.ReadPersistentCommandFlags(initClientCtx, cmd.Flags())
			if err != nil {
				return err
			}
			clientCtx, err = config.ReadFromClientConfig(clientCtx)
			if err != nil {
				return err
			}
			if err := client.SetCmdClientContextHandler(clientCtx, cmd); err != nil {
				return err
			}
			customAppTemplate, customAppConfig := initAppConfig()
			return server.InterceptConfigsPreRunHandler(cmd, customAppTemplate, customAppConfig, nil)
		},
	}

	initRootCmd(rootCmd, encodingConfig)
	return rootCmd, encodingConfig
}

// initRootCmd adds all sub-commands to the root command.
func initRootCmd(rootCmd *cobra.Command, encodingConfig app.EncodingConfig) {
	rootCmd.AddCommand(
		// Chain initialisation.
		genutilcli.InitCmd(app.ModuleBasics, DefaultNodeHome),
		// Genesis helpers.
		genutilcli.CollectGenTxsCmd(banktypes.GenesisBalancesIterator{}, DefaultNodeHome, genutiltypes.DefaultMessageValidator),
		genutilcli.GenTxCmd(app.ModuleBasics, encodingConfig.TxConfig, banktypes.GenesisBalancesIterator{}, DefaultNodeHome),
		genutilcli.ValidateGenesisCmd(app.ModuleBasics),
		AddGenesisAccountCmd(DefaultNodeHome),
		// Key management.
		keys.Commands(DefaultNodeHome),
		// Node status & config.
		rpc.StatusCommand(),
		config.Cmd(),
		queryCommand(),
		txCommand(),
		// Developer utilities.
		debug.Cmd(),
		version.NewVersionCommand(),
		// Pruning and snapshot utilities.
		pruning.Cmd(newApp, DefaultNodeHome),
		snapshot.Cmd(newApp),
	)

	// Add server commands: start, tendermint unsafe-reset-all, export, etc.
	server.AddCommands(rootCmd, DefaultNodeHome, newApp, appExport, addModuleInitFlags)

	// Add the default flags so --home, --log-level, etc. work.
	// Note: --home flag is set up by CometBFT; no need to redefine here.
}

func addModuleInitFlags(cmd *cobra.Command) { crisis.AddModuleInitFlags(cmd) }

func queryCommand() *cobra.Command {
	cmd := &cobra.Command{Use: "query", Aliases: []string{"q"}, Short: "Query chain state", RunE: client.ValidateCmd}
	cmd.AddCommand(rpc.QueryEventForTxCmd(), authcmd.GetAccountCmd(), rpc.ValidatorCommand(), rpc.BlockCommand(), authcmd.QueryTxsByEventsCmd(), authcmd.QueryTxCmd())
	app.ModuleBasics.AddQueryCommands(cmd)
	return cmd
}

func txCommand() *cobra.Command {
	cmd := &cobra.Command{Use: "tx", Short: "Transaction subcommands", RunE: client.ValidateCmd}
	cmd.AddCommand(authcmd.GetSignCommand(), authcmd.GetSignBatchCommand(), authcmd.GetMultiSignCommand(), authcmd.GetMultiSignBatchCmd(), authcmd.GetValidateSignaturesCommand(), authcmd.GetBroadcastCommand(), authcmd.GetEncodeCommand(), authcmd.GetDecodeCommand(), authcmd.GetAuxToFeeCommand())
	app.ModuleBasics.AddTxCommands(cmd)
	return cmd
}

// newApp constructs a DRPApp from the server start command context.
func newApp(
	logger cmtlog.Logger,
	db dbm.DB,
	traceStore io.Writer,
	appOpts servertypes.AppOptions,
) servertypes.Application {
	// Override the bond denom for the DRP chain.
	// This is a placeholder; governance will formalise monetary policy.
	sdk.DefaultBondDenom = app.BondDenom

	return app.NewDRPApp(
		logger,
		db,
		traceStore,
		true,
		appOpts,
		baseAppOptionsFromAppOpts(appOpts)...,
	)
}

// appExport exports chain state for genesis migration or snapshot tooling.
func appExport(
	logger cmtlog.Logger,
	db dbm.DB,
	traceStore io.Writer,
	height int64,
	forZeroHeight bool,
	jailAllowedAddrs []string,
	appOpts servertypes.AppOptions,
	modulesToExport []string,
) (servertypes.ExportedApp, error) {
	drpApp := app.NewDRPApp(
		logger, db, traceStore,
		height == -1, // loadLatest when no specific height requested
		appOpts,
	)

	if height != -1 {
		if err := drpApp.LoadVersion(height); err != nil {
			return servertypes.ExportedApp{}, errors.New("failed to load height: " + err.Error())
		}
	}

	return drpApp.ExportAppStateAndValidators(forZeroHeight, jailAllowedAddrs, modulesToExport)
}

// baseAppOptionsFromAppOpts maps AppOptions to baseapp functional options.
// Use the SDK mapping for gas prices, pruning, snapshots, halt options and caches.
func baseAppOptionsFromAppOpts(appOpts servertypes.AppOptions) []func(*baseapp.BaseApp) {
	return server.DefaultBaseappOptions(appOpts)
}

// initAppConfig returns a custom app.toml template and the default config struct.
// A zero udrp minimum permits localnet startup; operators may override it.
func initAppConfig() (string, interface{}) {
	cfg := serverconfig.DefaultConfig()
	cfg.MinGasPrices = "0" + app.BondDenom
	return serverconfig.DefaultConfigTemplate, cfg
}

// ── Module manager accessor ───────────────────────────────────────────────────

// GetModuleBasics returns the module BasicManager (used by tests and external tooling).
func GetModuleBasics() module.BasicManager {
	return app.ModuleBasics
}
