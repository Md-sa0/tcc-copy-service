import { z, type ZodError } from "zod";

const clean = (value: string) => value.normalize("NFC").trim();
const text = z
  .string()
  .transform(clean)
  .pipe(z.string().min(1, "Preencha este campo").max(500));
export const productSchema = z
  .object({
    sku: z
      .string()
      .transform(clean)
      .pipe(
        z
          .string()
          .regex(
            /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/,
            "SKU: até 64 letras, números, ponto, hífen ou sublinhado",
          ),
      ),
    name: z.string().transform(clean).pipe(z.string().min(2).max(200)),
    category: z.string().transform(clean).pipe(z.string().min(2).max(100)),
    target_audience: z
      .string()
      .transform(clean)
      .pipe(z.string().min(3).max(500)),
    technical_attributes: z
      .record(text, text)
      .refine(
        (v) => Object.keys(v).length >= 1 && Object.keys(v).length <= 30,
        "Informe entre 1 e 30 atributos",
      ),
    key_benefits: z
      .array(text)
      .min(1)
      .max(20)
      .refine(
        (v) => new Set(v).size === v.length,
        "Remova benefícios duplicados",
      ),
  })
  .strict();

export function formatProductValidationError(error: ZodError): string {
  const messages = new Set<string>();
  for (const issue of error.issues) {
    switch (issue.path[0]) {
      case "sku":
        messages.add(
          "Confira o SKU: comece com uma letra ou número e use até 64 caracteres, entre letras, números, ponto, hífen e sublinhado.",
        );
        break;
      case "name":
        messages.add("Informe o nome do produto (de 2 a 200 caracteres).");
        break;
      case "category":
        messages.add("Informe a categoria (de 2 a 100 caracteres).");
        break;
      case "target_audience":
        messages.add("Descreva o público-alvo (de 3 a 500 caracteres).");
        break;
      case "technical_attributes":
        messages.add(
          "Revise os atributos técnicos: informe de 1 a 30 linhas no formato “Nome: valor”.",
        );
        break;
      case "key_benefits":
        messages.add(
          issue.message.toLowerCase().includes("duplicad")
            ? "Há benefícios repetidos. Mantenha cada benefício apenas uma vez."
            : "Informe de 1 a 20 benefícios, um por linha.",
        );
        break;
    }
  }
  return messages.size
    ? [...messages].join(" ")
    : "Confira os dados do formulário e tente novamente.";
}

export function parseAttributes(value: string): Record<string, string> {
  const rows: [string, string][] = [];
  value.split("\n").forEach((line, index) => {
    if (!line.trim()) return;
    const lineNumber = index + 1;
    const separator = line.indexOf(":");
    if (separator < 0)
      throw new Error(
        `Linha ${lineNumber}: separe o nome do valor com “:”. Exemplo: Material: algodão.`,
      );
    const key = clean(line.slice(0, separator));
    const attributeValue = clean(line.slice(separator + 1));
    if (!key)
      throw new Error(
        `Linha ${lineNumber}: informe o nome do atributo antes de “:”.`,
      );
    if (!attributeValue)
      throw new Error(
        `Linha ${lineNumber}: informe o valor depois de “:”. Exemplo: Material: algodão.`,
      );
    rows.push([key, attributeValue]);
  });
  if (new Set(rows.map(([key]) => key)).size !== rows.length)
    throw new Error(
      "Há atributos repetidos. Use um nome diferente para cada atributo.",
    );
  return Object.fromEntries(rows);
}
