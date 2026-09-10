import type { ReactNode } from "react";

export type IconName =
  | "overview"
  | "inbox"
  | "connections"
  | "agents"
  | "workflows"
  | "runs"
  | "analytics"
  | "settings"
  | "search"
  | "plus"
  | "arrow"
  | "bolt"
  | "check"
  | "clock"
  | "telegram"
  | "mail"
  | "message"
  | "instagram"
  | "zalo";

type IconProps = {
  name: IconName;
  size?: number;
};

const paths: Record<IconName, ReactNode> = {
  overview: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="2" />
      <rect x="14" y="3" width="7" height="7" rx="2" />
      <rect x="3" y="14" width="7" height="7" rx="2" />
      <rect x="14" y="14" width="7" height="7" rx="2" />
    </>
  ),
  inbox: (
    <>
      <path d="M4 4h16v13H4z" />
      <path d="M4 13h4l2 3h4l2-3h4" />
    </>
  ),
  connections: (
    <>
      <circle cx="7" cy="12" r="3" />
      <circle cx="17" cy="7" r="3" />
      <circle cx="17" cy="17" r="3" />
      <path d="m10 11 4-2M10 13l4 2" />
    </>
  ),
  agents: (
    <>
      <rect x="5" y="7" width="14" height="11" rx="4" />
      <path d="M9 11h.01M15 11h.01M9 15h6M12 7V4M9 4h6" />
    </>
  ),
  workflows: (
    <>
      <rect x="3" y="4" width="6" height="5" rx="1.5" />
      <rect x="15" y="15" width="6" height="5" rx="1.5" />
      <rect x="15" y="4" width="6" height="5" rx="1.5" />
      <path d="M9 6.5h6M6 9v4a4 4 0 0 0 4 4h5" />
    </>
  ),
  runs: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m10 8 6 4-6 4z" />
    </>
  ),
  analytics: (
    <>
      <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19 13.5v-3l-2-.7-.7-1.7.9-1.9-2.1-2.1-1.9.9-1.7-.7-.7-2h-3l-.7 2-1.7.7-1.9-.9L1.4 6.2l.9 1.9-.7 1.7-2 .7v3l2 .7.7 1.7-.9 1.9 2.1 2.1 1.9-.9 1.7.7.7 2h3l.7-2 1.7-.7 1.9.9 2.1-2.1-.9-1.9.7-1.7z" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  arrow: <path d="m9 18 6-6-6-6" />,
  bolt: <path d="m13 2-8 12h6l-1 8 9-13h-6z" />,
  check: <path d="m5 12 4 4L19 6" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  telegram: (
    <>
      <path d="m3 11 18-7-6 17-4-6-4 3 1-5z" />
      <path d="m8 13 8-5" />
    </>
  ),
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m4 7 8 6 8-6" />
    </>
  ),
  message: (
    <>
      <path d="M4 5h16v11H8l-4 4z" />
      <path d="M8 9h8M8 12h5" />
    </>
  ),
  instagram: (
    <>
      <rect x="4" y="4" width="16" height="16" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1" />
    </>
  ),
  zalo: (
    <>
      <path d="M4 5h16v12H9l-5 4z" />
      <path d="M8 9h8M8 13h6" />
    </>
  ),
};

export function Icon({ name, size = 18 }: IconProps) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
