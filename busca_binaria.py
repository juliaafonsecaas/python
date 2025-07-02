def busca_binaria(lista, alvo):
    inicio = 0
    fim = len(lista) - 1

    while inicio <= fim:
        meio = (inicio + fim) // 2
        if lista[meio] == alvo:
            return meio
        elif lista[meio] < alvo:
            inicio = meio + 1
        else:
            fim = meio - 1
    return -1

if __name__ == "__main__":
    lista_ordenada = [1, 3, 5, 7, 9, 11, 13]
    alvo = 7
    resultado = busca_binaria(lista_ordenada, alvo)
    if resultado != -1:
        print(f"Elemento encontrado no índice {resultado}")
    else:
        print("Elemento não encontrado")
