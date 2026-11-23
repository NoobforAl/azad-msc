// Command registration-api serves the Course Registration Platform HTTP API.
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"example.com/registration/internal/catalog"
)

// newMux wires the HTTP routes. It is a function so tests can call it without a network.
func newMux(c *catalog.Catalog) *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("GET /courses", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, c.List())
	})
	return mux
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("encode response: %v", err)
	}
}

func main() {
	addr := os.Getenv("ADDR")
	if addr == "" {
		addr = ":8080"
	}
	cat := catalog.New(
		catalog.Course{ID: "SE101", Title: "Software Processes", Capacity: 40},
		catalog.Course{ID: "SE102", Title: "Requirements Engineering", Capacity: 35},
	)
	srv := &http.Server{
		Addr:              addr,
		Handler:           newMux(cat),
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("registration-api listening on %s", addr)
	log.Fatal(srv.ListenAndServe())
}
