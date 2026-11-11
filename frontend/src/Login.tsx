import { ArrowRight, Command, LoaderCircle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { api } from "./api";

export interface AuthUser {
  id: string;
  email: string;
}

export default function Login({
  onAuthenticated,
  onAttempt,
  statusMessage,
}: {
  onAuthenticated: (user: AuthUser) => void;
  onAttempt: () => void;
  statusMessage: string;
}) {
  const [registering, setRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onAttempt();
    setBusy(true);
    setError("");
    try {
      const result = await api<{ user: AuthUser } | AuthUser>(
        `/api/v1/auth/${registering ? "register" : "login"}`,
        { method: "POST", body: JSON.stringify({ email, password }) },
      );
      onAuthenticated("user" in result ? result.user : result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível acessar sua conta.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <a className="auth-brand" href="#" aria-label="CopyLab">
          <span className="brand-icon"><Command size={22} /></span>
          <span>copylab<span className="brand-dot">.</span></span>
        </a>
        <span className="eyebrow">SEU ESPAÇO DE CRIAÇÃO</span>
        <h1 id="auth-title">{registering ? "Crie sua conta" : "Boas-vindas de volta"}</h1>
        <p className="auth-intro">
          {registering
            ? "Cadastre-se para criar seu catálogo e gerar conteúdo com segurança."
            : "Entre para continuar criando conteúdo para seus produtos."}
        </p>

        <form className="auth-form" onSubmit={submit}>
          {statusMessage && <div className="error-box" role="alert">{statusMessage}</div>}
          <label htmlFor="account-email">E-mail</label>
          <input
            id="account-email"
            type="email"
            name="email"
            autoComplete="email"
            required
            maxLength={254}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="voce@empresa.com"
          />
          <label htmlFor="account-password">Senha</label>
          <input
            id="account-password"
            type="password"
            name="password"
            autoComplete={registering ? "new-password" : "current-password"}
            required
            minLength={registering ? 12 : 1}
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={registering ? "Pelo menos 12 caracteres" : "Sua senha"}
          />
          {error && <div className="error-box" role="alert">{error}</div>}
          <button className="button primary auth-submit" type="submit" disabled={busy}>
            {busy ? <LoaderCircle size={17} className="spin" /> : <ArrowRight size={17} />}
            {busy ? "Aguarde…" : registering ? "Criar conta" : "Entrar"}
          </button>
        </form>

        <p className="auth-switch">
          {registering ? "Já tem uma conta?" : "Ainda não tem uma conta?"}{" "}
          <button
            type="button"
            onClick={() => {
              setRegistering((value) => !value);
              setError("");
            }}
          >
            {registering ? "Fazer login" : "Criar conta"}
          </button>
        </p>
      </section>
    </main>
  );
}
