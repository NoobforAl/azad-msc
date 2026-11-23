package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"example.com/registration/internal/catalog"
)

func TestHealthz(t *testing.T) {
	srv := httptest.NewServer(newMux(catalog.New()))
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/healthz")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want 200", resp.StatusCode)
	}
}

func TestCoursesReturnsSeededList(t *testing.T) {
	cat := catalog.New(catalog.Course{ID: "SE1", Title: "Processes", Capacity: 25})
	srv := httptest.NewServer(newMux(cat))
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/courses")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	var got []catalog.Course
	if err := json.NewDecoder(resp.Body).Decode(&got); err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].ID != "SE1" {
		t.Fatalf("courses = %+v, want one course SE1", got)
	}
}
