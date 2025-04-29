import streamlit as st
import pandas as pd

# Função de pré-processamento e cálculo das somas no CSV
def conciliacao_financeira(arquivo_csv):
    # Carregar o arquivo CSV
    bandeiras_df = pd.read_csv(arquivo_csv, sep=";", encoding="ISO-8859-1")

    # Limpeza de dados
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].replace({r'R\$': '', r'\.': '', ' ': ''}, regex=True)
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].str.replace(',', '.', regex=False)
    bandeiras_df['Valor bruto'] = bandeiras_df['Valor bruto'].astype(float)

    # Filtrar apenas "Status" válidos
    bandeiras_df = bandeiras_df[~bandeiras_df['Status'].isin(['Recusada', 'Estornada'])]

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

    # Ajustes de soma das categorias Int
    somas_csv['Visa Cred'] += somas_csv.get('Visa Cred Int', 0)
    somas_csv['Visa Deb'] += somas_csv.get('Visa Deb Int', 0)
    somas_csv['Master Cred'] += somas_csv.get('Master Cred Int', 0)
    somas_csv['Maestro Deb'] += somas_csv.get('Maestro Deb Int', 0)
    somas_csv['Amex Cred'] += somas_csv.get('Amex Cred Int', 0)

    return somas_csv

# Função para extrair dados do Excel
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
                valores_extraidos[label] = float(str(valor).replace('.', '').replace(',', '.'))

    return valores_extraidos

# Função principal do Streamlit
def main():
    st.title("Conciliação Financeira - Sistema x Bin")

    st.write("Faça o upload dos arquivos:")

    arquivo_excel = st.file_uploader("Upload do arquivo Excel (.xls ou .xlsx)", type=["xls", "xlsx"])
    arquivo_csv = st.file_uploader("Upload do arquivo CSV", type=["csv"])

    if arquivo_excel and arquivo_csv:
        try:
            if arquivo_excel.name.lower().endswith('.xls'):
                df = pd.read_excel(arquivo_excel, engine='xlrd')
            elif arquivo_excel.name.lower().endswith('.xlsx'):
                df = pd.read_excel(arquivo_excel, engine='openpyxl')
            else:
                st.error("Arquivo Excel inválido.")
                return

            valores_sistema = extrair_dados_excel(df)
            valores_bin = conciliacao_financeira(arquivo_csv)

            # Garantir que B2B Master Credito sempre apareça
            if "B2B Master Credito" not in valores_bin:
                valores_bin["B2B Master Credito"] = 0

            st.subheader("Resultados da Conciliação:")

            for label in valores_sistema:
                sistema_valor = valores_sistema.get(label, 0)
                bin_valor = valores_bin.get(label, 0)

                # Calcular a diferença (Sistema - Bin) e exibir
                diferenca = abs(sistema_valor - bin_valor)

                st.write(f"{label}: Sistema = R${sistema_valor:,.2f} | Bin = R${bin_valor:,.2f}")

                # Exibe a diferença em caso de divergência
                if diferenca != 0:
                    st.markdown(
                        f"<p style='color:red; font-weight:bold;'>Soma Total (Sistema - Bin) = R${diferenca:,.2f}</p>",
                        unsafe_allow_html=True
                    )
                else:
                    st.write(f"Soma Total (Sistema - Bin) = R${diferenca:,.2f}")

        except Exception as e:
            st.error(f"Erro ao carregar os arquivos: {e}")

if __name__ == "__main__":
    main()
