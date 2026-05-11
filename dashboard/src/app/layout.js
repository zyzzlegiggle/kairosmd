import "./globals.css";
import Sidebar from "../components/Sidebar.js";

export const metadata = {
  title: "KairosMD — Ward Round Decision Support",
  description: "Multidisciplinary Clinical Decision Support System",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex">
        {/* Sidebar Navigation */}
        <Sidebar />

        {/* Main content */}
        <main className="ml-60 flex-1 min-h-screen">
          {/* Top bar */}
          <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-border px-8 py-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-text-primary">General Medicine Ward</h2>
              <p className="text-xs text-text-tertiary">
                {new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
              </p>
            </div>
          </header>

          {/* Page content */}
          <div className="p-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
