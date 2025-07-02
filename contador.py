def contar_vogais(texto):
    vogais = "aeiouAEIOU"
    return sum(1 for letra in texto if letra in vogais)

# Teste:
if __name__ == "__main__":
    frase = "welcome to my dev world"
    total = contar_vogais(frase)
    print(f"Número de vogais na frase: {total}")
