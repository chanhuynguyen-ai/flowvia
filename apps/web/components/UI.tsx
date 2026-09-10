import { useEffect, useRef, type ReactNode } from "react";
import {
  AlertCircle,
  Bot,
  CirclePlay,
  GitBranch,
  Hand,
  Inbox,
  Mail,
  MessageCircle,
  Network,
  Send,
  Settings2,
  ShieldCheck,
  Workflow,
  X,
} from "lucide-react";

export function NodeIcon({ type, size = 20 }: { type: string; size?: number }) {
  const Icon = type.includes("telegram")
    ? Send
    : type === "ai_agent"
      ? Bot
      : type === "if_else"
        ? GitBranch
        : type === "human_approval"
          ? ShieldCheck
          : type === "data_map"
            ? Settings2
            : type === "manual_trigger"
              ? Hand
              : type === "record_action"
                ? Inbox
                : Workflow;
  return <Icon size={size} />;
}
export function ChannelIcon({
  channel,
  size = 20,
}: {
  channel: string;
  size?: number;
}) {
  const Icon =
    channel === "telegram"
      ? Send
      : channel === "email"
        ? Mail
        : channel === "manual"
          ? CirclePlay
          : channel === "openrouter"
            ? Network
            : MessageCircle;
  return <Icon size={size} />;
}
export function Badge({ status }: { status: string }) {
  return (
    <span className={`badge badge-${status}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}
export function ErrorNotice({ message }: { message?: string }) {
  return message ? (
    <div className="notice notice-error" role="alert">
      <AlertCircle size={17} />
      <span>{message}</span>
    </div>
  ) : null;
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <Workflow size={30} />
      <h3>{title}</h3>
      {children}
    </div>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
    return () => ref.current?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      className="modal"
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-heading">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={19} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function dateTime(value: string) {
  return new Date(
    value.endsWith("Z") || /[+-]\d\d:\d\d$/.test(value) ? value : value + "Z",
  ).toLocaleString("vi-VN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
