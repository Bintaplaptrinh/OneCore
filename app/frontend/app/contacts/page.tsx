"use client";
import { useEffect, useState } from "react";
import { api, Contact } from "@/lib/api";
import { Search, User, Phone, Mail, Building2, RefreshCw, Users } from "lucide-react";

function ContactCard({ c }: { c: Contact }) {
  return (
    <div className="card hover:border-accent/40 transition-all hover:-translate-y-0.5 cursor-default">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center bg-accent/10 border border-accent/20">
          <User size={17} className="text-accent" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-text truncate">{c.name}</p>
          {c.role && <p className="text-[11px] text-text2 truncate mt-0.5">{c.role}</p>}

          {c.company && (
            <div className="flex items-center gap-1 mt-2">
              <Building2 size={11} className="text-[#F59E0B] flex-shrink-0" />
              <span className="text-[11px] text-text2 truncate">{c.company}</span>
            </div>
          )}

          <div className="flex flex-col gap-1 mt-2">
            {c.phone && (
              <div className="flex items-center gap-1.5">
                <Phone size={11} className="text-[#10B981] flex-shrink-0" />
                <span className="text-[11px] text-text font-medium">{c.phone}</span>
              </div>
            )}
            {c.email && (
              <div className="flex items-center gap-1.5">
                <Mail size={11} className="text-accent flex-shrink-0" />
                <span className="text-[11px] text-accent truncate">{c.email}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [total, setTotal]       = useState(0);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState("");
  const [company, setCompany]   = useState("");
  const [page, setPage]         = useState(1);
  const LIMIT = 100; // matches backend default

  useEffect(() => {
    setLoading(true);
    api.contacts({ search, company, page })
      .then(r => { setContacts(r.data); setTotal(r.total); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [search, company, page]);

  const totalPages = Math.ceil(total / LIMIT);

  return (
    <div className="px-8 py-7">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-[22px] font-bold text-text">Contacts</h1>
          <p className="text-[13px] text-text2 mt-0.5">
            Danh sách liên hệ từ các dự án bất động sản
          </p>
        </div>
        <div className="card py-2 px-4 flex items-center gap-2">
          <Users size={15} className="text-[#10B981]" />
          <span className="text-sm font-bold text-text">{total.toLocaleString()}</span>
          <span className="text-xs text-text2">liên hệ</span>
        </div>
      </div>

      {/* Filter bar */}
      <div className="card mb-5">
        <div className="flex gap-2.5 flex-wrap items-center">
          <div className="relative flex-[2] min-w-[200px]">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text2 pointer-events-none" />
            <input
              className="input pl-8"
              placeholder="Tên, email, số điện thoại..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <input
            className="input flex-1 min-w-[180px]"
            placeholder="Lọc theo công ty..."
            value={company}
            onChange={e => { setCompany(e.target.value); setPage(1); }}
          />
          <button className="btn btn-ghost" onClick={() => { setSearch(""); setCompany(""); setPage(1); }}>
            <RefreshCw size={14} /> Reset
          </button>
        </div>
        <p className="text-[11px] text-text2 mt-2.5">
          Hiển thị {contacts.length} / {total} liên hệ
        </p>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="text-center py-10 text-text2">Đang tải...</div>
      ) : contacts.length === 0 ? (
        <div className="text-center py-16 text-text2">
          <Users size={40} className="mx-auto mb-3 opacity-30" />
          <p>Không tìm thấy liên hệ nào</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-5">
            {contacts.map(c => <ContactCard key={c.slug} c={c} />)}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                ← Trước
              </button>
              <span className="text-[13px] text-text2">Trang {page} / {totalPages}</span>
              <button className="btn btn-ghost" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                Sau →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
