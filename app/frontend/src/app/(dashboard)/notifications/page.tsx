"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { notifications as api } from "@/lib/api";
import { Bell, MessageSquare, Mail } from "lucide-react";

export default function NotificationsPage() {
  const router = useRouter();
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.list(100).then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-brand-700 mb-6">Уведомления</h1>

      {loading ? (
        <div className="text-brand-300">Загрузка...</div>
      ) : data.length === 0 ? (
        <div className="bg-white rounded-xl3 border border-brand-100 p-12 text-center text-brand-300">
          <Bell className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>Уведомлений пока нет</p>
        </div>
      ) : (
        <div className="space-y-2">
          {data.map((n) => (
            <div
              key={n.id}
              onClick={() => router.push(`/returns?open=${n.return_request_id}`)}
              className="bg-white rounded-xl3 border border-brand-100 p-4 flex gap-4 cursor-pointer hover:border-brand-300 transition"
            >
              <div className="w-10 h-10 rounded-full bg-brand-50 flex items-center justify-center flex-shrink-0">
                {n.channel === "sms" ? <MessageSquare className="w-5 h-5 text-brand-500" /> : <Mail className="w-5 h-5 text-brand-500" />}
              </div>
              <div className="flex-1">
                <div className="text-sm text-brand-700 font-medium">{n.message}</div>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                  <span className="uppercase font-semibold">{n.channel}</span>
                  <span>{n.recipient_contact}</span>
                  <span>•</span>
                  <span>{n.created_at?.slice(0, 16).replace("T", " ")}</span>
                  {n.is_sent && <span className="text-green-500 font-semibold">отправлено</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
