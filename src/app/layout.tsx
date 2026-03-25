import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "next-themes";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RPA Learning System - AI-Powered Language Learning",
  description: "A self-improving AI learning system for vocabulary, grammar, and language skills. Powered by spaced repetition and adaptive learning algorithms.",
  keywords: ["RPA", "Language Learning", "Vocabulary", "Grammar", "Spaced Repetition", "AI", "Adaptive Learning"],
  authors: [{ name: "RPA Team" }],
  icons: {
    icon: "/logo.svg",
  },
  openGraph: {
    title: "RPA Learning System",
    description: "AI-powered language learning with spaced repetition",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
