// Package cmd provides the root CLI command for the drpd binary.
package cmd

import (
	"errors"
	"io"
	"os"

	dbm "github.com/cometbft/cometbft-db"
	cmtlog "github.com/cometbft/cometbft/libs/log"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"github.com/cosmos/cosmos-sdk/baseapp"
	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/config"
	"github.com/cosmos/cosmos-sdk/client/debug"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/cosmos/cosmos-sdk/client/keys"
	"github.com/cosmos/cosmos-sdk/client/pruning"
	"github.com/cosmos/cosmos-sdk/client/rpc"
	"github.com/cosmos/cosmos-sdk/client/snapshot"
	"github.com/cosmos/cosmos-sdk/server"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/module"
	"github.com/cosmos/cosmos-sdk/version"
	authtypes "github.com/cosmos/cosmos-sdk/x/auth/types"
	banktypes "github.com/cosmos/cosmos-sdk/x/bank/types"
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
	app.ModuleBasics.RegisterInterfaces(encodingConfig.InterfaceRegistry)

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
			// Set up client context, load config, and intercept server config.
			if err := client.SetCmdClientContextHandler(initClientCtx, cmd); err != nil {
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

func addModuleInitFlags(_ *cobra.Command) {}

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
// Currently passes trace-store information; extend as needed.
func baseAppOptionsFromAppOpts(_ servertypes.AppOptions) []func(*baseapp.BaseApp) {
	return nil
}

// initAppConfig returns a custom app.toml template and the default config struct.
// Returning empty string lets the SDK use its own defaults.
func initAppConfig() (string, interface{}) {
	return "", nil
}

// ── Module manager accessor ───────────────────────────────────────────────────

// GetModuleBasics returns the module BasicManager (used by tests and external tooling).
func GetModuleBasics() module.BasicManager {
	return app.ModuleBasics
}
