package types

type GenesisState struct {
	Params  Params         `json:"params"`
	Records []StatusRecord `json:"records"`
}

type Params struct {
	// AllowedIssuers: if non-empty, only these addresses may issue status records.
	// Empty means governance address is the sole issuer by default.
	AllowedIssuers []string `json:"allowed_issuers"`
}

func DefaultParams() Params  { return Params{AllowedIssuers: []string{}} }
func DefaultGenesis() *GenesisState {
	return &GenesisState{Params: DefaultParams(), Records: []StatusRecord{}}
}

func (gs GenesisState) Validate() error {
	seen := make(map[string]bool)
	for _, r := range gs.Records {
		if seen[r.ID] {
			return ErrDuplicateRecordID
		}
		seen[r.ID] = true
	}
	return nil
}
