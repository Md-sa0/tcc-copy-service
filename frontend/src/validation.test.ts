import { describe, expect, it } from "vitest";
import { parseAttributes, productSchema } from "./validation";

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
    expect(() => parseAttributes("cor: azul\n cor: verde")).toThrow();
    expect(() => parseAttributes("sem separador")).toThrow();
  });
});
