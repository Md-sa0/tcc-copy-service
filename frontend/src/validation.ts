import { z } from "zod";

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

export function parseAttributes(value: string): Record<string, string> {
  const rows = value
    .split("\n")
    .filter((v) => v.trim())
    .map((line) => {
      const separator = line.indexOf(":");
      if (separator < 1)
        throw new Error('Atributos: use um par "atributo: valor" por linha.');
      return [
        clean(line.slice(0, separator)),
        clean(line.slice(separator + 1)),
      ];
    });
  if (new Set(rows.map(([key]) => key)).size !== rows.length)
    throw new Error("Remova atributos duplicados.");
  return Object.fromEntries(rows);
}
