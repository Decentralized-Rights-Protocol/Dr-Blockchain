package rest

import (
	"errors"
	"strconv"
	"testing"
)

func TestStrToInt64(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  int64
		err   error
	}{
		{name: "zero", input: "0", want: 0},
		{name: "decimal", input: "42", want: 42},
		{name: "negative", input: "-42", want: -42},
		{name: "explicit positive", input: "+42", want: 42},
		{name: "leading zero", input: "010", want: 10},
		{name: "maximum", input: "9223372036854775807", want: 9223372036854775807},
		{name: "minimum", input: "-9223372036854775808", want: -9223372036854775808},
		{name: "empty", input: "", err: strconv.ErrSyntax},
		{name: "malformed", input: "12x", err: strconv.ErrSyntax},
		{name: "hexadecimal", input: "0x10", err: strconv.ErrSyntax},
		{name: "whitespace", input: " 42", err: strconv.ErrSyntax},
		{name: "positive overflow", input: "9223372036854775808", err: strconv.ErrRange},
		{name: "negative overflow", input: "-9223372036854775809", err: strconv.ErrRange},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := strToInt64(tt.input)
			if tt.err != nil {
				if !errors.Is(err, tt.err) {
					t.Fatalf("strToInt64(%q) error = %v, want %v", tt.input, err, tt.err)
				}
				return
			}
			if err != nil {
				t.Fatalf("strToInt64(%q) unexpected error: %v", tt.input, err)
			}
			if got != tt.want {
				t.Fatalf("strToInt64(%q) = %d, want %d", tt.input, got, tt.want)
			}
		})
	}
}
