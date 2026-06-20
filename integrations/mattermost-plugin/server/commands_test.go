package main

import "testing"

func TestParseSlashCommand(t *testing.T) {
	action := parseSlashCommand(`/uaa role add planner`)
	if action.Name != "role add" {
		t.Fatalf("expected role add action, got %q", action.Name)
	}
	if len(action.Args) != 1 || action.Args[0] != "planner" {
		t.Fatalf("unexpected args: %#v", action.Args)
	}
}

func TestRedactAndBoundPreview(t *testing.T) {
	preview := boundedPreview("Authorization: Bearer abcdefghijklmnop and hello", 24)
	if preview == "Authorization: Bearer abcdefghijklmnop and hello" {
		t.Fatal("expected redaction")
	}
	if len(preview) > 24 {
		t.Fatalf("preview exceeded bound: %d", len(preview))
	}
}

func TestBuildMessageEvent(t *testing.T) {
	cfg := configuration{WorkspaceRef: "mattermost-workspace:local", MaxPreviewChars: 2000}
	event := buildMessageEvent(cfg, "post1", "root1", "channel1", "user1", "@uaa-planner hello", []string{"planner"}, false)
	if event.EventRef != "mattermost-event:post1" {
		t.Fatalf("unexpected event ref: %s", event.EventRef)
	}
	if event.MessageSHA256 == "" {
		t.Fatal("expected hash")
	}
	if !event.IsDirectMention {
		t.Fatal("expected direct mention")
	}
}
