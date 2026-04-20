// Package main is the entry point for the drpd binary.
//
// drpd is the node daemon and CLI for the Decentralized Rights Protocol —
// a sovereign Cosmos SDK / CometBFT L1 chain.
//
// Build:
//
//	cd chain && go build -o bin/drpd ./cmd/drpd
//
// Quick start (single-validator localnet):
//
//	./scripts/localnet.sh
package main

import (
	"os"

	svrcmd "github.com/cosmos/cosmos-sdk/server/cmd"

	"github.com/decentralized-rights-protocol/drp/chain/cmd/drpd/cmd"
)

func main() {
	rootCmd, _ := cmd.NewRootCmd()
	if err := svrcmd.Execute(rootCmd, "DRPD", cmd.DefaultNodeHome); err != nil {
		os.Exit(1)
	}
}
