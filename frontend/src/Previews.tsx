import {
  Check,
  Copy as CopyIcon,
  Heart,
  MessageCircle,
  MoreHorizontal,
  Send,
} from "lucide-react";
import { useState } from "react";
import type { Copy } from "./types";

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
}: {
  copy: Copy;
  notify: (message: string) => void;
}) {
  const [tab, setTab] = useState<"instagram" | "whatsapp" | "seo">("instagram");
  const [copied, setCopied] = useState(false);
  const ig = copy.instagram_copy,
    wa = copy.whatsapp_copy,
    seo = copy.seo_copy;
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
          <span className="eyebrow">SAÍDA ESTRUTURADA</span>
          <h2>Pronto para cada canal</h2>
        </div>
        <span className="badge green">Validado</span>
      </div>
      <div className="tabs" role="tablist" aria-label="Canais de marketing">
        {(["instagram", "whatsapp", "seo"] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={t === tab}
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
      <div className="preview-stage" role="tabpanel">
        {tab === "instagram" && (
          <article className="instagram-card">
            <div className="social-head">
              <div className="avatar">c.</div>
              <div>
                <strong>sua.marca</strong>
                <small>Conteúdo para o seu próximo post</small>
              </div>
              <MoreHorizontal size={19} />
            </div>
            <div className="product-art">
              <span className="art-orbit" />
              <span className="art-label">EM DESTAQUE</span>
              <h3>{copy.input_snapshot.product.name}</h3>
              <span className="art-caption">
                Uma nova história começa aqui.
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
        )}
        {tab === "whatsapp" && (
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
        )}
        {tab === "seo" && (
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
            Tom {copy.tone_of_voice} · {copy.tokens_used} tokens
          </small>
        </span>
        <button className="button secondary" onClick={clipboard}>
          {copied ? <Check size={16} /> : <CopyIcon size={16} />}{" "}
          {copied ? "Copiado" : "Copiar texto"}
        </button>
      </div>
    </section>
  );
}
