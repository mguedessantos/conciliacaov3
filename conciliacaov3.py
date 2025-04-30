import pandas as pd
import streamlit as st

# Função para carregar o arquivo Excel dependendo da extensão
def carregar_excel(uploaded_file):
    try:
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
    bandeiras_df = pd.read_csv(arquivo_csv, sep=";", encoding="ISO-8859-1")
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].replace({r'R\$': '', r'\.': '', ' ': ''}, regex=True)
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].str.replace(',', '.', regex=False)
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].astype(float)
    bandeiras_df = bandeiras_df[(bandeiras_df['Status'] != 'Recusada') & (bandeiras_df['Status'] != 'Estornada')]

    categorias = [
        ('Visa', 'Crédito', 'Visa Cred'),
        ('Visa', 'Débito', 'Visa Deb'),
        ('Mastercard', 'Crédito', 'Master Cred'),
        ('Mastercard', 'Débito', 'Master Deb'),
        ('Maestro', 'Débito', 'Maestro Deb'),
        ('Elo', 'Crédito', 'Elo Cred'),
        ('Elo', 'Débito', 'Elo Deb'),
        ('Amex', 'Crédito', 'Amex Cred'),
        ('B2B', 'Master Credito', 'B2B Master Credito')
    ]

    somas_csv = {}
    for bandeira, tipo, nome_categoria in categorias:
        soma = bandeiras_df[(bandeiras_df['Bandeira'] == bandeira) & (bandeiras_df['Produto'] == tipo)]['Valor bruto'].sum()
        somas_csv[nome_categoria] = soma

    soma_visa_cred = somas_csv.get('Visa Cred', 0) + somas_csv.get('Visa Cred Int', 0)
    soma_visa_deb = somas_csv.get('Visa Deb', 0) + somas_csv.get('Visa Deb Int', 0)
    soma_master_cred = somas_csv.get('Master Cred', 0) + somas_csv.get('Master Cred Int', 0)
    soma_maestro_deb = somas_csv.get('Maestro Deb', 0) + somas_csv.get('Maestro Deb Int', 0)
    soma_amex_cred = somas_csv.get('Amex Cred', 0) + somas_csv.get('Amex Cred Int', 0)

    somas_csv['Visa Cred'] = soma_visa_cred
    somas_csv['Visa Deb'] = soma_visa_deb
    somas_csv['Master Cred'] = soma_master_cred
    somas_csv['Maestro Deb'] = soma_maestro_deb
    somas_csv['Amex Cred'] = soma_amex_cred

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
                if isinstance(valor, str):
                    valor = valor.replace("R$", "").replace(",", "").strip()
                valores_extraidos[label] = float(valor)

    return valores_extraidos

# Função para exibir no Streamlit
def exibir_comparacao(somas_excel, somas_csv):
    for label in somas_excel:
        sistema_valor = somas_excel[label]
        bin_valor = somas_csv.get(label, 0)
        diferenca = bin_valor + sistema_valor
        
        if diferenca != 0:
            st.markdown(f"{label}: Sistema = {sistema_valor:,.2f} | Bin = {bin_valor:,.2f} | **DIFERENÇA = {diferenca:,.2f}**", unsafe_allow_html=True)
        else:
            st.markdown(f"{label}: Sistema = {sistema_valor:,.2f} | Bin = {bin_valor:,.2f} | DIFERENÇA = 0.00", unsafe_allow_html=True)

def main():
    st.title('Comparação entre Sistema e Bin')

    uploaded_excel = st.file_uploader("📎 Faça o upload do arquivo Excel (.xls)", type=["xls"])

    if uploaded_excel is not None:
        st.info(f"Arquivo enviado: `{uploaded_excel.name}`")

        # Verifica se a extensão termina com .xls (evita arquivos com .xls.xlsx ou similares)
        if not uploaded_excel.name.lower().endswith(".xls"):
            st.error("❌ O arquivo enviado parece não ser um .xls válido. Verifique se a extensão está correta.")
            st.stop()

        df_excel = carregar_excel(uploaded_excel)
        if df_excel is None:
            st.stop()
        st.success("✅ Planilha Excel carregada com sucesso!")

    uploaded_csv = st.file_uploader("📄 Faça o upload do arquivo CSV", type=["csv"])
    if uploaded_csv is not None and uploaded_excel is not None:
        somas_csv = conciliacao_financeira(uploaded_csv)
        valores_excel = extrair_dados_excel(df_excel)
        exibir_comparacao(valores_excel, somas_csv)

if __name__ == "__main__":
    main()
