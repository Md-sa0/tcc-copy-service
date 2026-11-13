import { LoaderCircle, Save, X } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { ZodError } from "zod";
import {
  formatProductValidationError,
  parseAttributes,
  productSchema,
} from "./validation";
import type { Product, ProductInput } from "./types";

interface Props {
  product: Product | null;
  busy: boolean;
  onSave: (product: ProductInput) => Promise<void>;
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
      await onSave(data);
    } catch (e) {
      setError(
        e instanceof ZodError
          ? formatProductValidationError(e)
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
    <form className="panel product-form" onSubmit={submit} noValidate>
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Informações do produto</span>
          <h2>{product ? "Editar produto" : "Cadastrar produto"}</h2>
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
              aria-label="SKU"
              {...field("sku")}
            />
            <small>Código único escolhido por você, como FONE-001.</small>
          </label>
          <label>
            Categoria{" "}
            <input
              required
              minLength={2}
              maxLength={100}
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
            {...field("name")}
          />
        </label>
        <label>
          Público-alvo{" "}
          <input
            required
            minLength={3}
            maxLength={500}
            {...field("target_audience")}
          />
        </label>
        <label>
          Atributos técnicos{" "}
          <textarea
            required
            rows={3}
            {...field("attributes")}
          />
          <small>
            Escreva uma característica por linha, como Material: algodão. Até 30
            características.
          </small>
        </label>
        <label>
          Benefícios comprovados{" "}
          <textarea
            required
            rows={3}
            {...field("benefits")}
          />
          <small>
            Um benefício por linha. Use apenas informações verificadas.
          </small>
        </label>
        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}
        <div className="form-actions">
          <button
            type="submit"
            className="button primary"
            disabled={busy}
          >
            {busy ? <LoaderCircle size={18} className="spin" /> : <Save size={16} />}
            {busy ? "Salvando…" : "Salvar produto"}
          </button>
        </div>
      </fieldset>
      <p className="form-note">
        O cadastro do produto é independente da geração de textos. Depois de
        salvar, escolha o produto no catálogo para criar conteúdo.
      </p>
    </form>
  );
}
