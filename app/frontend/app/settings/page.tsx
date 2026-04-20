"use client";
import { useEffect, useState } from "react";
import { Check, MoonStar, SunMedium, Sparkles, Target, Info } from "lucide-react";

type ChatStyle = "precise" | "natural";
type Theme = "light" | "dark";

const STYLE_KEY = "leadsmap_chat_style";
const THEME_KEY = "leadsmap_theme";
const APP_VERSION = "1.0.0";

export default function Settings() {
  const [style, setStyle] = useState<ChatStyle>("natural");
  const [theme, setTheme] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setMounted(true);
    const s = localStorage.getItem(STYLE_KEY);
    if (s === "precise" || s === "natural") setStyle(s);
    const t = localStorage.getItem(THEME_KEY);
    if (t === "dark" || t === "light") setTheme(t);
  }, []);

  function selectStyle(next: ChatStyle) {
    setStyle(next);
    localStorage.setItem(STYLE_KEY, next);
    flashSaved();
  }

  function selectTheme(next: Theme) {
    setTheme(next);
    localStorage.setItem(THEME_KEY, next);
    // Notify the layout (same tab) so the sidebar/html class re-syncs immediately.
    window.dispatchEvent(new CustomEvent("leadsmap_theme_change", { detail: next }));
    flashSaved();
  }

  function flashSaved() {
    setSaved(true);
    setTimeout(() => setSaved(false), 1400);
  }

  if (!mounted) return null;

  return (
    <div style={{ padding: "28px 32px", maxWidth: 760 }}>
      <div style={{ marginBottom: 28, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text)" }}>Cài đặt</h1>
          <p style={{ fontSize: 13, color: "var(--text2)", marginTop: 2 }}>
            Tùy chỉnh trải nghiệm trợ lý AI Agent
          </p>
        </div>
        {saved && (
          <span className="badge badge-status-ok" style={{ display: "inline-flex", alignItems: "center" }}>
            <Check size={11} style={{ marginRight: 4 }} /> Đã lưu
          </span>
        )}
      </div>

      {/* 1. Style for model */}
      <section className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>
          Phong cách trả lời của AI
        </h3>
        <p style={{ fontSize: 12, color: "var(--text2)", marginBottom: 14 }}>
          Chọn cách AI tạo phản hồi cho mọi câu hỏi.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <StyleCard
            active={style === "precise"}
            onClick={() => selectStyle("precise")}
            icon={<Target size={16} />}
            title="Chính xác"
            description="Bám sát dữ liệu hệ thống, không suy đoán. Khi thiếu dữ liệu sẽ trả lời rõ là không có thay vì bịa ra."
          />
          <StyleCard
            active={style === "natural"}
            onClick={() => selectStyle("natural")}
            icon={<Sparkles size={16} />}
            title="Tự nhiên"
            description="Trò chuyện linh hoạt, có suy luận và phân tích. Phù hợp khi cần ý tưởng, phân tích thị trường, gợi ý."
          />
        </div>
      </section>

      {/* 2. Theme switch */}
      <section className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>
          Giao diện
        </h3>
        <p style={{ fontSize: 12, color: "var(--text2)", marginBottom: 14 }}>
          Chuyển đổi giữa chế độ sáng và tối.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <StyleCard
            active={theme === "light"}
            onClick={() => selectTheme("light")}
            icon={<SunMedium size={16} />}
            title="Giao diện sáng"
            description="Nền sáng, phù hợp môi trường làm việc ban ngày."
          />
          <StyleCard
            active={theme === "dark"}
            onClick={() => selectTheme("dark")}
            icon={<MoonStar size={16} />}
            title="Giao diện tối"
            description="Nền tối, dễ chịu cho mắt khi làm việc lâu hoặc trong điều kiện ánh sáng yếu."
          />
        </div>
      </section>

      {/* 3. Version info */}
      <section className="card">
        <h3 style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 12 }}>
          <Info size={14} style={{ display: "inline", marginRight: 8, marginBottom: -2 }} />
          Thông tin phiên bản
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {[
            ["Phiên bản", `v${APP_VERSION}`],
            ["Sản phẩm", "Leadmap web app"],
          ].map(([k, v]) => (
            <div
              key={k}
              style={{
                padding: "10px 12px",
                background: "var(--surface-container)",
                borderRadius: 8,
                border: "1px solid var(--border)",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  color: "var(--text2)",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  marginBottom: 4,
                }}
              >
                {k}
              </div>
              <div style={{ fontSize: 13, color: "var(--text)", fontWeight: 500 }}>{v}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function StyleCard({
  active,
  onClick,
  icon,
  title,
  description,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        textAlign: "left",
        padding: "14px 14px",
        borderRadius: 10,
        border: active ? "1px solid var(--primary)" : "1px solid var(--border)",
        background: active ? "color-mix(in srgb, var(--primary) 8%, var(--surface-container))" : "var(--surface-container)",
        cursor: "pointer",
        transition: "all 150ms",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        position: "relative",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: active ? "var(--primary)" : "var(--text2)" }}>{icon}</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>{title}</span>
        {active && (
          <span
            style={{
              marginLeft: "auto",
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              color: "var(--primary)",
              fontWeight: 600,
            }}
          >
            <Check size={11} /> Đang dùng
          </span>
        )}
      </div>
      <p style={{ fontSize: 12, color: "var(--text2)", lineHeight: 1.5, margin: 0 }}>{description}</p>
    </button>
  );
}
