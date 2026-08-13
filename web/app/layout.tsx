import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "WoundAI Research",
  description: "Explainable wound image classification research platform"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <main className="shell">
          <nav className="nav">
            <Link href="/" className="brand">WoundAI Research</Link>
            <div className="navlinks">
              <Link href="/analyze">Analyze</Link>
              <Link href="/history">History</Link>
              <Link href="/research">Research</Link>
              <Link href="/review">Review</Link>
              <Link href="/login">Login</Link>
            </div>
          </nav>
          {children}
        </main>
      </body>
    </html>
  );
}
