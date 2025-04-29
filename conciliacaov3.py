import streamlit as st
import pandas as pd

# Função de pré-processamento e cálculo das somas no CSV
def conciliacao_financeira(arquivo_csv):
    bandeiras_df = pd.read_csv(arquivo_csv, sep=";", encoding="ISO-8859-1")

    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].replace({r'R\$': '', r'\.': '', ' ': ''}, regex=True)
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].str.replace(',', '.', regex=False)
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].astype(float)

    bandeiras_df = bandeiras_df[(bandeiras_df['Status'] != 'Recusada') & (bandeiras_df['Status'] != 'Estornada')]

    categorias = [
        ('Visa', 'Crédito', 'Visa Cred'),
        ('Visa', 'Crédito Internacional', 'Visa Cred Int'),
        ('Visa', 'Débito', 'Visa Deb'),
        ('Visa', 'Débito Internacional', 'Visa Deb Int'),
        ('Mastercard', 'Crédito', 'Master Cred'),
        ('Mastercard', 'Crédito International', 'Master Cred Int'),
        ('Maestro', 'Débito', 'Maestro Deb'),
        ('Mastercard', 'Débito Internacional', 'Maestro Deb Int'),
        ('Elo', 'Crédito', 'Elo Cred'),
        ('Elo', 'Débito', 'Elo Deb'),
        ('Amex', 'Crédito', 'Amex Cred'),
        ('Amex', 'Crédito Internacional', 'Amex Cred Int')
    ]

    somas_csv = {}
    for bandeira, tipo, nome_categoria in categorias:
        soma = bandeiras_df[(bandeiras_df['Bandeira'] == bandeira) & (bandeiras_df['Produto'] == tipo)]['Valor bruto'].sum()
        somas_csv[nome_categoria] = soma

    return somas_csv

# Função para extrair os valores da planilha Excel
def extrair_dados_excel(df):
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
            dados_abaixo = df.iloc[linha_index + 1:]
            sub_total_index = dados_abaixo[dados_abaixo.apply(lambda row: row.astype(str).str.contains("SUB-TOTAL TIPO:", case=False).any(), axis=1)].index
            if len(sub_total_index) > 0:
                sub_total_index = sub_total_index[0]
                valor = df.iloc[sub_total_index]["Unnamed: 19"]
                valores_extraidos[label] = float(valor)

    return valores_extraidos

# Função principal
def main():
    st.title("Conciliação Financeira")

    st.write("Faça upload da planilha Excel (.xls ou .xlsx) e do arquivo CSV.")

    uploaded_excel = st.file_uploader("Upload da Planilha Excel", type=["xls", "xlsx"])
    uploaded_csv = st.file_uploader("Upload do Arquivo CSV", type=["csv"])

    if uploaded_excel and uploaded_csv:
        try:
            if uploaded_excel.name.lower().endswith('.xls'):
                df_excel = pd.read_excel(uploaded_excel, engine='xlrd')
            else:
                df_excel = pd.read_excel(uploaded_excel, engine='openpyxl')
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo Excel: {e}")
            return

        try:
            valores_sistema = extrair_dados_excel(df_excel)
        except Exception as e:
            st.error(f"Erro ao extrair dados do Excel: {e}")
            return

        try:
            valores_bin_raw = conciliacao_financeira(uploaded_csv)
        except Exception as e:
            st.error(f"Erro ao processar o arquivo CSV: {e}")
            return

        # Agrupar Visa Cred + Visa Cred Int, etc.
        valores_bin = {
            "Visa Cred": valores_bin_raw.get("Visa Cred", 0) + valores_bin_raw.get("Visa Cred Int", 0),
            "Visa Deb": valores_bin_raw.get("Visa Deb", 0) + valores_bin_raw.get("Visa Deb Int", 0),
            "Master Cred": valores_bin_raw.get("Master Cred", 0) + valores_bin_raw.get("Master Cred Int", 0),
            "Maestro Deb": valores_bin_raw.get("Maestro Deb", 0) + valores_bin_raw.get("Maestro Deb Int", 0),
            "Elo Cred": valores_bin_raw.get("Elo Cred", 0),
            "Elo Deb": valores_bin_raw.get("Elo Deb", 0),
            "Amex Cred": valores_bin_raw.get("Amex Cred", 0) + valores_bin_raw.get("Amex Cred Int", 0),
            "B2B Master Credito": 0  # Bin normalmente não tem B2B, mas mostramos 0
        }

        st.subheader("Comparação entre Sistema e Bin")

        for label in valores_sistema:
            sistema_valor = valores_sistema.get(label, 0)
            bin_valor = valores_bin.get(label, 0)

            diferenca = sistema_valor - bin_valor
            diferenca_absoluta = abs(diferenca)

            st.write(f"{label}: Sistema = R${sistema_valor:,.2f} | Bin = R${bin_valor:,.2f}")

            if diferenca != 0:
                st.markdown(f"<p style='color:red; font-weight:bold;'>Soma Total (Sistema - Bin) = R${diferenca_absoluta:,.2f}</p>", unsafe_allow_html=True)
            else:
                st.write(f"Soma Total (Sistema - Bin) = R${diferenca_absoluta:,.2f}")

if __name__ == "__main__":
    main()
