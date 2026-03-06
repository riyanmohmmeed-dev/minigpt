import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mini-ChatGPT for Coding",
  description: "Specialized coding assistant — stream from your own SLM",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
