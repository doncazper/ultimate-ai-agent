package main

import (
	"context"
	"net/http"
	"strings"
	"sync"
	"sync/atomic"

	"github.com/mattermost/mattermost/server/public/model"
	"github.com/mattermost/mattermost/server/public/plugin"
)

type Plugin struct {
	plugin.MattermostPlugin
	configuration atomic.Value
	seenPosts     sync.Map
}

func main() {
	plugin.ClientMain(&Plugin{})
}

func (p *Plugin) OnActivate() error {
	if err := p.loadConfiguration(); err != nil {
		return err
	}
	return p.API.RegisterCommand(&model.Command{
		Trigger:          "uaa",
		DisplayName:      "UAA Agent Rooms",
		Description:      "Manage UAA agent roles in this room.",
		AutoComplete:     true,
		AutoCompleteDesc: "status | roles | role add | role suggest | trigger | disable",
		AutoCompleteHint: "[command]",
	})
}

func (p *Plugin) OnConfigurationChange() error {
	return p.loadConfiguration()
}

func (p *Plugin) ExecuteCommand(_ *plugin.Context, args *model.CommandArgs) (*model.CommandResponse, *model.AppError) {
	action := parseSlashCommand(args.Command)
	return &model.CommandResponse{
		ResponseType: model.CommandResponseTypeEphemeral,
		Text:         renderSlashResponse(action),
	}, nil
}

func (p *Plugin) MessageHasBeenPosted(_ *plugin.Context, post *model.Post) {
	if post == nil || post.Id == "" || post.ChannelId == "" {
		return
	}
	if post.GetProp("from_bot") == true {
		return
	}
	if post.GetProp("uaa_command_ref") != nil {
		return
	}
	cfg := p.getConfiguration()
	if !cfg.ReplyEnabled || !cfg.channelAllowed(post.ChannelId) || cfg.isConfiguredRoleBot(post.UserId) {
		return
	}
	if _, loaded := p.seenPosts.LoadOrStore(post.Id, true); loaded {
		return
	}
	event := buildMessageEvent(cfg, post.Id, post.RootId, post.ChannelId, post.UserId, post.Message, mentionedRoleIDs(post.Message), false)
	ctx, cancel := context.WithTimeout(context.Background(), cfg.timeout())
	defer cancel()
	decision, err := postMessageEvent(ctx, http.DefaultClient, cfg, event)
	if err != nil {
		p.API.LogWarn("UAA Mattermost bridge request failed", "error", redactSecrets(err.Error()))
		return
	}
	for _, command := range decision.ReplyCommands {
		botUserID := cfg.RoleBotUserIDs[command.RoleID]
		if botUserID == "" {
			p.API.LogWarn("UAA role bot user is not configured", "role_id", command.RoleID)
			continue
		}
		replyPost := &model.Post{
			UserId:    botUserID,
			ChannelId: post.ChannelId,
			RootId:    post.RootId,
			Message:   command.ReplyPreview,
			Props: model.StringInterface{
				"from_bot": true,
				"uaa_role": command.RoleID,
				"uaa_command_ref": command.CommandRef,
			},
		}
		if _, appErr := p.API.CreatePost(replyPost); appErr != nil {
			p.API.LogWarn("UAA role bot post failed", "role_id", command.RoleID, "error", appErr.Error())
		}
	}
}

func (p *Plugin) loadConfiguration() error {
	cfg := &configuration{}
	if err := p.API.LoadPluginConfiguration(cfg); err != nil {
		return err
	}
	p.configuration.Store(cfg.normalized())
	return nil
}

func (p *Plugin) getConfiguration() configuration {
	cfg, ok := p.configuration.Load().(configuration)
	if !ok {
		return (&configuration{}).normalized()
	}
	return cfg.normalized()
}

func mentionedRoleIDs(message string) []string {
	lowered := strings.ToLower(message)
	roles := []string{}
	for _, roleID := range []string{"planner", "summarizer", "critic", "implementer", "safety-reviewer", "facilitator"} {
		if strings.Contains(lowered, "@uaa-"+roleID) || strings.Contains(lowered, roleID) {
			roles = append(roles, roleID)
		}
	}
	return roles
}
