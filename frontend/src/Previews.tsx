import {
  Check,
  Copy as CopyIcon,
  Pencil,
  Heart,
  MessageCircle,
  MoreHorizontal,
  RefreshCw,
  Send,
  X,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import type { Copy, CopyEdits } from "./types";

function WhatsAppText({ value }: { value: string }) {
  return (
    <>
      {value
        .split(/(\*[^*]+\*)/g)
        .map((part, i) =>
          part.startsWith("*") && part.endsWith("*") ? (
            <strong key={i}>{part.slice(1, -1)}</strong>
          ) : (
            part
          ),
        )}
    </>
  );
}

export default function Previews({
  copy,
  notify,
  onSaveEdit,
  onRegenerate,
}: {
  copy: Copy;
  notify: (message: string) => void;
  onSaveEdit: (edits: CopyEdits) => Promise<void>;
  onRegenerate: () => void;
}) {
  const [tab, setTab] = useState<"instagram" | "whatsapp" | "seo">("instagram");
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<CopyEdits>(() => ({
    instagram_copy: { ...copy.instagram_copy, hashtags: [...copy.instagram_copy.hashtags] },
    whatsapp_copy: { ...copy.whatsapp_copy },
    seo_copy: { ...copy.seo_copy, bullet_points: [...copy.seo_copy.bullet_points] },
  }));
  useEffect(() => {
    setEditing(false);
    setDraft({
      instagram_copy: { ...copy.instagram_copy, hashtags: [...copy.instagram_copy.hashtags] },
      whatsapp_copy: { ...copy.whatsapp_copy },
      seo_copy: { ...copy.seo_copy, bullet_points: [...copy.seo_copy.bullet_points] },
    });
  }, [copy.id]);
  const ig = copy.instagram_copy,
    wa = copy.whatsapp_copy,
    seo = copy.seo_copy;
  function changeInstagram<K extends keyof CopyEdits["instagram_copy"]>(
    key: K,
    value: CopyEdits["instagram_copy"][K],
  ) {
    setDraft((current) => ({
      ...current,
      instagram_copy: { ...current.instagram_copy, [key]: value },
    }));
  }
  function changeWhatsApp<K extends keyof CopyEdits["whatsapp_copy"]>(
    key: K,
    value: CopyEdits["whatsapp_copy"][K],
  ) {
    setDraft((current) => ({
      ...current,
      whatsapp_copy: { ...current.whatsapp_copy, [key]: value },
    }));
  }
  function changeSeo<K extends keyof CopyEdits["seo_copy"]>(
    key: K,
    value: CopyEdits["seo_copy"][K],
  ) {
    setDraft((current) => ({
      ...current,
      seo_copy: { ...current.seo_copy, [key]: value },
    }));
  }
  async function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    try {
      await onSaveEdit(draft);
      setEditing(false);
    } catch (error) {
      notify(error instanceof Error ? error.message : "Não foi possível salvar a edição.");
    } finally {
      setSaving(false);
    }
  }
  async function clipboard() {
    const text =
      tab === "instagram"
        ? `${ig.hook}\n\n${ig.caption}\n\n${ig.call_to_action}\n${ig.hashtags.join(" ")}`
        : tab === "whatsapp"
          ? `${wa.message}\n\n${wa.call_to_action}`
          : `${seo.meta_title}\n${seo.meta_description}\n\n${seo.bullet_points.join("\n")}\n\n${seo.long_description}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      notify("Conteúdo copiado para a área de transferência.");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      notify(
        "Não foi possível copiar. Verifique a permissão de área de transferência do navegador.",
      );
    }
  }
  return (
    <section className="panel preview-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Textos gerados</span>
          <h2>Textos por canal</h2>
        </div>
        <span className="badge green">Formato conferido</span>
      </div>
      <div className="tabs" role="tablist" aria-label="Canais de marketing">
        {(["instagram", "whatsapp", "seo"] as const).map((t) => (
          <button
            key={t}
            role="tab"
            id={`preview-tab-${t}`}
            aria-controls="preview-panel-content"
            aria-selected={t === tab}
            disabled={editing}
            onClick={() => setTab(t)}
            className={tab === t ? "active" : ""}
          >
            {t === "seo"
              ? "E-commerce / SEO"
              : t === "instagram"
                ? "Instagram"
                : "WhatsApp"}
          </button>
        ))}
      </div>
      <div
        className={`preview-stage preview-stage-${tab}`}
        id="preview-panel-content"
        role="tabpanel"
        aria-labelledby={`preview-tab-${tab}`}
      >
        {editing ? (
          <form className="copy-edit-form" onSubmit={saveEdit}>
            <div className="copy-edit-heading">
              <div>
                <span className="eyebrow">EDIÇÃO DE TEXTO</span>
                <h3>
                  {tab === "seo"
                    ? "E-commerce / SEO"
                    : tab === "instagram"
                      ? "Instagram"
                      : "WhatsApp"}
                </h3>
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label="Cancelar edição"
                onClick={() => setEditing(false)}
              >
                <X size={18} />
              </button>
            </div>
            {tab === "instagram" && (
              <>
                <label>
                  Chamada inicial
                  <input
                    value={draft.instagram_copy.hook}
                    maxLength={500}
                    required
                    onChange={(event) => changeInstagram("hook", event.target.value)}
                  />
                </label>
                <label>
                  Legenda
                  <textarea
                    value={draft.instagram_copy.caption}
                    maxLength={2200}
                    required
                    rows={6}
                    onChange={(event) => changeInstagram("caption", event.target.value)}
                  />
                </label>
                <label>
                  Chamada para ação
                  <input
                    value={draft.instagram_copy.call_to_action}
                    maxLength={500}
                    required
                    onChange={(event) =>
                      changeInstagram("call_to_action", event.target.value)
                    }
                  />
                </label>
                <label>
                  Hashtags (uma por linha, com #)
                  <textarea
                    value={draft.instagram_copy.hashtags.join("\n")}
                    required
                    rows={3}
                    onChange={(event) =>
                      changeInstagram(
                        "hashtags",
                        event.target.value.split("\n").map((value) => value.trim()),
                      )
                    }
                  />
                </label>
              </>
            )}
            {tab === "whatsapp" && (
              <>
                <label>
                  Mensagem
                  <textarea
                    value={draft.whatsapp_copy.message}
                    maxLength={4096}
                    required
                    rows={8}
                    onChange={(event) => changeWhatsApp("message", event.target.value)}
                  />
                </label>
                <label>
                  Chamada para ação
                  <input
                    value={draft.whatsapp_copy.call_to_action}
                    maxLength={500}
                    required
                    onChange={(event) =>
                      changeWhatsApp("call_to_action", event.target.value)
                    }
                  />
                </label>
              </>
            )}
            {tab === "seo" && (
              <>
                <label>
                  Título SEO (até 60 caracteres)
                  <input
                    value={draft.seo_copy.meta_title}
                    maxLength={60}
                    required
                    onChange={(event) => changeSeo("meta_title", event.target.value)}
                  />
                </label>
                <label>
                  Descrição SEO (até 160 caracteres)
                  <textarea
                    value={draft.seo_copy.meta_description}
                    maxLength={160}
                    required
                    rows={3}
                    onChange={(event) =>
                      changeSeo("meta_description", event.target.value)
                    }
                  />
                </label>
                <label>
                  Destaques (um por linha)
                  <textarea
                    value={draft.seo_copy.bullet_points.join("\n")}
                    required
                    rows={4}
                    onChange={(event) =>
                      changeSeo(
                        "bullet_points",
                        event.target.value.split("\n").map((value) => value.trim()),
                      )
                    }
                  />
                </label>
                <label>
                  Descrição do produto
                  <textarea
                    value={draft.seo_copy.long_description}
                    maxLength={5000}
                    required
                    rows={8}
                    onChange={(event) =>
                      changeSeo("long_description", event.target.value)
                    }
                  />
                </label>
              </>
            )}
            <div className="form-actions">
              <button
                type="button"
                className="button secondary"
                disabled={saving}
                onClick={() => setEditing(false)}
              >
                Cancelar
              </button>
              <button type="submit" className="button primary" disabled={saving}>
                {saving ? "Salvando…" : "Salvar nova versão"}
              </button>
            </div>
            <p className="copy-edit-note">
              A edição cria uma versão no histórico e preserva a original.
            </p>
          </form>
        ) : tab === "instagram" ? (
          <article className="instagram-card">
            <div className="social-head">
              <div className="avatar">c.</div>
              <div>
                <strong>sua.marca</strong>
                <small>Prévia de publicação</small>
              </div>
              <MoreHorizontal size={19} />
            </div>
            <div className="product-art">
              <span className="art-orbit" />
              <span className="art-label">EM DESTAQUE</span>
              <h3>{copy.input_snapshot.product.name}</h3>
              <span className="art-caption">
                Ilustração da prévia; não é uma foto do produto.
              </span>
              <div className="art-mark">c.</div>
            </div>
            <div className="social-body">
              <div className="social-actions">
                <Heart />
                <MessageCircle />
                <Send />
              </div>
              <strong>{ig.hook}</strong>
              <p className="whitespace-pre-wrap">{ig.caption}</p>
              <p>{ig.call_to_action}</p>
              <p className="hashtags">{ig.hashtags.join(" ")}</p>
            </div>
          </article>
        ) : tab === "whatsapp" ? (
          <article className="whatsapp-card">
            <div className="wa-head">
              <div className="avatar">c.</div>
              <div>
                <strong>Sua marca</strong>
                <small>Prévia de mensagem</small>
              </div>
            </div>
            <div className="wa-chat">
              <span className="wa-date">HOJE</span>
              <div className="wa-bubble">
                <p className="whitespace-pre-wrap">
                  <WhatsAppText value={wa.message} />
                </p>
                <p>{wa.call_to_action}</p>
                <small>Agora · ✓✓</small>
              </div>
            </div>
          </article>
        ) : (
          <article className="seo-card">
            <span className="eyebrow">PRÉVIA NA BUSCA</span>
            <p className="search-site">
              Sua loja{" "}
              <span>
                loja.exemplo / produtos /{" "}
                {copy.input_snapshot.product.sku.toLowerCase()}
              </span>
            </p>
            <a className="seo-title" href="#descricao-produto">
              {seo.meta_title}
            </a>
            <p>{seo.meta_description}</p>
            <div className="seo-limits">
              <span>Título {seo.meta_title.length}/60</span>
              <span>Descrição {seo.meta_description.length}/160</span>
            </div>
            <hr />
            <h3 id="descricao-produto">Descrição do produto</h3>
            <ul>
              {seo.bullet_points.map((v) => (
                <li key={v}>{v}</li>
              ))}
            </ul>
            <p className="whitespace-pre-wrap">{seo.long_description}</p>
          </article>
        )}
      </div>
      <div className="preview-footer">
        <span>
          {copy.model_name}
          <small>
            Estilo {copy.tone_of_voice} · {copy.tokens_used} tokens
          </small>
        </span>
        {!editing && (
          <div className="preview-actions">
            <button
              className="button secondary"
              onClick={() => setEditing(true)}
            >
              <Pencil size={15} /> Editar texto
            </button>
            <button
              className="button secondary"
              onClick={onRegenerate}
            >
              <RefreshCw size={15} /> Gerar nova versão
            </button>
            <button className="button secondary" onClick={clipboard}>
              {copied ? <Check size={16} /> : <CopyIcon size={16} />}{" "}
              {copied ? "Copiado" : "Copiar texto"}
            </button>
          </div>
        )}
      </div>
      <p className="regenerate-cost-note">
        Gerar nova versão pode consumir créditos do provedor de IA.
      </p>
    </section>
  );
}
