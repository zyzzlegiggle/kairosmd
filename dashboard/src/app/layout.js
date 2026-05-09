import "./globals.css";

export const metadata = {
  title: "KairosMD - Ward Round Dashboard",
  description: "Inpatient ward round decision support system",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-900 min-h-screen">
        <nav className="border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold">KairosMD</h1>
            <span className="text-xs text-gray-400 border-l border-gray-300 pl-3">
              Ward Round Dashboard
            </span>
          </div>
          <div className="flex gap-4 text-sm">
            <a href="/dashboard" className="text-gray-600 hover:text-gray-900">Ward</a>
            <a href="/dashboard/conflicts" className="text-gray-600 hover:text-gray-900">Conflicts</a>
            <a href="/dashboard/discharge" className="text-gray-600 hover:text-gray-900">Discharge</a>
          </div>
        </nav>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
