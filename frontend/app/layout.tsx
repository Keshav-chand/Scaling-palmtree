import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Helio Analysis",
  description: "AI assistant conversation insights",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}