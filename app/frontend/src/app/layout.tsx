import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "АИС Сопровождение возвратов | Регион Сервис",
  description: "Автоматизированная информационная система сопровождения возврата товаров",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className="bg-brand-50 text-gray-800">{children}</body>
    </html>
  );
}
