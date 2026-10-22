import { useState } from "react";
import { api, ApiError } from "./api";
import type { Generation, Product } from "./types";

export interface Runtime {
  provider: string;
  model: string;
  database: string;
  cache: string;
}
interface Observation {
  step: string;
  passed: boolean;
  status: number;
  cache: string;
  client_latency_ms: number;
  input_hash?: string;
  copy_id?: string;
}
interface Report {
  started_at: string;
  runtime: Runtime;
  product_id: string;
  observations: Observation[];
}

export default function Guide({
  runtime,
  onBusy,
  onProduct,
}: {
  runtime: Runtime | null;
  onBusy: (value: boolean) => void;
  onProduct: (product: Product) => void;
}) {
  const [running, setRunning] = useState(false);
  const [report, setReport] = useState<Report | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState("");
  async function demonstrate() {
    if (!runtime || runtime.provider !== "mock") return;
    setRunning(true);
    onBusy(true);
    setError("");
    setReport(null);
    setProduct(null);
    const current: Report = {
      started_at: new Date().toISOString(),
      runtime,
      product_id: "",
      observations: [],
    };
    const add = (row: Observation) => {
      current.observations.push(row);
      setReport({ ...current, observations: [...current.observations] });
    };
    try {
      // Check again before mutations; never intentionally run the tour against a paid provider.
      const fresh = await api<Runtime>("/health");
      if (fresh.provider !== "mock")
        throw new Error(
          "Esta demonstração automática exige modo mock. Use o estúdio para inferência real.",
        );
      current.runtime = fresh;
      const saved = await api<Product>("/api/v1/products", {
        method: "POST",
        body: JSON.stringify({
          sku: `GUIA-${crypto.randomUUID()}`,
          name: "Fone Bluetooth Aura · Demonstração",
          category: "Eletrônicos",
          target_audience: "Estudantes e profissionais",
          technical_attributes: {
            conectividade: "Bluetooth 5.3",
            autonomia: "24 horas",
          },
          key_benefits: ["Uso sem fios", "Estojo para transporte"],
        }),
      });
      current.product_id = saved.id;
      setProduct(saved);
      const invalidStart = performance.now();
      try {
        await api("/api/v1/copies/generate", { method: "POST", body: "{}" });
        add({
          step: "Dados incompletos são rejeitados",
          passed: false,
          status: 200,
          cache: "—",
          client_latency_ms: performance.now() - invalidStart,
        });
      } catch (e) {
        if (!(e instanceof ApiError)) throw e;
        add({
          step: "Dados incompletos são rejeitados",
          passed: e.status === 422,
          status: e.status,
          cache: e.cacheStatus ?? "Não informado",
          client_latency_ms: performance.now() - invalidStart,
        });
        if (e.status !== 422) throw e;
      }
      let original: Generation | null = null;
      for (const [index, tone] of [
        "persuasivo",
        "persuasivo",
        "institucional",
      ].entries()) {
        const start = performance.now();
        const response = await api<Generation>("/api/v1/copies/generate", {
          method: "POST",
          body: JSON.stringify({ product_id: saved.id, tone_of_voice: tone }),
        });
        const passed =
          index === 0
            ? response.cache_status === "MISS"
            : index === 1
              ? response.cache_status === "HIT" &&
                response.copy.id === original?.copy.id &&
                response.copy.input_hash === original.copy.input_hash
              : response.cache_status === "MISS" &&
                response.copy.input_hash !== original?.copy.input_hash;
        add({
          step: [
            "Primeira geração",
            "Mesmos dados reutilizam a versão",
            "Outro tom cria um novo hash",
          ][index],
          passed,
          status: 200,
          cache: response.cache_status,
          client_latency_ms: performance.now() - start,
          input_hash: response.copy.input_hash,
          copy_id: response.copy.id,
        });
        if (index === 0) original = response;
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Falha ao executar demonstração.",
      );
    } finally {
      setRunning(false);
      onBusy(false);
    }
  }
  function download() {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            ...report,
            limitation:
              "Demonstração funcional com IA simulada. Não é benchmark de Gemini nem comprovação de qualidade publicitária.",
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "copylab-demonstracao.json";
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <div className="guide">
      <details className="panel guide-section">
        <summary>Ver a configuração desta sessão</summary>
        <span className="eyebrow">AMBIENTE EM EXECUÇÃO</span>
        <h2>O que está funcionando neste endereço</h2>
        <div className="guide-runtime">
          <span>
            Interface <strong>React + Tailwind</strong>
          </span>
          <span>
            API <strong>FastAPI</strong>
          </span>
          <span>
            Banco <strong>{runtime?.database ?? "Não verificado"}</strong>
          </span>
          <span>
            Cache <strong>{runtime?.cache ?? "Não verificado"}</strong>
          </span>
          <span>
            Geração{" "}
            <strong>
              {runtime?.provider === "mock"
                ? "IA simulada"
                : (runtime?.model ?? "Não verificada")}
            </strong>
          </span>
        </div>
        <p>
          O cadastro e o histórico são gravados no banco informado acima. No
          ambiente local sem Docker, o cache é simulado e reinicia com o
          servidor. Os tempos desta sessão não representam o desempenho do
          Gemini.
        </p>
      </details>
      <section className="panel guide-section">
        <span className="eyebrow">PASSO A PASSO</span>
        <h2>Como cadastrar um produto e gerar os textos</h2>
        <ol className="guide-steps">
          <li>
            <strong>1. Preencha o cadastro</strong>
            <p>
              Abra Estúdio de criação. Preencha todos os campos: código do
              produto, nome, categoria, público, características e benefícios.
            </p>
          </li>
          <li>
            <strong>2. Escolha o tom</strong>
            <p>
              Escolha como o texto deve se comunicar: persuasivo, descontraído,
              institucional ou promocional. Clique em Gerar conteúdo.
            </p>
          </li>
          <li>
            <strong>3. Confira e copie</strong>
            <p>
              Selecione Instagram, WhatsApp ou E-commerce / SEO. Leia o
              resultado e use Copiar texto para colar no canal escolhido. O
              sistema não publica automaticamente.
            </p>
          </li>
          <li>
            <strong>4. Consulte as versões</strong>
            <p>
              No Catálogo de produtos, clique em Editar e gerar para abrir um
              produto salvo. As versões anteriores aparecem abaixo do
              formulário. Consulte os tempos na tela Métricas de engenharia.
            </p>
          </li>
        </ol>
      </section>
      <section className="panel guide-section">
        <span className="eyebrow">DEMONSTRAÇÃO INTERATIVA</span>
        <h2>Experimente com um produto de exemplo</h2>
        <p>
          O botão cria um produto de exemplo no catálogo e executa quatro
          verificações pela API. O erro 422 é provocado de propósito para
          demonstrar a proteção da entrada. Cada execução cria um produto novo e
          mantém seu histórico.
        </p>
        <div className="form-actions">
          <button
            className="button primary"
            disabled={running || runtime?.provider !== "mock"}
            onClick={demonstrate}
          >
            {running ? "Executando verificações…" : "Executar demonstração"}
          </button>
          {report && (
            <button
              disabled={running}
              className="button secondary"
              onClick={download}
            >
              Baixar relatório JSON
            </button>
          )}
          {product && (
            <button
              disabled={running}
              className="button secondary"
              onClick={() => onProduct(product)}
            >
              Ver produto e textos
            </button>
          )}
        </div>
        {runtime?.provider !== "mock" && (
          <p>A execução automática está disponível apenas em modo simulado.</p>
        )}
        {error && (
          <div className="error-box" role="alert">
            {error}
          </div>
        )}
        <div aria-live="polite">
          {report?.observations.map((row, index) => (
            <article className="guide-observation" key={index}>
              <span className={`badge ${row.passed ? "green" : "red"}`}>
                {row.passed ? "Verificado" : "Divergência"}
              </span>
              <strong>{row.step}</strong>
              <span>
                HTTP {row.status} · {row.cache} ·{" "}
                {row.client_latency_ms.toFixed(1)} ms no navegador
              </span>
              {row.input_hash && <code>{row.input_hash}</code>}
            </article>
          ))}
        </div>
        {report?.observations.length === 4 && !running && !error && (
          <p role="status">
            {report.observations.every((row) => row.passed)
              ? "As quatro verificações passaram."
              : "Há divergências. Consulte o relatório antes de apresentar."}
          </p>
        )}
      </section>
      <section className="panel guide-section">
        <span className="eyebrow">DÚVIDAS FREQUENTES</span>
        <h2>Entenda os termos que aparecem nas telas</h2>
        <dl className="help-definitions">
          <dt>O que é cache? E HIT ou MISS?</dt>
          <dd>
            O cache guarda temporariamente um resultado. HIT significa que o
            texto salvo foi reutilizado. MISS significa que foi preciso
            solicitar uma nova geração. Se os dados e o tom forem os mesmos, o
            resultado pode ser reaproveitado enquanto estiver no cache.
          </dd>
          <dt>Por que o código do produto é obrigatório?</dt>
          <dd>
            O SKU é um código escolhido por você, como FONE-001. Ele diferencia
            os produtos do catálogo e não pode se repetir.
          </dd>
          <dt>O que é o hash SHA-256?</dt>
          <dd>
            É o código calculado a partir dos dados usados na geração. Ele
            permite conferir se duas solicitações usaram os mesmos dados.
            Alterar o produto, o tom ou a configuração do gerador muda esse
            código.
          </dd>
          <dt>O que significam HTTP 422 e HTTP 200?</dt>
          <dd>
            422 indica que faltam dados ou que algum campo é inválido. 200
            indica que a solicitação foi atendida. Na demonstração acima, o 422
            é esperado: o teste envia dados incompletos de propósito.
          </dd>
          <dt>O que são tokens e latência?</dt>
          <dd>
            Tokens são unidades de texto contabilizadas pelo modelo. Latência é
            o tempo de resposta, mostrado em milissegundos (ms). No modo
            simulado não há consumo de tokens do Gemini.
          </dd>
          <dt>O que faço antes de publicar um texto?</dt>
          <dd>
            Confira se as características e vantagens correspondem ao produto. A
            verificação automática confere os campos e seus limites, mas não
            substitui a revisão das informações.
          </dd>
        </dl>
      </section>
    </div>
  );
}
