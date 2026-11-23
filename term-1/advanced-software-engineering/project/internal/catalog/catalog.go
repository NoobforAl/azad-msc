// Package catalog holds the course catalog of the Course Registration Platform.
package catalog

import "sort"

// Course is one offering students can register for.
type Course struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	Capacity int    `json:"capacity"`
}

// Catalog is an in-memory course store. Later modules replace it with PostgreSQL.
type Catalog struct {
	courses map[string]Course
}

// New returns a catalog seeded with the given courses.
func New(seed ...Course) *Catalog {
	c := &Catalog{courses: make(map[string]Course, len(seed))}
	for _, course := range seed {
		c.courses[course.ID] = course
	}
	return c
}

// List returns all courses ordered by ID.
func (c *Catalog) List() []Course {
	out := make([]Course, 0, len(c.courses))
	for _, course := range c.courses {
		out = append(out, course)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out
}

// Get returns one course and whether it exists.
func (c *Catalog) Get(id string) (Course, bool) {
	course, ok := c.courses[id]
	return course, ok
}
