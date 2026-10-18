package types

import (
	"fmt"

	sdk "github.com/cosmos/cosmos-sdk/types"
	paramtypes "github.com/cosmos/cosmos-sdk/x/params/types"
)

// Constants for the deri module
const (
	ModuleName = "deri"

	// Denomination for $DeRi token
	DeRiDenom = "uderi"

	// Emission limits
	MaxPerBlock    = int64(1000000)   // 1M uderi per block
	MaxPerEpoch    = int64(100000000) // 100M uderi per epoch
	MaxPerActivity = int64(10000)     // 10K uderi per activity
	MaxPerIdentity = int64(1000000)   // 1M uderi per identity
)

// NewParams creates a new Params instance with default values
func NewParams() Params {
	return Params{
		MaxPerBlock:    MaxPerBlock,
		MaxPerEpoch:    MaxPerEpoch,
		MaxPerActivity: MaxPerActivity,
		MaxPerIdentity: MaxPerIdentity,
		Denom:          DeRiDenom,
	}
}

// DefaultParams returns the default parameters
func DefaultParams() Params {
	return NewParams()
}

// Validate checks if the parameters are valid
func (p Params) Validate() error {
	if p.MaxPerBlock <= 0 {
		return fmt.Errorf("max_per_block must be positive: %d", p.MaxPerBlock)
	}
	if p.MaxPerEpoch <= 0 {
		return fmt.Errorf("max_per_epoch must be positive: %d", p.MaxPerEpoch)
	}
	if p.MaxPerActivity <= 0 {
		return fmt.Errorf("max_per_activity must be positive: %d", p.MaxPerActivity)
	}
	if p.MaxPerIdentity <= 0 {
		return fmt.Errorf("max_per_identity must be positive: %d", p.MaxPerIdentity)
	}
	return validateDenom(p.Denom)
}

// ParamSetPairs supplies independently validated fields to the SDK params keeper.
func (p *Params) ParamSetPairs() paramtypes.ParamSetPairs {
	return paramtypes.ParamSetPairs{
		paramtypes.NewParamSetPair([]byte("MaxPerBlock"), &p.MaxPerBlock, validateMaxPerBlock),
		paramtypes.NewParamSetPair([]byte("MaxPerEpoch"), &p.MaxPerEpoch, validateMaxPerEpoch),
		paramtypes.NewParamSetPair([]byte("MaxPerActivity"), &p.MaxPerActivity, validateMaxPerActivity),
		paramtypes.NewParamSetPair([]byte("MaxPerIdentity"), &p.MaxPerIdentity, validateMaxPerIdentity),
		paramtypes.NewParamSetPair([]byte("Denom"), &p.Denom, validateDenom),
	}
}

func validatePositiveLimit(v interface{}) error {
	n, ok := v.(int64)
	if !ok || n <= 0 {
		return fmt.Errorf("limit must be a positive int64: %v", v)
	}
	return nil
}

func validateMaxPerBlock(v interface{}) error    { return validatePositiveLimit(v) }
func validateMaxPerEpoch(v interface{}) error    { return validatePositiveLimit(v) }
func validateMaxPerActivity(v interface{}) error { return validatePositiveLimit(v) }
func validateMaxPerIdentity(v interface{}) error { return validatePositiveLimit(v) }

func validateDenom(v interface{}) error {
	denom, ok := v.(string)
	if !ok {
		return fmt.Errorf("denom must be a string: %T", v)
	}
	return sdk.ValidateDenom(denom)
}

// RewardCalculation defines the structure for reward calculations
type RewardCalculation struct {
	BaseReward       int64 `json:"base_reward" yaml:"base_reward"`
	ActivityScore    int64 `json:"activity_score" yaml:"activity_score"`
	VerificationConf int64 `json:"verification_confidence" yaml:"verification_confidence"`
	ReputationMult   int64 `json:"reputation_multiplier" yaml:"reputation_multiplier"`
	NetworkFactor    int64 `json:"network_factor" yaml:"network_factor"`
	FinalReward      int64 `json:"final_reward" yaml:"final_reward"`
}

// CalculateReward computes the reward using integer arithmetic
// Formula: BaseReward * ActivityScore * VerificationConfidence * ReputationMultiplier * NetworkFactor
func CalculateReward(baseReward, activityScore, verificationConf, reputationMult, networkFactor int64) int64 {
	// Use integer arithmetic to avoid floating-point nondeterminism
	// Scale factors to maintain precision: multiply by 10^12 for 6 decimal places
	const scale = int64(1000000000000)

	// Scale each component
	scaledBase := baseReward * scale
	scaledActivity := activityScore
	scaledVerif := verificationConf
	scaledReputation := reputationMult
	scaledNetwork := networkFactor

	// Multiply all components
	result := scaledBase
	result = result * scaledActivity / scale
	result = result * scaledVerif / scale
	result = result * scaledReputation / scale
	result = result * scaledNetwork / scale

	return result
}

// ValidateReward checks if a reward amount is valid
func ValidateReward(amount int64) error {
	if amount < 0 {
		return fmt.Errorf("reward amount cannot be negative: %d", amount)
	}
	return nil
}

// DeRiCoin defines a wrapper around sdk.Coin for $DeRi tokens
type DeRiCoin struct {
	sdk.Coin
}

// NewDeRiCoin creates a new DeRiCoin
func NewDeRiCoin(amount int64) DeRiCoin {
	return DeRiCoin{
		Coin: sdk.Coin{
			Denom:  DeRiDenom,
			Amount: sdk.NewInt(amount),
		},
	}
}

// DeRiCoins defines a wrapper around sdk.Coins for $DeRi tokens
type DeRiCoins []DeRiCoin

// NewDeRiCoins creates new DeRiCoins from a coin slice
func NewDeRiCoins(coins sdk.Coins) DeRiCoins {
	deriCoins := make(DeRiCoins, 0, len(coins))
	for _, coin := range coins {
		if coin.Denom == DeRiDenom {
			deriCoins = append(deriCoins, DeRiCoin{coin})
		}
	}
	return deriCoins
}

// TotalAmount returns the total amount of $DeRi in the coin slice
func (coins DeRiCoins) TotalAmount() int64 {
	total := int64(0)
	for _, coin := range coins {
		total += coin.Amount.Int64()
	}
	return total
}

// ParamKeyTable returns the parameter key table for the deri module
func ParamKeyTable() paramtypes.KeyTable {
	return paramtypes.NewKeyTable().
		RegisterParamSet(&Params{})
}
