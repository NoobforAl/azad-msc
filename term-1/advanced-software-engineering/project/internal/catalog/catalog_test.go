package catalog

import "testing"

func TestListIsSortedByID(t *testing.T) {
	c := New(Course{ID: "SE2", Title: "Requirements", Capacity: 30}, Course{ID: "SE1", Title: "Processes", Capacity: 25})
	got := c.List()
	if len(got) != 2 || got[0].ID != "SE1" || got[1].ID != "SE2" {
		t.Fatalf("List() = %+v, want SE1 then SE2", got)
	}
}

func TestGet(t *testing.T) {
	c := New(Course{ID: "SE1", Title: "Processes", Capacity: 25})
	if _, ok := c.Get("SE1"); !ok {
		t.Fatal("Get(SE1) not found")
	}
	if _, ok := c.Get("nope"); ok {
		t.Fatal("Get(nope) found a course that does not exist")
	}
}
