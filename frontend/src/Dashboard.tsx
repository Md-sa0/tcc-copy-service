import { useEffect, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  Database,
  RefreshCw,
  Zap,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "./api";
import type { Metric, Page, Summary } from "./types";

const number = (v: number | null | undefined, suffix = "") =>
  v == null
    ? "—"
    : `${v.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}${suffix}`;

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [history, setHistory] = useState<Page<Metric> | null>(null);
  const [hours, setHours] = useState(24),
    [offset, setOffset] = useState(0),
    [revision, setRevision] = useState(0);
  const [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    Promise.all([
      api<Summary>(`/api/v1/metrics/summary?hours=${hours}`, {
        signal: controller.signal,
      }),
      api<Page<Metric>>(
        `/api/v1/metrics/requests?hours=${hours}&offset=${offset}&limit=10&kind=generation`,
        { signal: controller.signal },
      ),
    ])
      .then(([s, h]) => {
        setSummary(s);
        setHistory(h);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [hours, offset, revision]);
  const data = [
    { name: "Cache miss", latency: summary?.miss_latency_ms ?? null },
    { name: "Cache hit", latency: summary?.hit_latency_ms ?? null },
  ];
  return (
    <div className="dashboard">
      <div className="section-toolbar">
        <p>Medições da API, persistidas no PostgreSQL.</p>
        <div>
          <select
            aria-label="Período das métricas"
            value={hours}
            onChange={(e) => {
              setHours(Number(e.target.value));
              setOffset(0);
            }}
          >
            <option value={1}>Última hora</option>
            <option value={24}>Últimas 24 horas</option>
            <option value={168}>Últimos 7 dias</option>
            <option value={720}>Últimos 30 dias</option>
          </select>
          <button
            className="button secondary"
            disabled={loading}
            onClick={() => setRevision((v) => v + 1)}
          >
            <RefreshCw size={15} className={loading ? "spin" : ""} /> Atualizar
          </button>
        </div>
      </div>
      {error && (
        <div className="error-box" role="alert">
          {error}
        </div>
      )}
      {summary?.provider === "mock" && (
        <div className="demo-banner">
          Demonstração: latências do simulador, sem consumo de tokens. Estes
          dados não representam desempenho do Gemini.
        </div>
      )}
      <div className="stat-grid">
        {[
          {
            label: "Requisições de geração",
            value: number(summary?.generation_requests),
            note: `${summary?.errors ?? 0} falhas registradas`,
            Icon: Activity,
          },
          {
            label: "Taxa de cache hit",
            value: number(
              summary?.cache_hit_ratio == null
                ? null
                : summary.cache_hit_ratio * 100,
              "%",
            ),
            note: "Sobre gerações bem-sucedidas",
            Icon: Database,
          },
          {
            label: "Economia de latência",
            value: number(summary?.latency_savings_percent, "%"),
            note: "Comparação das médias hit / miss",
            Icon: Zap,
          },
          {
            label: "Economia estimada de tokens",
            value: number(summary?.estimated_token_savings_percent, "%"),
            note: `${number(summary?.estimated_tokens_saved)} tokens estimados`,
            Icon: ArrowDownRight,
          },
        ].map((s) => (
          <section className="panel stat" key={s.label}>
            <s.Icon size={18} />
            <span>{s.label}</span>
            <strong>{s.value}</strong>
            <small>{s.note}</small>
          </section>
        ))}
      </div>
      <div className="chart-grid">
        <section className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">DESEMPENHO</span>
              <h2>Menos espera, mais conteúdo</h2>
            </div>
            <span className="badge">Média · ms</span>
          </div>
          {summary?.successful_generations ? (
            <div className="chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data}
                  layout="vertical"
                  margin={{ left: 10, right: 30 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 12 }} unit=" ms" />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={95}
                    tick={{ fontSize: 13 }}
                  />
                  <Tooltip
                    formatter={(value) => `${Number(value).toFixed(2)} ms`}
                  />
                  <Bar
                    isAnimationActive={false}
                    dataKey="latency"
                    name="Latência"
                    radius={[0, 6, 6, 0]}
                    barSize={36}
                  >
                    {data.map((v, i) => (
                      <Cell
                        key={v.name}
                        fill={i === 0 ? "#c9d5ce" : "#2e6f58"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-chart">
              Gere conteúdo para começar a medir.
            </div>
          )}
          <p className="chart-caption">
            Latência interna, anterior à gravação da auditoria. Não inclui o
            percurso de rede.
          </p>
        </section>
        <section className="panel methodology">
          <span className="eyebrow">TRANSPARÊNCIA EXPERIMENTAL</span>
          <h2>O que estamos medindo</h2>
          <p>
            O cache evita uma nova inferência para os mesmos atributos, tom,
            modelo e versão do prompt.
          </p>
          <dl>
            <div>
              <dt>Modelo do resumo</dt>
              <dd>{summary?.model_name ?? "—"}</dd>
            </div>
            <div>
              <dt>Tokens informados pelo provedor</dt>
              <dd>{number(summary?.tokens_used)}</dd>
            </div>
            <div>
              <dt>Respostas hit / miss</dt>
              <dd>
                {summary?.cache_hits ?? 0} / {summary?.cache_misses ?? 0}
              </dd>
            </div>
          </dl>
          <small>
            Economia de tokens usa o consumo da geração original como
            estimativa. “—” indica amostra insuficiente. Falhas não entram nas
            médias de sucesso. O histórico inclui todos os modelos.
          </small>
        </section>
      </div>
      <section className="panel history-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">RASTREABILIDADE</span>
            <h2>Histórico de requisições</h2>
          </div>
          <span className="badge">{history?.total ?? 0} registros</span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Data e hora</th>
                <th>Status</th>
                <th>Cache</th>
                <th>Latência</th>
                <th>SHA-256 / modelo</th>
                <th>Tokens</th>
              </tr>
            </thead>
            <tbody>
              {history?.items.map((row) => (
                <tr key={row.id}>
                  <td>{new Date(row.created_at).toLocaleString("pt-BR")}</td>
                  <td>
                    <span
                      className={`badge ${row.status_code < 300 ? "green" : "red"}`}
                    >
                      {row.status_code}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge ${row.cache_status === "HIT" ? "green" : ""}`}
                    >
                      {row.cache_status}
                    </span>
                  </td>
                  <td>{number(row.latency_ms, " ms")}</td>
                  <td>
                    <code title={row.input_hash ?? ""}>
                      {row.input_hash ?? "Sem hash: validação ou autenticação"}
                    </code>
                    <small>{row.model_name ?? "—"}</small>
                  </td>
                  <td>{row.tokens_used}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!history?.items.length && (
            <div className="empty-table">Nenhuma requisição neste período.</div>
          )}
        </div>
        <div className="pagination">
          <span>{history?.total ?? 0} resultados</span>
          <button
            disabled={offset === 0 || loading}
            onClick={() => setOffset(Math.max(0, offset - 10))}
          >
            Anterior
          </button>
          <button
            disabled={!history || offset + 10 >= history.total || loading}
            onClick={() => setOffset(offset + 10)}
          >
            Próxima
          </button>
        </div>
      </section>
    </div>
  );
}
