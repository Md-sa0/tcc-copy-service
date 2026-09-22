import { ArrowRight, LoaderCircle, Save, X } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { ZodError } from "zod";
import { parseAttributes, productSchema } from "./validation";
import type { Product, ProductInput, Tone } from "./types";

interface Props {
  product: Product | null;
  busy: boolean;
  onSave: (
    product: ProductInput,
    tone: Tone,
    generate: boolean,
  ) => Promise<void>;
  onClear: () => void;
}
const initial = {
  sku: "",
  name: "",
  category: "",
  target_audience: "",
  attributes: "",
  benefits: "",
};

export default function ProductForm({ product, busy, onSave, onClear }: Props) {
  const [form, setForm] = useState(initial);
  const [tone, setTone] = useState<Tone>("persuasivo");
  const [error, setError] = useState("");
  useEffect(() => {
    setForm(
      product
        ? {
            sku: product.sku,
            name: product.name,
            category: product.category,
            target_audience: product.target_audience,
            attributes: Object.entries(product.technical_attributes)
              .map(([k, v]) => `${k}: ${v}`)
              .join("\n"),
            benefits: product.key_benefits.join("\n"),
          }
        : initial,
    );
    setError("");
  }, [product]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      const { attributes, benefits, ...fields } = form;
      const data = productSchema.parse({
        ...fields,
        technical_attributes: parseAttributes(attributes),
        key_benefits: benefits.split("\n").filter((v) => v.trim()),
      });
      const generate =
        (event.nativeEvent as SubmitEvent).submitter?.getAttribute("value") !==
        "save";
      await onSave(data, tone, generate);
    } catch (e) {
      setError(
        e instanceof ZodError
          ? e.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join(" · ")
          : e instanceof Error
            ? e.message
            : "Falha ao salvar produto.",
      );
    }
  }
  function field(key: keyof typeof initial) {
    return {
      value: form[key],
      onChange: (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
      ) => setForm({ ...form, [key]: e.target.value }),
    };
  }
  return (
    <form className="panel product-form" onSubmit={submit}>
      <div className="panel-heading">
        <div>
          <span className="eyebrow">01 / INFORMAÇÕES DO PRODUTO</span>
          <h2>{product ? "Editar produto" : "O que vamos divulgar?"}</h2>
        </div>
        {product && (
          <button
            type="button"
            title="Novo produto"
            aria-label="Limpar seleção"
            className="icon-button"
            disabled={busy}
            onClick={onClear}
          >
            <X size={19} />
          </button>
        )}
      </div>
      <fieldset disabled={busy}>
        <div className="form-row">
          <label>
            SKU{" "}
            <input
              required
              maxLength={64}
              placeholder="FONE-001"
              {...field("sku")}
            />
          </label>
          <label>
            Categoria{" "}
            <input
              required
              minLength={2}
              maxLength={100}
              placeholder="Eletrônicos"
              {...field("category")}
            />
          </label>
        </div>
        <label>
          Nome do produto{" "}
          <input
            required
            minLength={2}
            maxLength={200}
            placeholder="Ex.: Fone Bluetooth Aura"
            {...field("name")}
          />
        </label>
        <label>
          Público-alvo{" "}
          <input
            required
            minLength={3}
            maxLength={500}
            placeholder="Para quem é esse produto?"
            {...field("target_audience")}
          />
        </label>
        <label>
          Atributos técnicos{" "}
          <textarea
            required
            rows={3}
            placeholder={"Conectividade: Bluetooth 5.3\nAutonomia: 24 horas"}
            {...field("attributes")}
          />
          <small>Um atributo: valor por linha. Até 30 atributos.</small>
        </label>
        <label>
          Benefícios comprovados{" "}
          <textarea
            required
            rows={3}
            placeholder={
              "Liberdade para ouvir sem fios\nConforto para a rotina"
            }
            {...field("benefits")}
          />
          <small>
            Um benefício por linha. Use apenas informações verificadas.
          </small>
        </label>
        <div className="tone-heading">
          <span className="eyebrow">02 / PERSONALIDADE DA MENSAGEM</span>
          <span>Tom de voz</span>
        </div>
        <div className="tone-grid">
          {(
            [
              "persuasivo",
              "descontraído",
              "institucional",
              "promocional",
            ] as Tone[]
          ).map((t) => (
            <label
              className={`tone-option ${tone === t ? "selected" : ""}`}
              key={t}
            >
              <input
                type="radio"
                name="tone"
                value={t}
                checked={tone === t}
                onChange={() => setTone(t)}
              />
              {t}
            </label>
          ))}
        </div>
        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}
        <div className="form-actions">
          <button
            type="submit"
            value="save"
            className="button secondary"
            title="Salvar sem gerar"
          >
            <Save size={16} /> Salvar
          </button>
          <button type="submit" value="generate" className="button primary">
            {busy ? (
              <LoaderCircle size={18} className="spin" />
            ) : (
              <ArrowRight size={18} />
            )}{" "}
            {busy ? "Processando…" : "Gerar conteúdo"}
          </button>
        </div>
      </fieldset>
      <p className="form-note">
        Validação estrita · Saída JSON estruturada · Cache SHA-256
      </p>
    </form>
  );
}
