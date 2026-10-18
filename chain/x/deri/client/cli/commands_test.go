package cli

import "testing"

func TestCommandDeclarations(t *testing.T) {
	query := GetQueryCmd()
	if len(query.Commands()) != 3 {
		t.Fatalf("unexpected query commands: %v", query.Commands())
	}
	for _, name := range []string{"balance", "total-supply", "supply", "params"} {
		cmd, _, err := query.Find([]string{name})
		if err != nil || cmd == query {
			t.Fatalf("query %s not registered: %v", name, err)
		}
		if cmd.RunE == nil || cmd.Args == nil {
			t.Fatalf("query %s lacks handler or argument validation", name)
		}
	}
	for _, cmd := range GetTxCmd().Commands() {
		if cmd.RunE == nil || cmd.Args == nil {
			t.Fatalf("transaction %s lacks handler or argument validation", cmd.Name())
		}
		if err := cmd.Args(cmd, nil); err == nil {
			t.Fatalf("transaction %s accepted missing arguments", cmd.Name())
		}
	}
	supply := NewQuerySupplyCmd()
	if supply.Name() != "total-supply" {
		t.Fatal("legacy constructor does not target total-supply")
	}
}
