import type { CSSProperties } from "react";
import {
  getIconDefinition,
  type IconAlias,
  type IconName,
  type IconReference,
} from "../icons/iconRegistry";

export const ICON_SIZE_PX = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 20,
  xl: 24,
  "2xl": 32,
  "3xl": 40,
  display: 48,
} as const;

export const ICON_TONES = [
  "current",
  "muted",
  "accent",
  "info",
  "success",
  "warning",
  "danger",
  "purple",
  "teal",
  "pink",
] as const;

export type IconSize = keyof typeof ICON_SIZE_PX | number;
export type IconTone = (typeof ICON_TONES)[number];
export type IconMotion = "none" | "pulse" | "spin";
export type IconBadgeVariant = "plain" | "outline" | "soft" | "solid";
export type IconBadgeShape = "rounded" | "circle" | "square";

type AccessibleIconProps =
  | { decorative?: true; label?: never }
  | { decorative: false; label: string };

export type NorthStarIconProps = AccessibleIconProps & {
  className?: string;
  motion?: IconMotion;
  name: IconReference;
  size?: IconSize;
  strokeWidth?: number;
  tone?: IconTone;
};

export function NorthStarIcon({
  className,
  decorative = true,
  label,
  motion = "none",
  name,
  size = "md",
  strokeWidth = 1.85,
  tone = "current",
}: NorthStarIconProps) {
  const definition = getIconDefinition(name);
  const Icon = definition.component;
  const pixelSize = typeof size === "number" ? size : ICON_SIZE_PX[size];
  const classes = [
    "north-star-icon",
    `icon-tone-${tone}`,
    motion !== "none" ? `icon-motion-${motion}` : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");
  const style = {
    "--icon-size": `${pixelSize}px`,
  } as CSSProperties;

  return (
    <Icon
      absoluteStrokeWidth
      aria-hidden={decorative ? "true" : undefined}
      aria-label={decorative ? undefined : label}
      className={classes}
      data-directional={definition.directional ? "true" : undefined}
      data-icon-name={definition.name}
      focusable="false"
      role={decorative ? undefined : "img"}
      size={pixelSize}
      strokeWidth={strokeWidth}
      style={style}
    />
  );
}

export type NorthStarIconBadgeProps = AccessibleIconProps & {
  className?: string;
  icon: IconReference;
  motion?: IconMotion;
  shape?: IconBadgeShape;
  size?: IconSize;
  tone?: Exclude<IconTone, "current">;
  variant?: IconBadgeVariant;
};

export function NorthStarIconBadge({
  className,
  decorative = true,
  icon,
  label,
  motion = "none",
  shape = "rounded",
  size = "lg",
  tone = "accent",
  variant = "soft",
}: NorthStarIconBadgeProps) {
  const pixelSize = typeof size === "number" ? size : ICON_SIZE_PX[size];
  const classes = [
    "north-star-icon-badge",
    `icon-badge-${variant}`,
    `icon-badge-${shape}`,
    `icon-tone-${tone}`,
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");
  const style = {
    "--icon-size": `${pixelSize}px`,
  } as CSSProperties;

  return (
    <span className={classes} data-icon-badge-tone={tone} style={style}>
      {decorative ? (
        <NorthStarIcon motion={motion} name={icon} size={size} tone={tone} />
      ) : (
        <NorthStarIcon
          decorative={false}
          label={label ?? `${getIconDefinition(icon).label} icon`}
          motion={motion}
          name={icon}
          size={size}
          tone={tone}
        />
      )}
    </span>
  );
}

export type { IconAlias, IconName, IconReference };
