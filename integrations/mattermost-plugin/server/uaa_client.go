package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

type mattermostMessageEvent struct {
	EventRef         string   `json:"event_ref"`
	WorkspaceRef     string   `json:"workspace_ref"`
	ChannelRef       string   `json:"channel_ref"`
	MessageRef       string   `json:"message_ref"`
	ThreadRef        string   `json:"thread_ref,omitempty"`
	ActorRef         string   `json:"actor_ref"`
	UserRef          string   `json:"user_ref,omitempty"`
	MessagePreview   string   `json:"message_preview"`
	MessageSHA256    string   `json:"message_sha256"`
	IdempotencyKey   string   `json:"idempotency_key"`
	MentionedRoleIDs []string `json:"mentioned_role_ids"`
	IsBotMessage     bool     `json:"is_bot_message"`
	IsDirectMention  bool     `json:"is_direct_mention"`
	Command          string   `json:"command,omitempty"`
}

type mattermostReplyCommand struct {
	CommandRef   string `json:"command_ref"`
	RoleID       string `json:"role_id"`
	BotUsername  string `json:"bot_username"`
	ChannelRef   string `json:"channel_ref"`
	ThreadRef    string `json:"thread_ref,omitempty"`
	ReplyPreview string `json:"reply_preview"`
	ReplyKind    string `json:"reply_kind"`
}

type mattermostDecisionData struct {
	DecisionRef   string                   `json:"decision_ref"`
	Status        string                   `json:"status"`
	ReasonCodes   []string                 `json:"reason_codes"`
	ReplyCommands []mattermostReplyCommand `json:"reply_commands"`
}

type uaaEnvelope struct {
	Success bool                   `json:"success"`
	Data    mattermostDecisionData `json:"data"`
}

func buildMessageEvent(cfg configuration, postID, rootID, channelID, userID, message string, mentionedRoles []string, isBot bool) mattermostMessageEvent {
	normalized := cfg.normalized()
	preview := boundedPreview(message, normalized.MaxPreviewChars)
	sum := sha256.Sum256([]byte(preview))
	threadRef := ""
	if rootID != "" {
		threadRef = "mattermost-thread:" + rootID
	}
	return mattermostMessageEvent{
		EventRef:         "mattermost-event:" + postID,
		WorkspaceRef:     normalized.WorkspaceRef,
		ChannelRef:       "mattermost-channel:" + channelID,
		MessageRef:       "mattermost-message:" + postID,
		ThreadRef:        threadRef,
		ActorRef:         "mattermost-actor:plugin",
		UserRef:          "mattermost-user:" + userID,
		MessagePreview:   preview,
		MessageSHA256:    hex.EncodeToString(sum[:]),
		IdempotencyKey:   "mattermost-idempotency:" + postID,
		MentionedRoleIDs: mentionedRoles,
		IsBotMessage:     isBot,
		IsDirectMention:  len(mentionedRoles) > 0 || strings.HasPrefix(strings.TrimSpace(message), "/uaa"),
	}
}

func postMessageEvent(ctx context.Context, client *http.Client, cfg configuration, event mattermostMessageEvent) (mattermostDecisionData, error) {
	normalized := cfg.normalized()
	payload, err := json.Marshal(event)
	if err != nil {
		return mattermostDecisionData{}, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(normalized.UAABaseURL, "/")+"/integrations/mattermost/events/message", bytes.NewReader(payload))
	if err != nil {
		return mattermostDecisionData{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	if normalized.UAABridgeBearer != "" {
		req.Header.Set("Authorization", "Bearer "+normalized.UAABridgeBearer)
	}
	resp, err := client.Do(req)
	if err != nil {
		return mattermostDecisionData{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return mattermostDecisionData{}, fmt.Errorf("uaa returned status %d", resp.StatusCode)
	}
	var envelope uaaEnvelope
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&envelope); err != nil {
		return mattermostDecisionData{}, err
	}
	if !envelope.Success {
		return mattermostDecisionData{}, fmt.Errorf("uaa bridge envelope was not successful")
	}
	return envelope.Data, nil
}
