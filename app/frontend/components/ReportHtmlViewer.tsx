"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ReportChartSpec } from "@/lib/api";

const COLORS = ["#0058ba", "#10aebf", "#ff9f0a", "#ef536d", "#4a8eff", "#7ad7e4"];

function ChartBlock({ chart }: { chart: ReportChartSpec }) {
  const data = (chart.data || []).map((item) => ({
    label: String(item.label || ""),
    value: Number(item.value || 0),
  }));

  if (!data.length) return null;

  return (
    <div className="report-chart-card">
      <p className="report-chart-title">{chart.title}</p>
      <div className="report-chart-canvas">
        <ResponsiveContainer width="100%" height="100%">
          {chart.type === "line" ? (
            <LineChart data={data} margin={{ top: 10, right: 14, bottom: 22, left: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} angle={-18} textAnchor="end" height={42} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#0058ba" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          ) : chart.type === "pie" ? (
            <PieChart>
              <Tooltip />
              <Pie data={data} dataKey="value" nameKey="label" outerRadius={76} label>
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : (
            <BarChart data={data} margin={{ top: 10, right: 14, bottom: 22, left: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} angle={-18} textAnchor="end" height={42} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function ReportHtmlViewer({
  html,
  charts = [],
  compact = false,
}: {
  html?: string;
  charts?: ReportChartSpec[];
  compact?: boolean;
}) {
  const hasEmbeddedCharts = !!html && html.includes('data-static-charts="true"');

  return (
    <div className={`report-html-viewer ${compact ? "is-compact" : ""}`}>
      {charts.length > 0 && !hasEmbeddedCharts && (
        <div className="report-chart-grid">
          {charts.map((chart) => (
            <ChartBlock key={chart.id || chart.title} chart={chart} />
          ))}
        </div>
      )}

      {html ? (
        <iframe
          className="report-html-frame"
          title="Report HTML preview"
          sandbox=""
          srcDoc={html}
        />
      ) : (
        <div className="report-html-empty">Chưa có bản xem trước HTML.</div>
      )}
    </div>
  );
}
