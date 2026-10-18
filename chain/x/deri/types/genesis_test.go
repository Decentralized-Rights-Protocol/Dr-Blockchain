package types

import (
	sdk "github.com/cosmos/cosmos-sdk/types"
	"testing"
)

func TestGenesisValidation(t *testing.T) {
	address := sdk.AccAddress([]byte("12345678901234567890")).String()
	tests := []struct {
		name     string
		balances []BalanceGenesis
		supply   string
		valid    bool
	}{
		{"empty", nil, "0", true},
		{"balanced", []BalanceGenesis{{Address: address, Amount: "12"}}, "12", true},
		{"negative balance", []BalanceGenesis{{Address: address, Amount: "-1"}}, "0", false},
		{"negative supply", nil, "-1", false},
		{"invalid address", []BalanceGenesis{{Address: "invalid", Amount: "0"}}, "0", false},
		{"duplicate", []BalanceGenesis{{Address: address, Amount: "1"}, {Address: address, Amount: "2"}}, "3", false},
		{"mismatch", []BalanceGenesis{{Address: address, Amount: "1"}}, "2", false},
		{"invalid amount", []BalanceGenesis{{Address: address, Amount: "one"}}, "0", false},
		{"invalid supply", nil, "", false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			state := NewGenesisState(DefaultParams(), tt.balances, tt.supply)
			if err := state.Validate(); (err == nil) != tt.valid {
				t.Fatalf("Validate() = %v, want valid %v", err, tt.valid)
			}
		})
	}
	if err := DefaultGenesisState().Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestParameterFieldValidators(t *testing.T) {
	params := DefaultParams()
	pairs := params.ParamSetPairs()
	if len(pairs) != 5 {
		t.Fatalf("got %d parameter pairs", len(pairs))
	}
	seen := map[string]bool{}
	for i, pair := range pairs {
		if seen[string(pair.Key)] {
			t.Fatalf("duplicate parameter key %q", pair.Key)
		}
		seen[string(pair.Key)] = true
		if i < 4 {
			for _, invalid := range []interface{}{int64(0), int64(-1), "1", uint64(1)} {
				if err := pair.ValidatorFn(invalid); err == nil {
					t.Fatalf("%s accepted %v (%T)", pair.Key, invalid, invalid)
				}
			}
			if err := pair.ValidatorFn(int64(1)); err != nil {
				t.Fatal(err)
			}
		} else {
			for _, invalid := range []interface{}{"", "a", "bad denom", int64(1)} {
				if err := pair.ValidatorFn(invalid); err == nil {
					t.Fatalf("denom accepted %v", invalid)
				}
			}
			if err := pair.ValidatorFn(DeRiDenom); err != nil {
				t.Fatal(err)
			}
		}
	}
	// Constructing the key table used to fail because Params lacked ParamSetPairs.
	ParamKeyTable()
	params.Denom = "bad denom"
	if err := params.Validate(); err == nil {
		t.Fatal("invalid denomination accepted")
	}
}
