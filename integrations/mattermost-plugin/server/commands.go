package main

import (
	"fmt"
	"strings"
)

type slashAction struct {
	Name string
	Args []string
}

func parseSlashCommand(text string) slashAction {
	fields := strings.Fields(strings.TrimSpace(text))
	if len(fields) == 0 {
		return slashAction{Name: "help"}
	}
	if fields[0] == "/uaa" {
		fields = fields[1:]
	}
	if len(fields) == 0 {
		return slashAction{Name: "help"}
	}
	if fields[0] == "role" && len(fields) > 1 {
		return slashAction{Name: "role " + fields[1], Args: fields[2:]}
	}
	return slashAction{Name: fields[0], Args: fields[1:]}
}

func renderSlashResponse(action slashAction) string {
	switch action.Name {
	case "status":
		return "UAA Mattermost bridge status requested."
	case "roles":
		return "UAA role catalog requested."
	case "role add":
		if len(action.Args) == 0 {
			return "Usage: /uaa role add <role-id>"
		}
		return fmt.Sprintf("UAA role binding requested for `%s`.", action.Args[0])
	case "role suggest":
		if len(action.Args) == 0 {
			return "Usage: /uaa role suggest <description>"
		}
		return "UAA role suggestion requested."
	case "trigger":
		if len(action.Args) == 0 {
			return "Usage: /uaa trigger mention_command|enabled_room|always_on_by_role"
		}
		return fmt.Sprintf("UAA trigger mode change requested: `%s`.", action.Args[0])
	case "disable":
		return "UAA agent room participation disable requested."
	default:
		return "UAA commands: status, roles, role add, role suggest, trigger, disable."
	}
}
