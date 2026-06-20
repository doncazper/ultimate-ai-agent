package main

import "regexp"

var bearerPattern = regexp.MustCompile(`(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}`)
var assignmentPattern = regexp.MustCompile(`(?i)\b(api[_-]?key|token|password|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{12,}`)

func redactSecrets(value string) string {
	redacted := bearerPattern.ReplaceAllString(value, "Bearer [REDACTED_SECRET]")
	return assignmentPattern.ReplaceAllString(redacted, "$1=[REDACTED_SECRET]")
}

func boundedPreview(value string, limit int) string {
	if limit <= 0 || limit > 2000 {
		limit = 2000
	}
	redacted := redactSecrets(value)
	if len(redacted) <= limit {
		return redacted
	}
	return redacted[:limit]
}
