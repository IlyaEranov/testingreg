import { STATUS_LABELS, STATUS_COLORS, type StatusCode } from "@/types";

export default function StatusBadge({ status }: { status: string }) {
  const code = status as StatusCode;
  const label = STATUS_LABELS[code] || status;
  const color = STATUS_COLORS[code] || "bg-gray-100 text-gray-800";

  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${color}`}
    >
      {label}
    </span>
  );
}
