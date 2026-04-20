export default function GlobalLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg text-text">
      <div className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3">
        <span className="inline-block h-3 w-3 rounded-full bg-accent animate-pulse" />
        <span className="text-sm text-text2">Dang tai trang...</span>
      </div>
    </div>
  );
}
