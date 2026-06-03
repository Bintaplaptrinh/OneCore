"use client";

import "./globals.css";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import logo from "@/assets/logo.png";
import {
  FileText,
  LayoutDashboard,
  MessageSquare,
  Network,
  Settings,
  Table2,
  Users,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/chat", icon: MessageSquare, label: "Chat AI" },
  { href: "/graph", icon: Network, label: "Graph 2D" },
  { href: "/tables", icon: Table2, label: "Data Manager" },
  { href: "/contacts", icon: Users, label: "Contacts" },
  { href: "/reports", icon: FileText, label: "Reports" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

function isActivePath(path: string, href: string) {
  if (href === "/dashboard") return path === "/" || path.startsWith("/dashboard");
  return path.startsWith(href);
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "/dashboard";
  const reduceMotion = useReducedMotion();

  const [mounted, setMounted] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const isFirstThemeEffect = useRef(true);

  useEffect(() => {
    setMounted(true);

    const saved = window.localStorage.getItem("leadsmap_theme");
    if (saved === "dark" || saved === "light") {
      setTheme(saved);
    }

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
    root.classList.toggle("light", theme !== "dark");
    root.dataset.theme = theme;

    if (isFirstThemeEffect.current) {
      isFirstThemeEffect.current = false;
      return;
    }
    localStorage.setItem("leadsmap_theme", theme);
  }, [theme]);

  const spring = reduceMotion
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 420, damping: 34, mass: 0.7 };

  return (
    <html lang="vi" className={theme === "dark" ? "dark" : "light"} suppressHydrationWarning>
      <head>
        <title>Bintaplaptrinh CoreOne</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('leadsmap_theme');if(t!=='dark'&&t!=='light'){t='light';}var r=document.documentElement;r.classList.toggle('dark',t==='dark');r.classList.toggle('light',t!=='dark');r.dataset.theme=t;}catch(e){}})();`,
          }}
        />
      </head>
      <body className="min-h-screen text-text font-sans antialiased">
        <div className="app-canvas">
          <div className="app-shell" data-mounted={mounted ? "true" : "false"}>
            <aside className="app-sidebar" aria-label="Primary navigation">
              <Link href="/dashboard" className="app-sidebar-brand" aria-label="Bintaplaptrinh CoreOne dashboard">
                <span className="app-sidebar-logo">
                  <Image src={logo} alt="" width={32} height={32} priority />
                </span>
                <span className="app-sidebar-brand-text">Bintaplaptrinh</span>
              </Link>

              <nav className="app-sidebar-nav">
                {NAV.map(({ href, icon: Icon, label }) => {
                  const active = isActivePath(pathname, href);
                  return (
                    <Link
                      key={href}
                      href={href}
                      prefetch={false}
                      title={label}
                      aria-label={label}
                      aria-current={active ? "page" : undefined}
                      className={`app-nav-link ${active ? "is-active" : ""}`}
                    >
                      {active && (
                        <motion.span
                          layoutId="sidebar-active-indicator"
                          className="app-nav-active"
                          transition={spring}
                        />
                      )}
                      <Icon size={18} className="app-nav-icon" />
                      <span className="app-nav-label">{label}</span>
                    </Link>
                  );
                })}
              </nav>
            </aside>

            <main className="app-main">
              <AnimatePresence mode="wait" initial={false}>
                <motion.div
                  key={pathname}
                  className="app-page-transition"
                  initial={reduceMotion ? false : { opacity: 0, x: 22, scale: 0.992 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit={reduceMotion ? undefined : { opacity: 0, x: -14, scale: 0.994 }}
                  transition={reduceMotion ? { duration: 0 } : { duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                >
                  {children}
                </motion.div>
              </AnimatePresence>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
