# Painel de Vendas: Sabor do Sertão

Painel interativo em Streamlit para analisar um ano de vendas da rede fictícia
Sabor do Sertão (Recife, Olinda, Caruaru, Petrolina e Garanhuns).

## Como rodar

```bash
pip install -r requirements.txt
python gerar_dados.py        # gera vendas_sabor_do_sertao.csv (5.000 linhas, semente 42)
streamlit run app.py
```

O painel usa o CSV local automaticamente; também é possível enviar o arquivo pela barra lateral.

## O que o painel tem

| Nível | Entrega |
|---|---|
| 1. Exploração | `head`, `describe`, ausentes por coluna; `avaliacao` preenchida com a mediana (justificativa na própria tela) |
| 2. Indicadores | Faturamento total, número de vendas, ticket médio e avaliação média |
| 3. Filtros | Cidade, categoria e período na barra lateral; KPIs e gráficos reagem a todos |
| 4. Gráficos | Faturamento mensal, por cidade, Top 5 produtos, formas de pagamento e mapa de calor (dia x hora), em abas |
| 5. Insights | Três conclusões que se atualizam com os filtros + download do CSV filtrado |
| Bônus | Aba "Explorador livre": qualquer CSV, escolha de eixo X, eixo Y e tipo de gráfico |

## Print do painel

<img width="1917" height="956" alt="imagem" src="https://github.com/user-attachments/assets/3d863e1c-dab2-419c-8a7c-3679cb4aa1fc" />


## Autores

Dupla: Thauan Bezerra e Arthur Vinicius
