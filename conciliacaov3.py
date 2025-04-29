pip install openpyxl

import streamlit as st
import pandas as pd

# Função para carregar e processar o arquivo Excel
def processar_excel(uploaded_file):
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.success("Arquivo Excel carregado com sucesso!")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo Excel: {e}")
        return None

# Função para carregar o arquivo CSV e fazer a análise
def conciliacao_financeira(arquivo_csv):
    try:
        bandeiras_df = pd.read_csv(arquivo_csv, sep=";", encoding="ISO-8859-1")
        
        # Limpeza de dados
        bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].replace({r'R\$': '', r'\.': '', ' ': ''}, regex=True)
        bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].str.replace(',', '.', regex=False)  # Substituindo vírgula por ponto
        bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].astype(float)
        
        # Filtrando dados
        bandeiras_df = bandeiras_df[(bandeiras_df['Status'] != 'Recusada') & (bandeiras_df['Status'] != 'Estornada')]
        
        # Categorias e somas
        categorias = [
            ('Visa', 'Crédito', 'Visa Cred'),
            ('Visa', 'Débito', 'Visa Deb'),
            ('Mastercard', 'Crédito', 'Master Cred'),
            ('Mastercard', 'Débito', 'Master Deb'),
            ('Elo', 'Crédito', 'Elo Cred'),
            ('Elo', 'Débito', 'Elo Deb'),
            ('Amex', 'Crédito', 'Amex Cred'),
            ('B2B', 'Master Credito', 'B2B Master Credito'),
        ]
        
        somas_csv = {}
        for bandeira, tipo, nome_categoria in categorias:
            soma = bandeiras_df[(bandeiras_df['Bandeira'] == bandeira) & (bandeiras_df['Produto'] == tipo)]['Valor bruto'].sum()
            somas_csv[nome_categoria] = soma
        return somas_csv
    except Exception as e:
        st.error(f"Erro ao processar o arquivo CSV: {e}")
        return {}

# Função principal
def main():
    st.title("Conciliador Financeiro")

    # Upload de arquivos
    st.subheader("1. Carregar arquivo Excel")
    uploaded_excel = st.file_uploader("Carregue seu arquivo Excel", type=["xlsx", "xls"])
    
    if uploaded_excel is not None:
        df_excel = processar_excel(uploaded_excel)

        if df_excel is not None:
            st.subheader("Dados extraídos do Excel")
            st.write(df_excel.head())  # Exibe as primeiras linhas do Excel

    st.subheader("2. Carregar arquivo CSV")
    uploaded_csv = st.file_uploader("Carregue seu arquivo CSV", type=["csv"])

    if uploaded_csv is not None:
        # Processar o CSV
        somas_csv = conciliacao_financeira(uploaded_csv)
        st.subheader("Análise do CSV")
        st.write(somas_csv)

        # Comparação dos valores
        if uploaded_excel is not None and df_excel is not None:
            st.subheader("Comparação entre Excel e CSV")
            for label in somas_csv:
                if label == "Visa Cred":
                    # Somar Visa Cred e Visa Cred Int
                    visa_cred_total = somas_csv["Visa Cred"] + somas_csv.get("Visa Cred Int", 0)
                    somas_csv["Visa Cred"] = visa_cred_total  # Substitui o valor de Visa Cred com a soma

                if label == "Visa Deb":
                    # Somar Visa Deb e Visa Deb Int
                    visa_deb_total = somas_csv["Visa Deb"] + somas_csv.get("Visa Deb Int", 0)
                    somas_csv["Visa Deb"] = visa_deb_total  # Substitui o valor de Visa Deb com a soma
                
                if label == "Master Cred":
                    # Somar Master Cred e Master Cred Int
                    master_cred_total = somas_csv["Master Cred"] + somas_csv.get("Master Cred Int", 0)
                    somas_csv["Master Cred"] = master_cred_total  # Substitui o valor de Master Cred com a soma

                if label == "Maestro Deb":
                    # Somar Maestro Deb e Maestro Deb Int
                    maestro_deb_total = somas_csv["Maestro Deb"] + somas_csv.get("Maestro Deb Int", 0)
                    somas_csv["Maestro Deb"] = maestro_deb_total  # Substitui o valor de Maestro Deb com a soma

                if label == "Amex Cred":
                    # Somar Amex Cred e Amex Cred Int
                    amex_cred_total = somas_csv["Amex Cred"] + somas_csv.get("Amex Cred Int", 0)
                    somas_csv["Amex Cred"] = amex_cred_total  # Substitui o valor de Amex Cred com a soma

            # Comparar resultados
            for label in somas_csv:
                valor_sistema = df_excel.get(label, 0)  # Valor extraído do Excel
                valor_bin = somas_csv[label]  # Valor extraído do CSV
                if valor_sistema != valor_bin:
                    st.markdown(f"<span style='color:red;'>Soma Total ({label}): Sistema = R${valor_sistema:,.2f} | Bin = R${valor_bin:,.2f} | Soma Total = R${valor_sistema + valor_bin:,.2f}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"Soma Total ({label}): Sistema = R${valor_sistema:,.2f} | Bin = R${valor_bin:,.2f} | Soma Total = R${valor_sistema + valor_bin:,.2f}")

if __name__ == "__main__":
    main()
