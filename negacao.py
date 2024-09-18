class Negacoes:
    def __init__(self):
        # Dicionário de negações com tags como chaves e nomes como valores
        self._negados = {
            223344556: "Pedro Santos",
            665544332: "Ana Costa",
            778899001: "Lucas Ferreira"
        }

    def __contains__(self, tag):
        # Verifica se a tag está no dicionário de negações
        return tag in self._negados

    def __getitem__(self, tag):
        # Retorna o nome do colaborador cuja tag está negada
        return self._negados.get(tag, None)

    def adicionar_negacao(self, tag, nome):
        # Adiciona uma nova tag e nome ao dicionário de negações
        self._negados[tag] = nome

    def remover_negacao(self, tag):
        # Remove uma tag do dicionário de negações
        if tag in self._negados:
            del self._negados[tag]
