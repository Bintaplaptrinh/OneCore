"use client";
import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import {
  LayoutDashboard,
  Network,
  MessageSquare,
  Users,
  Upload,
  Settings,
  Building2,
  FileText,
  Table2,
} from "lucide-react";


const NAV = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/chat", icon: MessageSquare, label: "Chat AI" },
  { href: "/graph", icon: Network, label: "Graph 2D" },
  { href: "/tables", icon: Table2, label: "Table Builder" },
  { href: "/contacts", icon: Users, label: "Contacts" },
  { href: "/reports", icon: FileText, label: "Báo cáo" },
  { href: "/upload", icon: Upload, label: "Upload" },
  { href: "/settings", icon: Settings, label: "Cài đặt" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();

  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  // Lazy init: read the saved theme synchronously on the client so the very
  // first render already carries the correct value. During SSR `window` is
  // undefined, so we fall back to "light" — the inline <head> script (below)
  // then fixes the <html> class before hydration to prevent a flash.
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const isFirstThemeEffect = useRef(true);

  useEffect(() => {
    setMounted(true);

    // Keep first hydrated render deterministic (light), then sync persisted theme.
    const saved = window.localStorage.getItem("leadsmap_theme");
    if (saved === "dark" || saved === "light") {
      setTheme(saved);
    } else if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
      setTheme("dark");
    }

    // Listen for theme changes from other tabs/components (e.g. Settings page).
    const onStorage = (e: StorageEvent) => {
      if (e.key === "leadsmap_theme" && (e.newValue === "dark" || e.newValue === "light")) {
        setTheme(e.newValue);
      }
    };
    const onCustom = (e: Event) => {
      const next = (e as CustomEvent<"light" | "dark">).detail;
      if (next === "dark" || next === "light") setTheme(next);
    };
    window.addEventListener("storage", onStorage);
    window.addEventListener("leadsmap_theme_change", onCustom as EventListener);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("leadsmap_theme_change", onCustom as EventListener);
    };
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    root.dataset.theme = theme;
    // Skip writing on the very first mount: localStorage already holds the
    // canonical value and writing it back is harmless, but if it ever fires
    // BEFORE another effect's setTheme propagates it would overwrite the
    // saved choice with the SSR default. The lazy init above prevents that
    // for normal flows; the ref is belt-and-suspenders.
    if (isFirstThemeEffect.current) {
      isFirstThemeEffect.current = false;
      return;
    }
    localStorage.setItem("leadsmap_theme", theme);
  }, [theme]);

  const width = collapsed ? 56 : 220;
  const marginLeft = collapsed ? 56 : 220;
  const effectiveTheme = mounted ? theme : "light";
  const sidebarBackground = effectiveTheme === "dark" ? "rgba(17,27,45,0.92)" : "rgba(243,247,251,0.95)";
  const sidebarShadow = effectiveTheme === "dark" ? "2px 0 24px rgba(0,0,0,0.34)" : "2px 0 20px rgba(0,88,186,0.08)";
  const sidebarDivider = effectiveTheme === "dark" ? "1px solid rgba(143,161,187,0.2)" : "1px solid rgba(0,88,186,0.08)";

  return (
    <html lang="vi" className={theme === "dark" ? "dark" : "light"} suppressHydrationWarning>
      <head>
        <title>HaiVo LeadsMap</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* Apply saved theme synchronously, before React hydrates, to avoid a
            light-mode flash on refresh when the user has chosen dark. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('leadsmap_theme');if(t!=='dark'&&t!=='light'){t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}var r=document.documentElement;r.classList.toggle('dark',t==='dark');r.classList.toggle('light',t!=='dark');r.dataset.theme=t;}catch(e){}})();`,
          }}
        />
      </head>
      <body className="flex min-h-screen bg-bg text-text font-sans antialiased">
        <aside
          onMouseEnter={() => setCollapsed(false)}
          onMouseLeave={() => setCollapsed(true)}
          className="fixed top-0 left-0 bottom-0 z-50 flex flex-col gap-1 overflow-hidden"
          style={{
            width: mounted ? width : 220,
            background: sidebarBackground,
            backdropFilter: "blur(20px)",
            boxShadow: sidebarShadow,
            transition: "width 250ms cubic-bezier(.4,0,.2,1)",
          }}
        >
          <div className="flex items-center px-3 pt-5 pb-4 mb-1" style={{ borderBottom: sidebarDivider }}>
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-accent to-violet-500 shadow-lg shadow-accent/30">
              <Building2 size={18} color="white" />
            </div>
            <div
              className="overflow-hidden whitespace-nowrap ml-2.5"
              style={{
                maxWidth: collapsed ? 0 : 140,
                opacity: collapsed ? 0 : 1,
                transition: "max-width 200ms, opacity 180ms",
              }}
            >
              <div className="font-bold text-sm text-text" style={{ fontFamily: "'Manrope', system-ui, sans-serif" }}>App</div>
              <div className="text-[10px] text-text2 tracking-[0.5px]">LEADSMAP INTELLIGENT</div>
            </div>
          </div>

          <div className="flex flex-col gap-0.5 px-1.5 flex-1">
            {NAV.map(({ href, icon: Icon, label }) => {
              const active = path.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  prefetch={false}
                  title={collapsed ? label : undefined}
                  className={`nav-item justify-start gap-3 ${active ? "active" : ""}`}
                  style={{ paddingLeft: collapsed ? "12px" : undefined }}
                >
                  <Icon size={16} className="flex-shrink-0" />
                  <span
                    className="overflow-hidden whitespace-nowrap"
                    style={{
                      maxWidth: collapsed ? 0 : 140,
                      opacity: collapsed ? 0 : 1,
                      transition: "max-width 200ms, opacity 150ms",
                    }}
                  >
                    {label}
                  </span>
                </Link>
              );
            })}
          </div>

        </aside>

        <main
          className="flex-1 min-h-screen overflow-auto"
          style={{
            marginLeft: mounted ? marginLeft : 220,
            transition: "margin-left 250ms cubic-bezier(.4,0,.2,1)",
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
