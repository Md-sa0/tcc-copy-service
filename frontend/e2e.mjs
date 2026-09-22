import { chromium } from "playwright";
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";

const baseURL = process.env.E2E_BASE_URL || "http://127.0.0.1:5173";
const output = "../artifacts/screenshots";
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1080 },
  permissions: ["clipboard-read", "clipboard-write"],
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const sku = `UI-${Date.now()}`;
try {
  await page.goto(baseURL);
  await page.getByText("API conectada").waitFor();
  await page.screenshot({ path: `${output}/studio-empty.png`, fullPage: true });
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
  await page.getByRole("button", { name: "Gerar conteúdo" }).click();
  await page.getByRole("heading", { name: "Pronto para cada canal" }).waitFor();
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
  await page.locator(".wa-bubble strong").waitFor();
  await page.getByRole("tab", { name: "E-commerce / SEO" }).click();
  await page.locator(".seo-title").waitFor();
  await page
    .getByRole("button", { name: "Gerar conteúdo", exact: true })
    .click();
  await page.getByText("CACHE HIT", { exact: true }).waitFor();
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
  const productCard = page.locator(".catalog-card").filter({ hasText: sku });
  await productCard.getByRole("button", { name: "Editar e gerar" }).click();
  await page.waitForFunction(
    (value) =>
      [...document.querySelectorAll("input")].some(
        (input) => input.value === value,
      ),
    sku,
  );
  assert.equal(await page.getByLabel("SKU", { exact: true }).inputValue(), sku);
  await page.getByLabel("Nome do produto").fill("Fone Bluetooth Aura Revisado");
  await page.getByRole("button", { name: "Salvar", exact: true }).click();
  await page.getByText("Produto salvo no catálogo.", { exact: true }).waitFor();
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
  assert.deepEqual(errors, []);
  console.log(
    "E2E passed: create, generate, cache hit, clipboard, channel previews, metrics, search, edit, delete, mobile layout.",
  );
} finally {
  await browser.close();
}
