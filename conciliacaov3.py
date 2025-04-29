import pandas as pd
import streamlit as st

# Função para carregar o arquivo Excel dependendo da extensão
def carregar_excel(uploaded_file):
    try:
        # Verificar a extensão do arquivo
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'xls':
            df = pd.read_excel(uploaded_file, engine='xlrd')  # Usar xlrd para .xls
        else:
            raise ValueError("O arquivo precisa ser do tipo .xls")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel: {e}")
        return None

# Função de pré-processamento e cálculo das somas no CSV
def conciliacao_financeira(arquivo_csv):
    # Carregar o arquivo CSV com a codificação 'ISO-8859-1'
    bandeiras_df = pd.read_csv(arquivo_csv, sep=";", encoding="ISO-8859-1")

    # Limpeza de dados: Remover o símbolo 'R$', substituir a vírgula por ponto e remover o ponto de milhar
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].replace({r'R\$': '', r'\.': '', ' ': ''}, regex=True)
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].str.replace(',', '.', regex=False)  # Substituindo vírgula por ponto

    # Converter para float
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].astype(float)

    # Filtrar apenas linhas onde o "Status" não seja "Recusado"
    bandeiras_df = bandeiras_df[(bandeiras_df['Status'] != 'Recusada') & (bandeiras_df['Status'] != 'Estornada')]

    # Lista de categorias para ordenação
    categorias = [
        ('Visa', 'Crédito', 'Visa Cred'),
        ('Visa', 'Débito', 'Visa Deb'),
        ('Mastercard', 'Crédito', 'Master Cred'),
        ('Mastercard', 'Débito', 'Master Deb'),
        ('Maestro', 'Débito', 'Maestro Deb'),
        ('Elo', 'Crédito', 'Elo Cred'),
        ('Amex', 'Crédito', 'Amex Cred'),
        ('B2B', 'Master Credito', 'B2B Master Credito')
    ]

    somas_csv = {}
    # Calculando as somas para cada categoria e armazenando
    for bandeira, tipo, nome_categoria in categorias:
        soma = bandeiras_df[(bandeiras_df['Bandeira'] == bandeira) & (bandeiras_df['Produto'] == tipo)]['Valor bruto'].sum()
        somas_csv[nome_categoria] = soma

    # Soma específica para categorias combinadas
    soma_visa_cred = somas_csv.get('Visa Cred', 0) + somas_csv.get('Visa Cred Int', 0)
    soma_visa_deb = somas_csv.get('Visa Deb', 0) + somas_csv.get('Visa Deb Int', 0)
    soma_master_cred = somas_csv.get('Master Cred', 0) + somas_csv.get('Master Cred Int', 0)
    soma_maestro_deb = somas_csv.get('Maestro Deb', 0) + somas_csv.get('Maestro Deb Int', 0)
    soma_amex_cred = somas_csv.get('Amex Cred', 0) + somas_csv.get('Amex Cred Int', 0)

    # Atualizando os resultados combinados
    somas_csv['Visa Cred'] = soma_visa_cred
    somas_csv['Visa Deb'] = soma_visa_deb
    somas_csv['Master Cred'] = soma_master_cred
    somas_csv['Maestro Deb'] = soma_maestro_deb
    somas_csv['Amex Cred'] = soma_amex_cred

    return somas_csv


# Função para extrair os valores da planilha Excel
def extrair_dados_excel(df):
    # Procurar as palavras-chave e extrair os valores
    valores_extraidos = {}

    keywords = [
        ("Bin Visa Cred", "Visa Cred"),
        ("Bin Visa Deb", "Visa Deb"),
        ("Bin Master Cred", "Master Cred"),
        ("Bin Maestro Deb", "Maestro Deb"),
        ("Bin Elo Cred", "Elo Cred"),
        ("Bin Elo Deb", "Elo Deb"),
        ("Bin Amex", "Amex Cred"),
        ("B2B Master Credito", "B2B Master Credito"),
    ]

    for keyword, label in keywords:
        linha_index = df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)].index
        if len(linha_index) > 0:
            linha_index = linha_index[0]
            dados_abaixo = df.iloc[linha_index + 1:]  # Todas as linhas abaixo da linha encontrada
            sub_total_index = dados_abaixo[dados_abaixo.apply(lambda row: row.astype(str).str.contains("SUB-TOTAL TIPO:", case=False).any(), axis=1)].index
            if len(sub_total_index) > 0:
                sub_total_index = sub_total_index[0]
                # Encontrar o valor na coluna 'Unnamed: 19'
                valor = df.iloc[sub_total_index]["Unnamed: 19"]

                # Convertendo valores financeiros com ponto como separador decimal
                if isinstance(valor, str):
                    valor = valor.replace("R$", "").replace(",", "").strip()
                valores_extraidos[label] = float(valor)

    return valores_extraidos


# Função para exibir no Streamlit
def exibir_comparacao(somas_excel, somas_csv):
    for label in somas_excel:
        sistema_valor = somas_excel[label]
        bin_valor = somas_csv.get(label, 0)

        if sistema_valor != bin_valor:
            diferenca = sistema_valor - bin_valor
            st.markdown(f"{label}: Sistema = {sistema_valor:,.2f} | Bin = {bin_valor:,.2f} | **DIFERENÇA = {diferenca:,.2f}**", unsafe_allow_html=True)
        else:
            st.markdown(f"{label}: Sistema = {sistema_valor:,.2f} | Bin = {bin_valor:,.2f} | DIFERENÇA = 0.00", unsafe_allow_html=True)


def main():
    # Carregar o arquivo Excel
    st.title('Comparação entre Sistema e Bin')

    uploaded_excel = st.file_uploader("Faça o upload do arquivo Excel", type=["xls"])
    if uploaded_excel is not None:
        # Carregar o arquivo Excel com a função que detecta a extensão
        df_excel = carregar_excel(uploaded_excel)
        if df_excel is None:
            return
        st.success("Planilha Excel carregada com sucesso!")

    # Carregar o arquivo CSV
    uploaded_csv = st.file_uploader("Faça o upload do arquivo CSV", type=["csv"])
    if uploaded_csv is not None:
        somas_csv = conciliacao_financeira(uploaded_csv)

        # Extrair os valores do Excel
        valores_excel = extrair_dados_excel(df_excel)

        # Exibir os resultados da comparação
        exibir_comparacao(valores_excel, somas_csv)


if __name__ == "__main__":
    main()
