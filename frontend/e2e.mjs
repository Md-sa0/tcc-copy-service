import { chromium } from "playwright";
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { randomUUID } from "node:crypto";

const baseURL = process.env.E2E_BASE_URL || "http://127.0.0.1:5173";
const output = "../artifacts/screenshots";
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ ignoreHTTPSErrors: process.env.E2E_IGNORE_HTTPS_ERRORS === "1",
  viewport: { width: 1440, height: 1080 },
  permissions: ["clipboard-read", "clipboard-write"],
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const sku = `UI-${Date.now()}`;
const email = `e2e-${randomUUID()}@example.com`;
const password = `CopyLab-e2e-${randomUUID()}`;
try {
  await page.goto(baseURL);
  await page.waitForFunction(async () => {
    const response = await fetch("/health");
    return response.ok;
  });
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill(password);
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await page.getByRole("heading", { name: "Gerar textos" }).waitFor();
  await page.screenshot({ path: `${output}/studio-empty.png`, fullPage: true });
  await page
    .locator("nav")
    .getByRole("button", { name: "Cadastrar produto", exact: true })
    .click();
  await page.getByLabel("SKU", { exact: true }).fill(sku);
  await page.getByLabel("Categoria", { exact: true }).fill("Eletrônicos");
  await page.getByLabel("Nome do produto").fill("Fone Bluetooth Aura");
  await page.getByLabel("Público-alvo").fill("Estudantes e profissionais");
  await page
    .getByLabel("Atributos técnicos")
    .fill("Conectividade: Bluetooth 5.3\nAutonomia: 24 horas");
  await page
    .getByLabel("Benefícios comprovados")
    .fill("Uso sem fios\nEstojo para transporte");
  await page.getByRole("button", { name: "Salvar produto" }).click();
  await page.getByText("Produto salvo no catálogo.", { exact: true }).waitFor();
  const productCard = page.locator(".catalog-card").filter({ hasText: sku });
  await productCard.getByRole("button", { name: "Gerar textos" }).click();
  await page.getByRole("radio", { name: "persuasivo" }).check();
  await page
    .locator(".generation-tone")
    .getByRole("button", { name: "Gerar textos", exact: true })
    .click();
  await page.getByRole("heading", { name: "Textos por canal" }).waitFor();
  await page.screenshot({
    path: `${output}/studio-generated.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "Copiar texto", exact: true }).click();
  await page.getByRole("button", { name: "Copiado", exact: true }).waitFor();
  assert.match(
    await page.evaluate(() => navigator.clipboard.readText()),
    /Fone Bluetooth Aura/,
  );
  await page.getByRole("tab", { name: "WhatsApp", exact: true }).click();
  await page.locator(".wa-bubble").waitFor();
  assert.match(await page.locator(".wa-bubble").innerText(), /Fone Bluetooth Aura/);
  await page.getByRole("tab", { name: "E-commerce / SEO" }).click();
  await page.locator(".seo-title").waitFor();
  await page
    .locator(".generation-tone")
    .getByRole("button", { name: "Gerar textos", exact: true })
    .click();
  await page.getByText("CACHE HIT", { exact: true }).waitFor();
  await page.getByRole("tab", { name: "Instagram", exact: true }).click();
  await page.getByRole("button", { name: "Editar texto", exact: true }).click();
  await page
    .getByRole("textbox", { name: /^Legenda/ })
    .fill("Legenda revisada no editor do CopyLab.");
  await page.getByRole("button", { name: "Salvar nova versão" }).click();
  await page
    .getByText("Edição salva como uma nova versão do histórico.", { exact: true })
    .waitFor();
  await page.getByText("Legenda revisada no editor do CopyLab.", { exact: true }).waitFor();
  await page.getByRole("button", { name: "Gerar nova versão", exact: true }).click();
  await page.getByRole("heading", { name: "Gerar uma nova versão?" }).waitFor();
  await page.getByText(/pode consumir créditos e gerar cobrança/).waitFor();
  await page.getByRole("button", { name: "Confirmar e gerar" }).click();
  await page
    .getByText("Nova versão gerada. A chamada pode gerar custos no provedor de IA.", { exact: true })
    .waitFor();
  await page
    .getByRole("button", { name: "Métricas de engenharia", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Histórico de requisições" })
    .waitFor();
  await page.locator("tbody tr").first().waitFor();
  await page.locator(".recharts-bar-rectangle path").first().waitFor();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `${output}/metrics-desktop.png`,
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Catálogo de produtos", exact: true })
    .click();
  await page.getByPlaceholder("Buscar nome ou SKU").fill(sku);
  await productCard.getByRole("button", { name: "Editar produto" }).click();
  await page.waitForFunction(
    (value) =>
      [...document.querySelectorAll("input")].some(
        (input) => input.value === value,
      ),
    sku,
  );
  assert.equal(await page.getByLabel("SKU", { exact: true }).inputValue(), sku);
  await page.getByLabel("Nome do produto").fill("Fone Bluetooth Aura Revisado");
  await page.getByRole("button", { name: "Salvar produto", exact: true }).click();
  await page.getByText("Produto salvo no catálogo.", { exact: true }).waitFor();
  await productCard.getByRole("button", { name: "Gerar textos" }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `${output}/studio-mobile.png`,
    fullPage: true,
  });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    true,
    "Mobile must not overflow horizontally",
  );
  await page
    .getByRole("button", { name: "Catálogo de produtos", exact: true })
    .click();
  await productCard
    .getByRole("button", {
      name: "Excluir Fone Bluetooth Aura Revisado",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Excluir produto", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Nenhum produto encontrado" })
    .waitFor();
  await page
    .getByRole("button", { name: "Como funciona", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Executar demonstração", exact: true })
    .click();
  await page
    .getByText("As quatro verificações passaram.", { exact: true })
    .waitFor();
  assert.equal(await page.locator(".guide-observation").count(), 4);
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Baixar relatório JSON" }).click();
  const download = await downloadPromise;
  await download.saveAs("../artifacts/guide-report.json");
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({
    path: `${output}/guide-desktop.png`,
    fullPage: true,
  });
  assert.deepEqual(errors, []);
  console.log(
    "E2E passed: CRUD, generation, cache, clipboard, previews, metrics, mobile, guided demonstration and report download.",
  );
} catch (error) {
  await page.screenshot({ path: `${output}/failure.png`, fullPage: true });
  console.error(await page.locator("main").innerText());
  throw error;
} finally {
  await browser.close();
}
