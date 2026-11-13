import { describe, expect, it } from "vitest";
import {
  formatProductValidationError,
  parseAttributes,
  productSchema,
} from "./validation";

const valid = {
  sku: "SKU-01",
  name: "Produto teste",
  category: "Eletrônicos",
  target_audience: "Estudantes",
  technical_attributes: { cor: "azul" },
  key_benefits: ["Portátil"],
};
describe("contrato do catálogo", () => {
  it("normaliza espaços e Unicode", () =>
    expect(productSchema.parse({ ...valid, name: " Cafe\u0301 " }).name).toBe(
      "Café",
    ));
  it("rejeita campos em branco", () =>
    expect(productSchema.safeParse({ ...valid, name: "  " }).success).toBe(
      false,
    ));
  it("rejeita coerção de números e campos extras", () => {
    expect(productSchema.safeParse({ ...valid, sku: 12 }).success).toBe(false);
    expect(productSchema.safeParse({ ...valid, unexpected: 1 }).success).toBe(
      false,
    );
  });
  it("exige atributos e benefícios únicos", () => {
    expect(
      productSchema.safeParse({ ...valid, technical_attributes: {} }).success,
    ).toBe(false);
    expect(
      productSchema.safeParse({
        ...valid,
        key_benefits: ["Portátil", " Portátil "],
      }).success,
    ).toBe(false);
  });
  it("preserva dois pontos nos valores e rejeita chaves duplicadas", () => {
    expect(parseAttributes("horário: 10:30")).toEqual({ horário: "10:30" });
    expect(() => parseAttributes("cor: azul\n cor: verde")).toThrow(
      "Há atributos repetidos.",
    );
    expect(() => parseAttributes("cor: azul\nsem separador")).toThrow(
      "Linha 2:",
    );
    expect(() => parseAttributes("cor: ")).toThrow("informe o valor depois");
  });
  it("explica erros do cadastro sem expor mensagens técnicas", () => {
    const invalid = productSchema.safeParse({ ...valid, sku: "SKU inválido" });
    if (invalid.success) throw new Error("O SKU deveria ser rejeitado.");
    expect(formatProductValidationError(invalid.error)).toContain(
      "Confira o SKU",
    );
  });
});
