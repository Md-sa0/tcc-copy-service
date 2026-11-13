import {
  KeyRound,
  LoaderCircle,
  LockKeyhole,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "./api";

interface ProviderStatus {
  configured: boolean;
  locked: boolean;
  provider: string;
  model: string;
  base_url: string | null;
  error: string | null;
}

export default function ProviderSettings({
  onSaved,
}: {
  onSaved: () => void;
}) {
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("https://api.openai.com/v1");
  const [model, setModel] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  async function refresh() {
    const current = await api<ProviderStatus>("/api/v1/settings/provider");
    setStatus(current);
    if (current.configured) {
      if (current.base_url) setBaseUrl(current.base_url);
      setModel(current.model);
    }
  }

  useEffect(() => {
    refresh().catch((e: unknown) =>
      setError(e instanceof Error ? e.message : "Não foi possível carregar as configurações."),
    );
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setSaved(false);
    try {
      const current = await api<ProviderStatus>("/api/v1/settings/provider", {
        method: "PUT",
        body: JSON.stringify({ api_key: apiKey, base_url: baseUrl, model }),
      });
      setStatus(current);
      setApiKey("");
      setSaved(true);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar a chave.");
    } finally {
      setBusy(false);
    }
  }

  async function removeKey() {
    if (
      !window.confirm(
        "Excluir a chave salva? A geração deixará de usar esse provedor até uma nova chave ser configurada.",
      )
    ) {
      return;
    }

    setBusy(true);
    setError("");
    setSaved(false);
    try {
      const current = await api<ProviderStatus>("/api/v1/settings/provider", {
        method: "DELETE",
      });
      setStatus(current);
      setApiKey("");
      setBaseUrl("https://api.openai.com/v1");
      setModel("");
      setSaved(true);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível excluir a chave.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="provider-settings">
      <section className="panel settings-status">
        <div className="settings-status-icon">
          {status?.configured ? <ShieldCheck size={21} /> : <KeyRound size={21} />}
        </div>
        <div>
          <span className="eyebrow">PROVEDOR DE INFERÊNCIA</span>
          <h2>
            {status?.locked
              ? "A chave salva não pode ser recuperada"
              : status?.configured
                ? "Uma chave está configurada"
                : "Configure sua chave de IA"}
          </h2>
          <p>
            {status?.configured
              ? `Provedor atual: ${status.provider} · Modelo: ${status.model}`
              : "Informe uma chave obtida por você em um provedor compatível com a API OpenAI."}
          </p>
          {status?.locked && status.error && (
            <p className="settings-error" role="alert">{status.error}</p>
          )}
        </div>
        <span className={`settings-status-pill ${status?.configured ? "is-configured" : ""}`}>
          <i /> {status?.configured ? "Configurada" : "Pendente"}
        </span>
      </section>

      <form className="panel provider-form" onSubmit={submit}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">ACESSO DO PROVEDOR</span>
            <h2>{status?.configured ? "Trocar chave da API" : "Adicionar chave de API"}</h2>
          </div>
          <LockKeyhole size={19} />
        </div>
        <div className="provider-form-body">
          <div className="settings-security-note">
            <ShieldCheck size={18} />
            <p>
              A chave nova substitui a configuração atual ao ser salva. Ela é
              armazenada criptografada e nunca volta para o navegador.
            </p>
          </div>
          <label>
            Chave de API
            <input
              type="password"
              name="provider-api-key"
              autoComplete="new-password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              required
              maxLength={4096}
            />
            <small>Apenas provedores compatíveis com OpenAI Chat Completions.</small>
          </label>
          <label>
            URL base do endpoint
            <input
              type="url"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              required
              maxLength={500}
            />
            <small>Use a URL HTTPS indicada pelo seu provedor.</small>
          </label>
          <label>
            Identificador do modelo
            <input
              value={model}
              onChange={(event) => setModel(event.target.value)}
              required
              maxLength={200}
            />
          </label>
          {error && <div className="error-box" role="alert">{error}</div>}
          {saved && (
            <div className="success-box" role="status">
              {status?.configured
                ? "Nova chave salva e configuração atualizada."
                : "Chave removida. A geração usará a configuração padrão até uma nova chave ser salva."}
            </div>
          )}
          <div className="provider-form-footer">
            <div className="provider-actions">
              {(status?.configured || status?.locked) && (
                <button
                  className="button danger"
                  type="button"
                  disabled={busy}
                  onClick={() => void removeKey()}
                >
                  {busy ? (
                    <LoaderCircle size={16} className="spin" />
                  ) : (
                    <Trash2 size={16} />
                  )}
                  Excluir chave salva
                </button>
              )}
              <button
                className="button primary"
                type="submit"
                disabled={busy || !apiKey.trim()}
              >
                {busy ? (
                  <LoaderCircle size={16} className="spin" />
                ) : (
                  <KeyRound size={16} />
                )}
                {busy
                  ? "Salvando…"
                  : status?.configured
                    ? "Trocar chave"
                    : "Salvar chave"}
              </button>
            </div>
          </div>
        </div>
      </form>

    </div>
  );
}
