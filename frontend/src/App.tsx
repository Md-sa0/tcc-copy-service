import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  ChevronRight,
  Command,
  FileText,
  KeyRound,
  LayoutDashboard,
  LoaderCircle,
  Plus,
  Search,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { api, setAccessKey } from "./api";
import Dashboard from "./Dashboard";
import ProductForm from "./ProductForm";
import Previews from "./Previews";
import type {
  Copy,
  Generation,
  Page,
  Product,
  ProductInput,
  Tone,
} from "./types";

type View = "generator" | "catalog" | "metrics";
export default function App() {
  const [view, setView] = useState<View>("generator");
  const [health, setHealth] = useState<{
    provider: string;
    model: string;
  } | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [result, setResult] = useState<Generation | null>(null);
  const [busy, setBusy] = useState(false),
    [toast, setToast] = useState("");
  const [query, setQuery] = useState(""),
    [offset, setOffset] = useState(0),
    [revision, setRevision] = useState(0);
  const [catalog, setCatalog] = useState<Page<Product> | null>(null),
    [catalogError, setCatalogError] = useState("");
  const [catalogLoading, setCatalogLoading] = useState(false),
    [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [history, setHistory] = useState<Copy[]>([]),
    [historyError, setHistoryError] = useState("");
  const [showKey, setShowKey] = useState(false),
    [key, setKey] = useState("");
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
  }, [view]);
  useEffect(() => {
    api<{ provider: string; model: string }>("/health")
      .then(setHealth)
      .catch(() => setHealth(null));
  }, [revision]);
  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(id);
  }, [toast]);
  useEffect(() => {
    const controller = new AbortController();
    setCatalogLoading(true);
    const id = window.setTimeout(() => {
      setCatalogError("");
      api<Page<Product>>(
        `/api/v1/products?q=${encodeURIComponent(query)}&offset=${offset}&limit=12`,
        { signal: controller.signal },
      )
        .then(setCatalog)
        .catch((e) => {
          if (!controller.signal.aborted) setCatalogError(e.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setCatalogLoading(false);
        });
    }, 250);
    return () => {
      clearTimeout(id);
      controller.abort();
    };
  }, [query, offset, revision]);
  useEffect(() => {
    setHistory([]);
    setHistoryError("");
    if (!product) return;
    const controller = new AbortController();
    api<Page<Copy>>(`/api/v1/copies?product_id=${product.id}&limit=10`, {
      signal: controller.signal,
    })
      .then((v) => setHistory(v.items))
      .catch((e) => {
        if (!controller.signal.aborted) setHistoryError(e.message);
      });
    return () => controller.abort();
  }, [product, revision]);
  async function save(data: ProductInput, tone: Tone, generate: boolean) {
    setBusy(true);
    try {
      const saved = await api<Product>(
        product ? `/api/v1/products/${product.id}` : "/api/v1/products",
        { method: product ? "PUT" : "POST", body: JSON.stringify(data) },
      );
      setProduct(saved);
      setResult(null);
      setRevision((v) => v + 1);
      if (generate) {
        const generated = await api<Generation>("/api/v1/copies/generate", {
          method: "POST",
          body: JSON.stringify({ product_id: saved.id, tone_of_voice: tone }),
        });
        setResult(generated);
        setRevision((v) => v + 1);
        setToast(
          generated.cache_status === "HIT"
            ? "Conteúdo recuperado do cache."
            : "Conteúdo gerado e salvo no histórico.",
        );
      } else setToast("Produto salvo no catálogo.");
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (!deleteTarget) return;
    setBusy(true);
    try {
      await api(`/api/v1/products/${deleteTarget.id}`, { method: "DELETE" });
      if (product?.id === deleteTarget.id) {
        setProduct(null);
        setResult(null);
      }
      setDeleteTarget(null);
      setOffset(0);
      setRevision((v) => v + 1);
      setToast("Produto e copies removidos.");
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Falha ao excluir.");
    } finally {
      setBusy(false);
    }
  }
  function selectProduct(item: Product) {
    setProduct(item);
    setResult(null);
    setView("generator");
  }
  const title =
    view === "generator"
      ? "Uma ideia. Todos os canais."
      : view === "catalog"
        ? "Seu catálogo, organizado."
        : "Da geração à evidência.";
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setView("generator");
          }}
        >
          <div className="brand-icon">
            <Command size={24} />
          </div>
          <span>
            copylab<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">M</span>
          <div>
            <strong>Laboratório de conteúdo</strong>
            <small>Workspace acadêmico</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <span className="nav-label">WORKSPACE</span>
        <nav>
          {(
            [
              { id: "generator", label: "Estúdio de criação", Icon: Sparkles },
              { id: "catalog", label: "Catálogo de produtos", Icon: Boxes },
              {
                id: "metrics",
                label: "Métricas de engenharia",
                Icon: LayoutDashboard,
              },
            ] as const
          ).map((item) => (
            <button
              disabled={busy}
              key={item.id}
              className={view === item.id ? "selected" : ""}
              onClick={() => setView(item.id)}
            >
              <item.Icon size={19} />
              {item.label}
              {view === item.id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="architecture-note">
            <Activity size={18} />
            <strong>Projetado para medir.</strong>
            <p>
              Conteúdo estruturado, cache determinístico e dados para cada
              decisão.
            </p>
            <span>FastAPI + Gemini + Redis</span>
          </div>
          <div className="academic">
            <div className="academic-logo">iCEV</div>
            <span>
              Engenharia de Software<small>Projeto de conclusão de curso</small>
            </span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            Workspace <ChevronRight size={14} />
            <strong>
              {view === "generator"
                ? "Estúdio de criação"
                : view === "catalog"
                  ? "Catálogo"
                  : "Métricas de engenharia"}
            </strong>
          </div>
          <div>
            <span className={`connection ${health ? "online" : ""}`}>
              <i />
              {health ? "API conectada" : "API indisponível"}
            </span>
            <button
              className="icon-button"
              aria-label="Configurar chave de acesso"
              title="Chave de acesso à API"
              onClick={() => setShowKey(true)}
            >
              <KeyRound size={18} />
            </button>
            <span className="user-avatar">MD</span>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                {view === "generator"
                  ? "CONTEÚDO COM INTELIGÊNCIA"
                  : view === "catalog"
                    ? "BASE DE PRODUTOS"
                    : "OBSERVABILIDADE & PESQUISA"}
              </span>
              <h1>{title}</h1>
              <p>
                {view === "generator"
                  ? "Transforme atributos do produto em conteúdo que conecta."
                  : view === "catalog"
                    ? "Gerencie a fonte de verdade das suas próximas campanhas."
                    : "Acompanhe desempenho, reaproveitamento e consumo da aplicação."}
              </p>
            </div>
            <span className="version-tag">
              CopyLab <span>v2.0</span>
            </span>
          </div>
          {view !== "metrics" && health?.provider === "mock" && (
            <div className="demo-banner">
              <Sparkles size={16} />
              <span>
                Modo demonstração · conteúdo simulado, sem chamadas ao Gemini.
              </span>
            </div>
          )}
          {view === "generator" && (
            <>
              <div className="flow-strip">
                <span className="flow-step">
                  <b>1</b> Cadastre o produto
                </span>
                <ChevronRight size={14} />
                <span className="flow-step">
                  <b>2</b> Escolha o tom
                </span>
                <ChevronRight size={14} />
                <span className="flow-step">
                  <b>3</b> Gere o conteúdo
                </span>
                <span className="flow-end">
                  <CheckCircle2 size={14} /> Três canais. Um fluxo.
                </span>
              </div>
              <div className="studio-grid">
                <div>
                  <ProductForm
                    product={product}
                    busy={busy}
                    onSave={save}
                    onClear={() => {
                      setProduct(null);
                      setResult(null);
                    }}
                  />
                  {historyError && (
                    <div className="error-box" role="alert">
                      {historyError}
                    </div>
                  )}
                  {history.length > 0 && (
                    <section className="panel copy-history">
                      <span className="eyebrow">
                        ÚLTIMAS VERSÕES DO PRODUTO
                      </span>
                      {history.map((copy) => (
                        <button
                          disabled={busy}
                          key={copy.id}
                          onClick={() =>
                            setResult({ copy, cache_status: "MISS" })
                          }
                        >
                          <FileText size={16} />
                          <span>
                            {copy.tone_of_voice}
                            <small>
                              {new Date(copy.created_at).toLocaleString(
                                "pt-BR",
                              )}{" "}
                              · {copy.model_name}
                            </small>
                          </span>
                          <ArrowUpRight size={15} />
                        </button>
                      ))}
                    </section>
                  )}
                </div>
                <div className="output-column">
                  {result ? (
                    <>
                      <Previews copy={result.copy} notify={setToast} />
                      <div className="hash-card">
                        <DatabaseBadge status={result.cache_status} />
                        <code>{result.copy.input_hash}</code>
                        <small>
                          SHA-256 dos dados canônicos · A versão exibida pode
                          ser consultada no histórico.
                        </small>
                      </div>
                    </>
                  ) : (
                    <section className="panel empty-preview">
                      <div className="empty-preview-top">
                        <span className="eyebrow">SEU PRÓXIMO CONTEÚDO</span>
                        <span className="badge">3 canais</span>
                      </div>
                      <div className="empty-illustration">
                        <div className="mini-card back">
                          <span />
                          <span />
                          <span />
                        </div>
                        <div className="mini-card front">
                          <Sparkles size={32} />
                          <span />
                          <span />
                        </div>
                        <i className="spark">✦</i>
                      </div>
                      <h2>
                        {busy
                          ? "Preparando sua próxima campanha…"
                          : "Boas histórias começam\ncom bons produtos."}
                      </h2>
                      <p>
                        {busy
                          ? "Validando os dados e preparando as saídas estruturadas. Isso pode levar alguns instantes."
                          : "Preencha os detalhes ao lado. O CopyLab cuida da primeira versão para cada canal."}
                      </p>
                      {busy && <LoaderCircle className="spin" size={24} />}
                      <div className="channel-pills">
                        <span>Instagram</span>
                        <span>WhatsApp</span>
                        <span>E-commerce</span>
                      </div>
                      <div className="empty-bottom">
                        <CheckCircle2 size={16} /> Cada saída é validada antes
                        de chegar até você.
                      </div>
                    </section>
                  )}
                  <div className="editorial-note">
                    <span>↗</span>
                    <div>
                      <strong>Os detalhes fazem a diferença.</strong>
                      <p>
                        Benefícios específicos e atributos completos ajudam a
                        criar mensagens mais relevantes. Revise o conteúdo antes
                        de publicar.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
          {view === "catalog" && (
            <>
              <div className="section-toolbar">
                <label className="search-field">
                  <Search size={17} />
                  <input
                    placeholder="Buscar nome ou SKU"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setOffset(0);
                    }}
                  />
                </label>
                <button
                  className="button primary"
                  onClick={() => {
                    setProduct(null);
                    setResult(null);
                    setView("generator");
                  }}
                >
                  <Plus size={17} /> Novo produto
                </button>
              </div>
              {catalogError && (
                <div className="error-box" role="alert">
                  {catalogError}
                </div>
              )}
              {catalogLoading && <p role="status">Carregando catálogo…</p>}
              <div className="catalog-grid">
                {catalog?.items.map((item) => (
                  <article className="panel catalog-card" key={item.id}>
                    <div>
                      <span className="badge">{item.category}</span>
                      <button
                        className="icon-button"
                        aria-label={`Excluir ${item.name}`}
                        onClick={() => setDeleteTarget(item)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                    <small>{item.sku}</small>
                    <h2>{item.name}</h2>
                    <p>{item.target_audience}</p>
                    <span>
                      {item.key_benefits.length} benefícios ·{" "}
                      {Object.keys(item.technical_attributes).length} atributos
                    </span>
                    <button
                      className="button secondary"
                      onClick={() => selectProduct(item)}
                    >
                      Editar e gerar <ArrowUpRight size={16} />
                    </button>
                  </article>
                ))}
              </div>
              {!catalogLoading && !catalogError && !catalog?.items.length && (
                <div className="panel empty-catalog">
                  <Boxes size={34} />
                  <h2>
                    {query
                      ? "Nenhum produto encontrado"
                      : "Seu catálogo começa aqui"}
                  </h2>
                  <p>
                    {query
                      ? "Experimente outro nome ou SKU."
                      : "Cadastre um produto no estúdio ou execute o script de carga."}
                  </p>
                </div>
              )}
              <div className="pagination">
                <span>{catalog?.total ?? 0} produtos</span>
                <button
                  disabled={offset === 0 || catalogLoading}
                  onClick={() => setOffset(Math.max(0, offset - 12))}
                >
                  Anterior
                </button>
                <button
                  disabled={
                    !catalog || offset + 12 >= catalog.total || catalogLoading
                  }
                  onClick={() => setOffset(offset + 12)}
                >
                  Próxima
                </button>
              </div>
            </>
          )}
          {view === "metrics" && <Dashboard key={revision} />}
          <footer className="page-footer">
            <span>
              CopyLab · Automação de conteúdo para o varejo eletrônico
            </span>
            <span>Marcus David Nascimento de Sá · iCEV</span>
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={19} />
          <span>{toast}</span>
          <button aria-label="Fechar notificação" onClick={() => setToast("")}>
            <X size={16} />
          </button>
        </div>
      )}
      {showKey && (
        <div className="modal-backdrop">
          <form
            role="dialog"
            aria-modal="true"
            aria-labelledby="access-title"
            className="panel modal"
            onSubmit={(e) => {
              e.preventDefault();
              setAccessKey(key.trim());
              setShowKey(false);
              setRevision((v) => v + 1);
              setToast("Chave de acesso aplicada nesta sessão.");
            }}
          >
            <h2 id="access-title">Acesso à API</h2>
            <p>
              Informe a API_KEY configurada no servidor. A chave fica apenas na
              memória desta aba.
            </p>
            <label>
              Chave de acesso
              <input
                autoFocus
                type="password"
                autoComplete="off"
                value={key}
                onChange={(e) => setKey(e.target.value)}
              />
            </label>
            <div className="form-actions">
              <button
                type="button"
                className="button secondary"
                onClick={() => setShowKey(false)}
              >
                Cancelar
              </button>
              <button className="button primary">Aplicar</button>
            </div>
          </form>
        </div>
      )}
      {deleteTarget && (
        <div className="modal-backdrop">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-title"
            className="panel modal"
          >
            <h2 id="delete-title">Excluir {deleteTarget.name}?</h2>
            <p>
              O produto e suas copies serão excluídos permanentemente. A
              auditoria das requisições será preservada.
            </p>
            <div className="form-actions">
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => setDeleteTarget(null)}
              >
                Cancelar
              </button>
              <button
                className="button danger"
                disabled={busy}
                onClick={remove}
              >
                Excluir produto
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DatabaseBadge({ status }: { status: string }) {
  return (
    <span className={`badge ${status === "HIT" ? "green" : ""}`}>
      {status === "HIT" ? "CACHE HIT" : "VERSÃO PERSISTIDA"}
    </span>
  );
}
