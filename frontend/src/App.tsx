import { lazy, Suspense, useEffect, useState } from "react";
import {
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  ChevronRight,
  Command,
  FileText,
  LayoutDashboard,
  LoaderCircle,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Settings2,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { api, ApiError } from "./api";
import Login, { type AuthUser } from "./Login";
import Guide, { type Runtime } from "./Guide";
import ProductForm from "./ProductForm";
import ProviderSettings from "./ProviderSettings";
import Previews from "./Previews";
import type {
  Copy,
  CopyEdits,
  Generation,
  Page,
  Product,
  ProductInput,
  Tone,
} from "./types";

const Dashboard = lazy(() => import("./Dashboard"));

const MOCK_PRODUCTS: ProductInput[] = [
  {
    sku: "DEMO-FONE",
    name: "Fone Bluetooth Aura",
    category: "Eletrônicos",
    target_audience: "Pessoas que ouvem música na rotina",
    technical_attributes: { conectividade: "Bluetooth 5.3", autonomia: "24 horas" },
    key_benefits: ["Uso sem fios", "Estojo para transporte"],
  },
  {
    sku: "DEMO-TECLADO",
    name: "Teclado compacto Pixel",
    category: "Informática",
    target_audience: "Profissionais com mesas pequenas",
    technical_attributes: { layout: "ABNT2", conexão: "USB", formato: "60%" },
    key_benefits: ["Ocupa menos espaço", "Conexão por cabo"],
  },
  {
    sku: "DEMO-GARRAFA",
    name: "Garrafa inox Trilhas",
    category: "Casa e lazer",
    target_audience: "Pessoas que transportam água diariamente",
    technical_attributes: { volume: "600 ml", material: "aço inox" },
    key_benefits: ["Recipiente reutilizável", "Tampa rosqueável"],
  },
];

type View = "generator" | "product" | "catalog" | "metrics" | "guide" | "settings";
export default function App() {
  const [account, setAccount] = useState<AuthUser | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const [view, setView] = useState<View>(
    window.location.hash === "#como-funciona" ? "guide" : "generator",
  );
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [health, setHealth] = useState<Runtime | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [result, setResult] = useState<Generation | null>(null);
  const [tone, setTone] = useState<Tone>("persuasivo");
  const [confirmRegenerate, setConfirmRegenerate] = useState(false);
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
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 });
  }, [view]);
  useEffect(() => {
    let active = true;
    api<AuthUser>("/api/v1/auth/me")
      .then((user) => {
        if (active) setAccount(user);
      })
      .catch((error: unknown) => {
        if (!active) return;
        setAccount(null);
        if (error instanceof ApiError && error.status === 401) {
          setAuthError("");
        } else {
          setAuthError(
            error instanceof Error ? error.message : "Não foi possível verificar sua sessão.",
          );
        }
      })
      .finally(() => {
        if (active) setAuthLoading(false);
      });
    const handleUnauthorized = () => {
      setAccount(null);
      setAuthError("Sua sessão expirou. Entre novamente para continuar.");
    };
    window.addEventListener("copylab:unauthorized", handleUnauthorized);
    return () => {
      active = false;
      window.removeEventListener("copylab:unauthorized", handleUnauthorized);
    };
  }, []);
  useEffect(() => {
    if (!account) {
      setHealth(null);
      return;
    }
    Promise.all([
      api<Runtime>("/health"),
      api<{ configured: boolean; locked: boolean; provider: string; model: string }>(
        "/api/v1/settings/provider",
      ),
    ])
      .then(([runtime, provider]) =>
        setHealth({
          ...runtime,
          provider: provider.locked
            ? "unavailable"
            : provider.configured
              ? provider.provider
              : "mock",
          model: provider.configured ? provider.model : runtime.model,
        }),
      )
      .catch(() => setHealth(null));
  }, [account?.id, revision]);
  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(id);
  }, [toast]);
  async function logout() {
    try {
      await api<void>("/api/v1/auth/logout", { method: "POST" });
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Não foi possível encerrar a sessão.");
    } finally {
      setAccount(null);
      setProduct(null);
      setResult(null);
      setCatalog(null);
    }
  }
  useEffect(() => {
    if (!account) {
      setCatalog(null);
      setCatalogLoading(false);
      return;
    }
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
  }, [account?.id, query, offset, revision]);
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
  async function save(data: ProductInput) {
    setBusy(true);
    try {
      const saved = await api<Product>(
        product ? `/api/v1/products/${product.id}` : "/api/v1/products",
        { method: product ? "PUT" : "POST", body: JSON.stringify(data) },
      );
      setProduct(saved);
      setResult(null);
      setRevision((v) => v + 1);
      setView("catalog");
      setToast("Produto salvo no catálogo.");
    } finally {
      setBusy(false);
    }
  }
  async function createMockProducts() {
    setBusy(true);
    let created = 0;
    let alreadyPresent = 0;
    try {
      for (const sample of MOCK_PRODUCTS) {
        const existing = await api<Page<Product>>(
          `/api/v1/products?sku=${encodeURIComponent(sample.sku)}&limit=1`,
        );
        if (existing.total > 0) {
          alreadyPresent += 1;
          continue;
        }
        await api<Product>("/api/v1/products", {
          method: "POST",
          body: JSON.stringify(sample),
        });
        created += 1;
      }
      setQuery("");
      setOffset(0);
      setRevision((value) => value + 1);
      setToast(
        created
          ? `${created} produto${created === 1 ? "" : "s"} de exemplo adicionado${created === 1 ? "" : "s"}${alreadyPresent ? `; ${alreadyPresent} já existia${alreadyPresent === 1 ? "" : "m"}` : ""}.`
          : "Os produtos de exemplo já estão no catálogo.",
      );
    } catch (error) {
      if (created) {
        setQuery("");
        setOffset(0);
        setRevision((value) => value + 1);
      }
      setToast(
        created
          ? `${created} produto${created === 1 ? "" : "s"} ${created === 1 ? "foi adicionado" : "foram adicionados"} antes da falha: ${error instanceof Error ? error.message : "erro inesperado"}.`
          : error instanceof Error
            ? error.message
            : "Não foi possível criar os produtos de exemplo.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function generateCopy(forceRegenerate = false) {
    if (!product) return;
    setBusy(true);
    try {
      const generated = await api<Generation>("/api/v1/copies/generate", {
        method: "POST",
        body: JSON.stringify({
          product_id: product.id,
          tone_of_voice: tone,
          force_regenerate: forceRegenerate,
        }),
      });
      setResult(generated);
      setRevision((v) => v + 1);
      setToast(
        forceRegenerate
          ? "Nova versão gerada. A chamada pode gerar custos no provedor de IA."
          : generated.cache_status === "HIT"
            ? "Conteúdo recuperado do cache."
            : "Conteúdo gerado e salvo no histórico.",
      );
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Falha ao gerar conteúdo.");
    } finally {
      setBusy(false);
    }
  }
  async function saveCopyEdit(edits: CopyEdits) {
    if (!result) return;
    setBusy(true);
    try {
      const saved = await api<Copy>(`/api/v1/copies/${result.copy.id}/revisions`, {
        method: "POST",
        body: JSON.stringify(edits),
      });
      setResult({ copy: saved, cache_status: "MISS" });
      setRevision((value) => value + 1);
      setToast("Edição salva como uma nova versão do histórico.");
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
      setToast("Produto e textos removidos.");
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
  function editProduct(item: Product | null) {
    setProduct(item);
    setResult(null);
    setView("product");
  }
  const title =
    view === "generator"
      ? "Gerar textos"
      : view === "product"
        ? product
          ? "Editar produto"
          : "Cadastrar produto"
      : view === "catalog"
        ? "Catálogo de produtos"
        : view === "guide"
          ? "Como usar o CopyLab"
            : view === "metrics"
              ? "Resultados das requisições"
              : "Chaves de API";
  if (authLoading) {
    return (
      <main className="auth-loading" aria-label="Verificando sessão">
        <LoaderCircle className="spin" size={24} />
      </main>
    );
  }
  if (!account) {
    return (
      <Login
        onAuthenticated={(user) => {
          setAuthError("");
          setAccount(user);
        }}
        onAttempt={() => setAuthError("")}
        statusMessage={authError}
      />
    );
  }
  return (
    <div className={`app-shell${sidebarExpanded ? "" : " sidebar-collapsed"}`}>
      <aside className="sidebar">
        <div className="sidebar-brand-row">
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
          <button
            type="button"
            className="sidebar-toggle"
            aria-label={
              sidebarExpanded ? "Recolher barra lateral" : "Expandir barra lateral"
            }
            aria-controls="primary-navigation"
            aria-expanded={sidebarExpanded}
            title={sidebarExpanded ? "Recolher barra lateral" : "Expandir barra lateral"}
            onClick={() => setSidebarExpanded((expanded) => !expanded)}
          >
            {sidebarExpanded ? (
              <PanelLeftClose size={18} />
            ) : (
              <PanelLeftOpen size={18} />
            )}
          </button>
        </div>
        <div className="workspace">
          <span className="workspace-icon">M</span>
          <div>
            <strong>Laboratório de conteúdo</strong>
          </div>
          <ChevronRight size={15} />
        </div>
        <span className="nav-label">MENU</span>
        <nav id="primary-navigation">
          {(
            [
              { id: "generator", label: "Gerar textos", Icon: Sparkles },
              { id: "product", label: "Cadastrar produto", Icon: Plus },
              { id: "catalog", label: "Catálogo de produtos", Icon: Boxes },
              { id: "guide", label: "Como funciona", Icon: FileText },
              {
                id: "metrics",
                label: "Métricas de engenharia",
                Icon: LayoutDashboard,
              },
              { id: "settings", label: "Chaves de API", Icon: Settings2 },
            ] as const
          ).map((item) => (
            <button
              disabled={busy}
              key={item.id}
              className={view === item.id ? "selected" : ""}
              aria-label={item.label}
              title={item.label}
              onClick={() =>
                item.id === "product" ? editProduct(null) : setView(item.id)
              }
            >
              <item.Icon size={19} />
              <span className="nav-item-label">{item.label}</span>
              {view === item.id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            CopyLab <ChevronRight size={14} />
            <strong>
              {view === "generator"
                ? "Gerar textos"
                : view === "product"
                  ? "Produto"
                : view === "catalog"
                  ? "Catálogo"
                  : view === "guide"
                    ? "Como funciona"
                    : view === "metrics"
                      ? "Métricas de engenharia"
                      : "Chaves de API"}
            </strong>
          </div>
          <div>
            <span className="account-email">{account.email}</span>
            <button type="button" className="logout-button" onClick={logout}>
              <LogOut size={16} />
              Sair
            </button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                {view === "generator"
                  ? "Criação de conteúdo"
                  : view === "product"
                    ? "Cadastro de produto"
                  : view === "catalog"
                    ? "Sua base de produtos"
                    : view === "guide"
                      ? "Tour da aplicação"
                      : view === "metrics"
                        ? "Desempenho do sistema"
                        : "Configurações de segurança"}
              </span>
              <h1>{title}</h1>
              <p>
                {view === "generator"
                  ? "Escolha um produto do catálogo, defina o estilo do texto e gere conteúdo para seus canais."
                  : view === "product"
                    ? "Cadastre ou atualize os dados do produto. A geração de conteúdo acontece em uma página separada."
                  : view === "catalog"
                    ? "Busque um produto para editar seus dados, gerar textos ou consultar versões anteriores."
                    : view === "guide"
                      ? "Veja por onde começar e faça um teste com um produto de exemplo."
                      : view === "metrics"
                        ? "Acompanhe desempenho, reaproveitamento e consumo da aplicação."
                        : "Configure ou substitua a chave do seu provedor de IA com segurança."}
              </p>
            </div>
            <span className="version-tag">
              CopyLab <span>v2.0</span>
            </span>
          </div>
          {view === "generator" && (
            <>
              <div className="flow-strip">
                <span className="flow-step">
                  <b>1</b> Escolha o produto
                </span>
                <ChevronRight size={14} />
                <span className="flow-step">
                  <b>2</b> Defina o estilo de texto
                </span>
                <ChevronRight size={14} />
                <span className="flow-step">
                  <b>3</b> Gere os textos
                </span>
                <span className="flow-end"><CheckCircle2 size={14} /> Instagram · WhatsApp · E-commerce</span>
              </div>
              <div className="studio-grid">
                <div>
                  <section className="panel generation-controls">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">PRODUTO PARA ESTA GERAÇÃO</span>
                        <h2>{product ? product.name : "Nenhum produto selecionado"}</h2>
                      </div>
                    </div>
                    {product ? (
                      <div className="selected-product-details">
                        <span className="badge">{product.category}</span>
                        <span>SKU: {product.sku}</span>
                        <button className="button secondary" onClick={() => setView("catalog")}>
                          Trocar produto
                        </button>
                      </div>
                    ) : (
                      <div className="generation-no-product">
                        <p>Para começar, escolha um produto cadastrado ou crie um novo.</p>
                        <div className="form-actions">
                          <button className="button secondary" onClick={() => setView("catalog")}>
                            <Boxes size={16} /> Abrir catálogo
                          </button>
                          <button className="button primary" onClick={() => editProduct(null)}>
                            <Plus size={16} /> Cadastrar produto
                          </button>
                        </div>
                      </div>
                    )}
                    {product && (
                      <fieldset className="generation-tone" disabled={busy}>
                        <legend className="eyebrow">ESTILO DO TEXTO</legend>
                        <div className="tone-grid">
                          {(["persuasivo", "descontraído", "institucional", "promocional"] as Tone[]).map((option) => (
                            <label
                              className={`tone-option ${tone === option ? "selected" : ""}`}
                              key={option}
                            >
                              <input
                                type="radio"
                                name="generation-tone"
                                value={option}
                                checked={tone === option}
                                onChange={() => setTone(option)}
                              />
                              {option}
                            </label>
                          ))}
                        </div>
                        <p className="field-explanation" aria-live="polite">
                          {{
                            persuasivo: "Destaca os benefícios para incentivar a compra.",
                            descontraído: "Usa uma linguagem informal e próxima do leitor.",
                            institucional: "Apresenta o produto de forma objetiva e formal.",
                            promocional: "Dá destaque à oferta, sem inventar preços ou descontos.",
                          }[tone]}
                        </p>
                        <button
                          type="button"
                          className="button primary"
                          disabled={busy}
                          onClick={() => void generateCopy()}
                        >
                          {busy ? <LoaderCircle size={18} className="spin" /> : <Sparkles size={17} />}
                          {busy ? "Gerando textos…" : "Gerar textos"}
                        </button>
                      </fieldset>
                    )}
                  </section>
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
                      <Previews
                        copy={result.copy}
                        notify={setToast}
                        onSaveEdit={saveCopyEdit}
                        onRegenerate={() => setConfirmRegenerate(true)}
                      />
                      <div className="hash-card">
                        <DatabaseBadge status={result.cache_status} />
                        <code>{result.copy.input_hash}</code>
                        <small>
                          Este código identifica os dados usados na geração.
                          Alterar o produto ou o tom muda o código.
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
                          ? "Gerando os textos…"
                          : "Os textos aparecerão aqui"}
                      </h2>
                      <p>
                        {busy
                          ? "Aguarde a resposta. Os textos serão salvos no histórico do produto."
                          : product
                            ? "Defina o estilo do texto e gere o conteúdo. Depois, selecione o canal para ler e copiar."
                            : "Escolha um produto no catálogo para começar a gerar conteúdo."}
                      </p>
                      {busy && <LoaderCircle className="spin" size={24} />}
                      <div className="channel-pills">
                        <span>Instagram</span>
                        <span>WhatsApp</span>
                        <span>E-commerce</span>
                      </div>
                      <div className="empty-bottom">
                        <CheckCircle2 size={16} /> Revise os textos antes de
                        usá-los nos seus canais.
                      </div>
                    </section>
                  )}
                  <div className="editorial-note">
                    <span>↗</span>
                    <div>
                      <strong>O que informar no cadastro</strong>
                      <p>
                        Informe características que você possa confirmar, como
                        material, tamanho e autonomia. Evite vantagens que o
                        produto não oferece.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
          {view === "product" && (
            <div className="product-page">
              <ProductForm
                product={product}
                busy={busy}
                onSave={save}
                onClear={() => setProduct(null)}
              />
            </div>
          )}
          {view === "catalog" && (
            <>
              <div className="section-toolbar">
                <label className="search-field">
                  <Search size={17} />
                  <input
                    aria-label="Buscar nome ou SKU"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setOffset(0);
                    }}
                  />
                </label>
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={() => editProduct(null)}
                >
                  <Plus size={17} /> Novo produto
                </button>
                {health?.provider === "mock" && (
                  <button
                    className="button secondary"
                    disabled={busy}
                    onClick={createMockProducts}
                    title="Adiciona produtos de exemplo à sua conta sem chamar um provedor de IA"
                  >
                    {busy ? <LoaderCircle size={16} className="spin" /> : <Sparkles size={16} />}
                    {busy ? "Criando exemplos…" : "Criar produtos de exemplo"}
                  </button>
                )}
              </div>
              {health?.provider === "mock" && (
                <p className="mock-products-note">
                  Os exemplos ficam salvos no catálogo da sua conta. A geração usa o simulador e não chama um provedor pago.
                </p>
              )}
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
                      Gerar textos <ArrowUpRight size={16} />
                    </button>
                    <button className="button catalog-edit" onClick={() => editProduct(item)}>
                      Editar produto
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
                      : "Cadastre um produto ou execute o script de carga."}
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
          {view === "guide" && (
            <Guide
              runtime={health}
              onBusy={setBusy}
              onProduct={selectProduct}
            />
          )}
          {view === "metrics" && (
            <Suspense fallback={<p role="status">Carregando métricas…</p>}>
              <Dashboard key={revision} />
            </Suspense>
          )}
          {view === "settings" && (
            <ProviderSettings onSaved={() => setRevision((value) => value + 1)} />
          )}
          <footer className="page-footer">
            <span>
              CopyLab · Automação de conteúdo para o varejo eletrônico
            </span>
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
              O produto e seus textos serão excluídos permanentemente. A
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
      {confirmRegenerate && (
        <div className="modal-backdrop">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="regenerate-title"
            aria-describedby="regenerate-description"
            className="panel modal regenerate-modal"
          >
            <h2 id="regenerate-title">Gerar uma nova versão?</h2>
            <p id="regenerate-description">
              Vamos solicitar novos textos para Instagram, WhatsApp e E-commerce
              com o estilo selecionado. Essa ação ignora o cache.
            </p>
            <p className="regenerate-warning">
              Uma chamada a um provedor de IA pode consumir créditos e gerar
              cobrança conforme o modelo e o plano contratado. No modo simulado,
              não há custo.
            </p>
            <div className="form-actions">
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => setConfirmRegenerate(false)}
              >
                Cancelar
              </button>
              <button
                className="button primary"
                disabled={busy}
                onClick={() => {
                  setConfirmRegenerate(false);
                  void generateCopy(true);
                }}
              >
                {busy ? "Gerando…" : "Confirmar e gerar"}
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
