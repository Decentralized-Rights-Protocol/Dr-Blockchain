package app

import (
	"encoding/json"
	"testing"
	"time"

	dbm "github.com/cometbft/cometbft-db"
	abci "github.com/cometbft/cometbft/abci/types"
	"github.com/cometbft/cometbft/libs/log"
	cmtproto "github.com/cometbft/cometbft/proto/tendermint/types"
	cmttypes "github.com/cometbft/cometbft/types"
	"github.com/cosmos/cosmos-sdk/baseapp"
	"github.com/cosmos/cosmos-sdk/crypto/keys/ed25519"
	sdk "github.com/cosmos/cosmos-sdk/types"
	authtypes "github.com/cosmos/cosmos-sdk/x/auth/types"
	banktypes "github.com/cosmos/cosmos-sdk/x/bank/types"
	stakingtypes "github.com/cosmos/cosmos-sdk/x/staking/types"
)

func TestBaselineGenesisAndUnsignedTx(t *testing.T) {
	app := NewDRPApp(log.NewNopLogger(), dbm.NewMemDB(), nil, true, nil, baseapp.SetChainID("baseline-test"))
	enc := MakeEncodingConfig()
	if len(app.mm.Modules) != len(ModuleBasics) {
		t.Fatal("basic and runtime module sets differ")
	}
	for name := range ModuleBasics {
		if _, ok := app.mm.Modules[name]; !ok {
			t.Fatalf("missing runtime module %s", name)
		}
	}
	genesis := app.DefaultGenesis()
	address := sdk.AccAddress(ed25519.GenPrivKey().PubKey().Address())
	tokens := sdk.DefaultPowerReduction
	validator, err := stakingtypes.NewValidator(sdk.ValAddress(address), ed25519.GenPrivKey().PubKey(), stakingtypes.Description{Moniker: "baseline"})
	if err != nil {
		t.Fatal(err)
	}
	validator.Tokens = tokens
	validator.DelegatorShares = sdk.NewDecFromInt(tokens)
	stakingGenesis := stakingtypes.DefaultGenesisState()
	stakingGenesis.Validators = []stakingtypes.Validator{validator}
	stakingGenesis.Delegations = []stakingtypes.Delegation{stakingtypes.NewDelegation(address, sdk.ValAddress(address), validator.DelegatorShares)}
	genesis[stakingtypes.ModuleName] = enc.Marshaler.MustMarshalJSON(stakingGenesis)
	bankGenesis := banktypes.DefaultGenesisState()
	coins := sdk.NewCoins(sdk.NewCoin(stakingGenesis.Params.BondDenom, tokens))
	bankGenesis.Balances = []banktypes.Balance{{Address: authtypes.NewModuleAddress(stakingtypes.NotBondedPoolName).String(), Coins: coins}}
	bankGenesis.Supply = coins
	genesis[banktypes.ModuleName] = enc.Marshaler.MustMarshalJSON(bankGenesis)
	if err := ModuleBasics.ValidateGenesis(enc.Marshaler, enc.TxConfig, genesis); err != nil {
		t.Fatal(err)
	}
	state, err := json.Marshal(genesis)
	if err != nil {
		t.Fatal(err)
	}
	params := cmttypes.DefaultConsensusParams().ToProto()
	response := app.InitChain(abci.RequestInitChain{ChainId: "baseline-test", InitialHeight: 1, Time: time.Unix(1, 0).UTC(), ConsensusParams: &params, AppStateBytes: state})
	if len(response.Validators) != 1 {
		t.Fatalf("expected one validator, got %d", len(response.Validators))
	}
	ctx := app.NewContext(false, cmtproto.Header{})
	stored := app.GetConsensusParams(ctx)
	if stored == nil || stored.Block.MaxBytes != params.Block.MaxBytes {
		t.Fatal("consensus parameters were not persisted")
	}
	if app.UpgradeKeeper.GetModuleVersionMap(ctx)[stakingtypes.ModuleName] == 0 {
		t.Fatal("module versions not initialized")
	}

	app.BeginBlock(abci.RequestBeginBlock{Header: cmtproto.Header{ChainID: "baseline-test", Height: 1, Time: time.Unix(2, 0).UTC()}})
	app.EndBlock(abci.RequestEndBlock{Height: 1})
	app.Commit()

	// A well-formed message must not pass CheckTx without signer credentials.
	// Without an ante-handler, CheckTx accepts this transaction without executing messages.
	tx := enc.TxConfig.NewTxBuilder()
	recipient := sdk.AccAddress(ed25519.GenPrivKey().PubKey().Address())
	if err := tx.SetMsgs(banktypes.NewMsgSend(address, recipient, sdk.NewCoins(sdk.NewInt64Coin(stakingGenesis.Params.BondDenom, 1)))); err != nil {
		t.Fatal(err)
	}
	tx.SetGasLimit(200000)
	encoded, err := enc.TxConfig.TxEncoder()(tx.GetTx())
	if err != nil {
		t.Fatal(err)
	}
	if result := app.CheckTx(abci.RequestCheckTx{Tx: encoded}); result.Code == 0 {
		t.Fatal("unsigned transaction accepted")
	}
}

func TestUnsupportedZeroHeightExport(t *testing.T) {
	app := NewDRPApp(log.NewNopLogger(), dbm.NewMemDB(), nil, true, nil)
	if _, err := app.ExportAppStateAndValidators(true, nil, nil); err == nil {
		t.Fatal("incomplete zero-height export must fail explicitly")
	}
}
