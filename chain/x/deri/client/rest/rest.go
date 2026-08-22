package rest

import (
	"net/http"

	"github.com/gorilla/mux"

	"github.com/cosmos/cosmos-sdk/client"
	"github.com/cosmos/cosmos-sdk/types/rest"

	"github.com/Decentralized-Rights-Protocol/drp/x/deri/types"
)

func RegisterRoutes(clientCtx client.Context, rtr *mux.Router) {
	rtr.HandleFunc("/deri/balances/{address}", queryBalanceHandler(clientCtx)).Methods("GET")
	rtr.HandleFunc("/deri/supply", querySupplyHandler(clientCtx)).Methods("GET")
}

func queryBalanceHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		address := vars["address"]
		clientCtx := clientCtx.WithInterfaceRegistry(types.InterfaceRegistry())
		queryClient := types.NewQueryClient(clientCtx)
		resp, err := queryClient.Balance(context.Background(), &types.QueryBalanceRequest{Address: address})
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}
		rest.PostProcessResponse(w, clientCtx, resp)
	}
}

func querySupplyHandler(clientCtx client.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		clientCtx := clientCtx.WithInterfaceRegistry(types.InterfaceRegistry())
		queryClient := types.NewQueryClient(clientCtx)
		resp, err := queryClient.Supply(context.Background(), &types.QuerySupplyRequest{})
		if err != nil {
			rest.WriteErrorResponse(w, http.StatusInternalServerError, err.Error())
			return
		}
		rest.PostProcessResponse(w, clientCtx, resp)
	}
}