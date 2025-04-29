import pandas as pd
import streamlit as st

# Função para pré-processamento e cálculo das somas no CSV
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
        ('Amex', 'Crédito Internacional', 'Amex Cred Int'),
    ]

    somas_csv = {}

    for bandeira, tipo, nome_categoria in categorias:
        soma = bandeiras_df[
            (bandeiras_df['Bandeira'] == bandeira) &
            (bandeiras_df['Produto'] == tipo)
        ]['Valor bruto'].sum()
        somas_csv[nome_categoria] = soma

    # Combinar categorias *_Int nas suas principais
    somas_csv['Visa Cred'] += somas_csv.get('Visa Cred Int', 0)
    somas_csv['Visa Deb'] += somas_csv.get('Visa Deb Int', 0)
    somas_csv['Master Cred'] += somas_csv.get('Master Cred Int', 0)
    somas_csv['Maestro Deb'] += somas_csv.get('Maestro Deb Int', 0)
    somas_csv['Amex Cred'] += somas_csv.get('Amex Cred Int', 0)

    # Remover categorias *_Int que já foram somadas
    for key in ['Visa Cred Int', 'Visa Deb Int', 'Master Cred Int', 'Maestro Deb Int', 'Amex Cred Int']:
        if key in somas_csv:
            del somas_csv[key]

    return somas_csv

# Função para extrair os dados da planilha Excel
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
                valores_extraidos[label] = valor

    return valores_extraidos

# Função principal (Streamlit)
def main():
    st.title("Conciliação Financeira")

    st.write("Faça upload da planilha Excel (.xls ou .xlsx)")
    arquivo_excel = st.file_uploader("Upload do arquivo Excel", type=["xls", "xlsx"])

    if arquivo_excel is not None:
        try:
            if arquivo_excel.name.lower().endswith('.xls'):
                df_excel = pd.read_excel(arquivo_excel, engine='xlrd')
            elif arquivo_excel.name.lower().endswith('.xlsx'):
                df_excel = pd.read_excel(arquivo_excel, engine='openpyxl')
            else:
                st.error("Formato de arquivo inválido. Envie um arquivo .xls ou .xlsx")
                return
            st.success("Arquivo Excel carregado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo Excel: {e}")
            return

        valores_excel = extrair_dados_excel(df_excel)

        st.write("Faça upload do arquivo CSV")
        arquivo_csv = st.file_uploader("Upload do arquivo CSV", type=["csv"])

        if arquivo_csv is not None:
            try:
                somas_csv = conciliacao_financeira(arquivo_csv)
            except Exception as e:
                st.error(f"Erro ao processar o arquivo CSV: {e}")
                return

            st.header("Comparação de Valores")

            for label in valores_excel.keys():
                valor_excel = valores_excel.get(label, 0)
                valor_csv = somas_csv.get(label, 0)

                soma_total = float(valor_excel) + float(valor_csv)

                if label == "B2B Master Credito":
                    # Sempre mostrar B2B, mesmo que não tenha valor no CSV
                    valor_csv = somas_csv.get(label, 0)

                if abs(soma_total) > 0.01:
                    st.markdown(
                        f"<span style='color: red;'>{label}: Sistema = R${valor_excel:,.2f} | Bin = R${valor_csv:,.2f} | Soma Total = R${soma_total:,.2f}</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.write(f"{label}: Sistema = R${valor_excel:,.2f} | Bin = R${valor_csv:,.2f} | Soma Total = R${soma_total:,.2f}")

if __name__ == "__main__":
    main()
