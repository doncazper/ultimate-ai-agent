package main

import (
	"strings"
	"time"
)

type configuration struct {
	UAABaseURL              string
	UAABridgeBearer        string
	WorkspaceRef           string
	AllowedChannelIDs      string
	ReplyEnabled           bool
	TriggerMode            string
	RoleCreationMode       string
	MaxPreviewChars        int
	TimeoutMillis          int
	PlannerBotUserID       string
	SummarizerBotUserID    string
	CriticBotUserID        string
	ImplementerBotUserID   string
	SafetyReviewerBotUserID string
	FacilitatorBotUserID   string
	RoleBotUserIDs         map[string]string
}

func (c *configuration) sanitize() configuration {
	copy := *c
	copy.UAABridgeBearer = ""
	return copy
}

func (c *configuration) normalized() configuration {
	out := *c
	if out.UAABaseURL == "" {
		out.UAABaseURL = "http://127.0.0.1:8000"
	}
	if out.WorkspaceRef == "" {
		out.WorkspaceRef = "mattermost-workspace:local"
	}
	if out.TriggerMode == "" {
		out.TriggerMode = "mention_command"
	}
	if out.RoleCreationMode == "" {
		out.RoleCreationMode = "proposal_then_approve"
	}
	if out.MaxPreviewChars <= 0 || out.MaxPreviewChars > 2000 {
		out.MaxPreviewChars = 2000
	}
	if out.TimeoutMillis <= 0 || out.TimeoutMillis > 30000 {
		out.TimeoutMillis = 5000
	}
	if out.RoleBotUserIDs == nil {
		out.RoleBotUserIDs = map[string]string{}
	}
	setRoleBotUserID(out.RoleBotUserIDs, "planner", out.PlannerBotUserID)
	setRoleBotUserID(out.RoleBotUserIDs, "summarizer", out.SummarizerBotUserID)
	setRoleBotUserID(out.RoleBotUserIDs, "critic", out.CriticBotUserID)
	setRoleBotUserID(out.RoleBotUserIDs, "implementer", out.ImplementerBotUserID)
	setRoleBotUserID(out.RoleBotUserIDs, "safety-reviewer", out.SafetyReviewerBotUserID)
	setRoleBotUserID(out.RoleBotUserIDs, "facilitator", out.FacilitatorBotUserID)
	return out
}

func (c *configuration) timeout() time.Duration {
	normalized := c.normalized()
	return time.Duration(normalized.TimeoutMillis) * time.Millisecond
}

func (c *configuration) channelAllowed(channelID string) bool {
	normalized := c.normalized()
	if normalized.AllowedChannelIDs == "" {
		return false
	}
	for _, item := range splitCSV(normalized.AllowedChannelIDs) {
		if item == channelID {
			return true
		}
	}
	return false
}

func (c *configuration) isConfiguredRoleBot(userID string) bool {
	normalized := c.normalized()
	for _, botUserID := range normalized.RoleBotUserIDs {
		if botUserID == userID {
			return true
		}
	}
	return false
}

func splitCSV(value string) []string {
	parts := []string{}
	for _, item := range strings.Split(value, ",") {
		trimmed := strings.TrimSpace(item)
		if trimmed != "" {
			parts = append(parts, trimmed)
		}
	}
	return parts
}

func setRoleBotUserID(values map[string]string, roleID string, userID string) {
	trimmed := strings.TrimSpace(userID)
	if trimmed != "" {
		values[roleID] = trimmed
	}
}
