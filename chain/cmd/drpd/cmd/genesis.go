package cmd

import (
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"

	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/cosmos/cosmos-sdk/codec"
	"github.com/cosmos/cosmos-sdk/server"
	sdk "github.com/cosmos/cosmos-sdk/types"
	authtypes "github.com/cosmos/cosmos-sdk/x/auth/types"
	authvesting "github.com/cosmos/cosmos-sdk/x/auth/vesting/types"
	banktypes "github.com/cosmos/cosmos-sdk/x/bank/types"
	"github.com/cosmos/cosmos-sdk/x/genutil"
	genutiltypes "github.com/cosmos/cosmos-sdk/x/genutil/types"
)

// AddGenesisAccountCmd returns a command to add a genesis account to the genesis.json.
// This command mirrors simapp's AddGenesisAccountCmd so localnet setup works
// without depending on external tooling.
func AddGenesisAccountCmd(defaultNodeHome string) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "add-genesis-account [address_or_key_name] [coin][,[coin]]",
		Short: "Add a genesis account to genesis.json",
		Long: `Add a genesis account to genesis.json. The provided account must specify
the account address or key name and a list of initial coins. The list of
initial tokens must contain valid denominations. Accounts may optionally be
supplied with vesting parameters.

For DRP localnet setup: use udrp as the base denomination.
Example:
  drpd add-genesis-account drp-validator-1 10000000000udrp
`,
		Args: cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			clientCtx := client.GetClientContextFromCmd(cmd)
			cdc := clientCtx.Codec

			serverCtx := server.GetServerContextFromCmd(cmd)
			config := serverCtx.Config
			config.SetRoot(clientCtx.HomeDir)

			coins, err := sdk.ParseCoinsNormalized(args[1])
			if err != nil {
				return fmt.Errorf("failed to parse coins: %w", err)
			}

			addr, err := sdk.AccAddressFromBech32(args[0])
			if err != nil {
				// Try as a key name.
				backend, _ := cmd.Flags().GetString(flags.FlagKeyringBackend)
				if backend == "" {
					backend = flags.DefaultKeyringBackend
				}
				keyring, kerr := client.NewKeyringFromBackend(clientCtx, backend)
				if kerr != nil {
					return fmt.Errorf("failed to open keyring: %w", kerr)
				}
				info, kerr := keyring.Key(args[0])
				if kerr != nil {
					return fmt.Errorf("failed to get key %q: %w", args[0], kerr)
				}
				addr, err = info.GetAddress()
				if err != nil {
					return err
				}
			}

			genFile := config.GenesisFile()
			appState, genDoc, err := genutiltypes.GenesisStateFromGenFile(genFile)
			if err != nil {
				return fmt.Errorf("failed to unmarshal genesis state: %w", err)
			}

			authGenState := authtypes.GetGenesisStateFromAppState(cdc, appState)
			bankGenState := banktypes.GetGenesisStateFromAppState(cdc, appState)

			// Check for duplicate.
			accts, err := authtypes.UnpackAccounts(authGenState.Accounts)
			if err != nil {
				return fmt.Errorf("failed to unpack accounts: %w", err)
			}
			for _, a := range accts {
				if a.GetAddress().Equals(addr) {
					return fmt.Errorf("cannot add account at existing address %s", addr)
				}
			}

			// Create base account.
			baseAccount := authtypes.NewBaseAccountWithAddress(addr)
			if err := baseAccount.SetAccountNumber(uint64(len(accts))); err != nil {
				return err
			}

			// Optionally wrap in a vesting account.
			vestingAmt, _ := cmd.Flags().GetString("vesting-amount")
			vestingStart, _ := cmd.Flags().GetInt64("vesting-start-time")
			vestingEnd, _ := cmd.Flags().GetInt64("vesting-end-time")

			var newAccount authtypes.GenesisAccount
			if vestingAmt == "" {
				newAccount = baseAccount
			} else {
				vCoins, verr := sdk.ParseCoinsNormalized(vestingAmt)
				if verr != nil {
					return fmt.Errorf("failed to parse vesting amount: %w", verr)
				}
				if vestingEnd != 0 {
					newAccount = authvesting.NewContinuousVestingAccountRaw(
						authvesting.NewBaseVestingAccount(baseAccount, vCoins, vestingEnd),
						vestingStart,
					)
				} else {
					newAccount = baseAccount
				}
			}

			accts = append(accts, newAccount)
			authGenState.Accounts, err = authtypes.PackAccounts(accts)
			if err != nil {
				return fmt.Errorf("failed to pack accounts: %w", err)
			}

			bankGenState.Balances = append(bankGenState.Balances, banktypes.Balance{
				Address: addr.String(),
				Coins:   coins.Sort(),
			})
			bankGenState.Supply = bankGenState.Supply.Add(coins...)

			authGenStateBz, err := cdc.MarshalJSON(&authGenState)
			if err != nil {
				return fmt.Errorf("failed to marshal auth genesis state: %w", err)
			}
			bankGenStateBz, err := cdc.MarshalJSON(bankGenState)
			if err != nil {
				return fmt.Errorf("failed to marshal bank genesis state: %w", err)
			}

			appState[authtypes.ModuleName] = authGenStateBz
			appState[banktypes.ModuleName] = bankGenStateBz

			appStateJSON, err := json.Marshal(appState)
			if err != nil {
				return fmt.Errorf("failed to marshal application genesis state: %w", err)
			}
			genDoc.AppState = appStateJSON

			return genutil.ExportGenesisFile(genDoc, genFile)
		},
	}

	cmd.Flags().String(flags.FlagHome, defaultNodeHome, "The application home directory")
	cmd.Flags().String("vesting-amount", "", "Amount of coins for vesting accounts")
	cmd.Flags().Int64("vesting-start-time", 0, "Unix timestamp of vesting start time")
	cmd.Flags().Int64("vesting-end-time", 0, "Unix timestamp of vesting end time")

	return cmd
}

// helperCodecFromCtx extracts the codec from a client context.
func helperCodecFromCtx(cdc codec.Codec) codec.Codec { return cdc }
