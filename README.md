# Mapping Generator for CGRA and QCA Architectures

Este projeto é uma ferramenta para a geração procedural e análise de mapeamentos de Grafos de Fluxo de Dados (DFGs) para arquiteturas Coarse-Grained Reconfigurable Array (CGRA) e Quantum-dot Cellular Automata (QCA).

## Visão Geral

O objetivo principal é gerar grandes volumes de dados de mapeamentos (DFG + posicionamento/roteamento) que podem ser usados para treinar modelos de machine learning, analisar heurísticas de mapeamento ou explorar o espaço de design de arquiteturas reconfiguráveis.

### Funcionalidades

* **Suporte a Múltiplas Arquiteturas:** Geração de grafos de conectividade para CGRA (com várias topologias de interconexão) e QCA (com esquemas de clocking USE, RES e 2DDWave).
* **Múltiplos Modos de Geração:**
    * **Grammar-based:** Usa um conjunto de regras de gramática para construir DFGs com níveis de complexidade estrutural controlados.
    * **Random:** Usa um método construtivo por níveis para gerar rapidamente DFGs aleatórios que são garantidamente balanceados e acíclicos (DAGs).
* **Interface de Linha de Comando (CLI) Flexível:** Controle total sobre os parâmetros de geração para execuções únicas ou campanhas em massa.
* **Execução Paralela:** Otimizado para gerar grandes campanhas de dados rapidamente, utilizando todos os núcleos de CPU disponíveis.
* **Utilitários de Pós-processamento:** Scripts para limpar os dados (removendo grafos isomórficos) e gerar sumários estatísticos em formato CSV.

## Estrutura do Projeto
