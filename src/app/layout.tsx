import type { Metadata } from "next";
import { Geist, JetBrains_Mono, Cormorant_Garamond } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

const cormorantGaramond = Cormorant_Garamond({
  variable: "--font-cormorant",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "SVA — Semantic Verification & Assurance",
  description: "Software that can prove it understands your intent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${jetBrainsMono.variable} ${cormorantGaramond.variable} antialiased min-h-screen flex flex-col bg-[#17130F] text-[#F5EFE5]`}
      >
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
