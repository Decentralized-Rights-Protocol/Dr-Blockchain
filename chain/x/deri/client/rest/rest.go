package rest

import (
	"fmt"
	"net/http"
	"strconv"

	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/types/rest"
	"github.com/gorilla/mux"

	"github.com/Decentralized-Rights-Protocol/Dr-Blockchain/chain/x/deri/types"
)

// RegisterRoutes registers the REST routes for the deri module
func RegisterRoutes(clientCtx client.Context, rtr *mux.Router) {
	// Register transaction routes
	rtr.HandleFunc("/deri/transfer", newTransferHandler(clientCtx)).Methods("POST")
	rtr.HandleFunc("/deri/mint", newMintHandler(clientCtx)).Methods("POST")
	rtr.HandleFunc("/deri/burn", newBurnHandler(clientCtx)).Methods("POST")

	// Register query routes
	rtr.HandleFunc("/deri/balances/{address}", newBalanceHandler(clientCtx)).Methods("GET")
	rtr.HandleFunc("/deri/total-supply", newTotalSupplyHandler(clientCtx)).Methods("GET")
	rtr.HandleFunc("/deri/params", newParamsHandler(clientCtx)).Methods("GET")
}

// transferRequest defines the request body for transfer
// This is a placeholder for the actual request structure
type transferRequest struct {
	BaseReq rest.BaseReq `json:"base_req"`
	From    string       `json:"from"`
	To      string       `json:"to"`
	Amount  string       `json:"amount"`
}

// transferResponse defines the response body for transfer
type transferResponse struct {
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

// newTransferHandler creates a new transfer handler
func newTransferHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req transferRequest
		if !rest.ReadRESTReq(w, r, clientCtx.LegacyAmino, &req) {
			rest.WriteErrorResponse(w, http.StatusBadRequest, "failed to parse request")
			return
		}

		// Validate request
		if req.From == "" || req.To == "" || req.Amount == "" {
			rest.WriteErrorResponse(w, http.StatusBadRequest, "from, to, and amount are required")
			return
		}

		// Create message
		msg := types.NewMsgTransfer(req.From, req.To, req.Amount)

		// Validate message
		if err := msg.ValidateBasic(); err != nil {
			rest.WriteErrorResponse(w, http.StatusBadRequest, err.Error())
			return
		}

		// Build and broadcast transaction
		txBytes, err := clientCtx.TxConfig.NewTxBuilder().
			WithTxConfig(clientCtx.TxConfig).
			BuildAndSign(req.BaseReq.Simulate, req.BaseReq, msg)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Broadcast transaction
		res, err := clientCtx.BroadcastTx(txBytes)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Write response
		rest.PostProcessResponse(w, clientCtx, res)
	}
}

// mintRequest defines the request body for mint
// This is a placeholder for the actual request structure
type mintRequest struct {
	BaseReq rest.BaseReq `json:"base_req"`
	To      string       `json:"to"`
	Amount  string       `json:"amount"`
	Reason  string       `json:"reason"`
	Signer  string       `json:"signer"`
}

// mintResponse defines the response body for mint
type mintResponse struct {
	Success      bool   `json:"success"`
	Error        string `json:"error,omitempty"`
	MintedAmount string `json:"minted_amount,omitempty"`
}

// newMintHandler creates a new mint handler
func newMintHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req mintRequest
		if !rest.ReadRESTReq(w, r, clientCtx.LegacyAmino, &req) {
			rest.WriteErrorResponse(w, http.StatusBadRequest, "failed to parse request")
			return
		}

		// Validate request
		if req.To == "" || req.Amount == "" || req.Reason == "" || req.Signer == "" {
			rest.WriteErrorResponse(w, http.StatusBadRequest, "to, amount, reason, and signer are required")
			return
		}

		// Create message
		msg := types.NewMsgMint(req.To, req.Amount, req.Reason, req.Signer)

		// Validate message
		if err := msg.ValidateBasic(); err != nil {
			rest.WriteErrorResponse(w, http.StatusBadRequest, err.Error())
			return
		}

		// Build and broadcast transaction
		txBytes, err := clientCtx.TxConfig.NewTxBuilder().
			WithTxConfig(clientCtx.TxConfig).
			BuildAndSign(req.BaseReq.Simulate, req.BaseReq, msg)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Broadcast transaction
		res, err := clientCtx.BroadcastTx(txBytes)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Write response
		rest.PostProcessResponse(w, clientCtx, res)
	}
}

// burnRequest defines the request body for burn
// This is a placeholder for the actual request structure
type burnRequest struct {
	BaseReq rest.BaseReq `json:"base_req"`
	From    string       `json:"from"`
	Amount  string       `json:"amount"`
	Reason  string       `json:"reason"`
}

// burnResponse defines the response body for burn
type burnResponse struct {
	Success     bool   `json:"success"`
	Error       string `json:"error,omitempty"`
	BurnedAmount string `json:"burned_amount,omitempty"`
}

// newBurnHandler creates a new burn handler
func newBurnHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req burnRequest
		if !rest.ReadRESTReq(w, r, clientCtx.LegacyAmino, &req) {
			rest.WriteErrorResponse(w, http.StatusBadRequest, "failed to parse request")
			return
		}

		// Validate request
		if req.From == "" || req.Amount == "" || req.Reason == "" {
			rest.WriteErrorResponse(w, http.StatusBadRequest, "from, amount, and reason are required")
			return
		}

		// Create message
		msg := types.NewMsgBurn(req.From, req.Amount, req.Reason)

		// Validate message
		if err := msg.ValidateBasic(); err != nil {
			rest.WriteErrorResponse(w, http.StatusBadRequest, err.Error())
			return
		}

		// Build and broadcast transaction
		txBytes, err := clientCtx.TxConfig.NewTxBuilder().
			WithTxConfig(clientCtx.TxConfig).
			BuildAndSign(req.BaseReq.Simulate, req.BaseReq, msg)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Broadcast transaction
		res, err := clientCtx.BroadcastTx(txBytes)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Write response
		rest.PostProcessResponse(w, clientCtx, res)
	}
}

// newBalanceHandler creates a new balance query handler
func newBalanceHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		address := vars["address"]

		if address == "" {
			rest.WriteErrorResponse(w, http.StatusBadRequest, "address is required")
			return
		}

		// Create query request
		req := &types.QueryBalanceRequest{
			Address: address,
		}

		// Query the balance
		queryClient := types.NewQueryClient(clientCtx)
		resp, err := queryClient.Balance(r.Context(), req)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Write response
		rest.PostProcessResponse(w, clientCtx, resp)
	}
}

// newTotalSupplyHandler creates a new total supply query handler
func newTotalSupplyHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Create query request
		req := &types.QueryTotalSupplyRequest{}

		// Query the total supply
		queryClient := types.NewQueryClient(clientCtx)
		resp, err := queryClient.TotalSupply(r.Context(), req)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Write response
		rest.PostProcessResponse(w, clientCtx, resp)
	}
}

// newParamsHandler creates a new params query handler
func newParamsHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Create query request
		req := &types.QueryParamsRequest{}

		// Query the parameters
		queryClient := types.NewQueryClient(clientCtx)
		resp, err := queryClient.Params(r.Context(), req)
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}

		// Write response
		rest.PostProcessResponse(w, clientCtx, resp)
	}
}

// ParseHTTPArgs is a helper to parse HTTP arguments
func ParseHTTPArgs(r *http.Request) ([]string, error) {
	query := r.URL.Query()
	args := make([]string, 0)
	
	for i := 0; ; i++ {
		arg := query.Get(fmt.Sprintf("arg%d", i))
		if arg == "" {
			break
		}
		args = append(args, arg)
	}
	
	return args, nil
}

//nolint:unused
func strToInt64(s string) (int64, error) {
	return strconv.ParseInt64(s, 10, 64)
}
