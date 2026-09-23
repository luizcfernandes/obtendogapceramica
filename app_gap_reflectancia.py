import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- 🛠️ SEUS DOIS SCRIPTS ADAPTADOS ---

# -- função que verifique o cabeçalho do navegador para ver se está sendo executado num celular ou num pc/note
def ehCelular():
    user_agent = st.context.headers.get("User-Agent", "").lower()
    dispositivos_moveis = ["android","iphone", "ipad","windows phone"]
    return any(dispositivo in user_agent for dispositivo in dispositivos_moveis)
  
def exibirAnalisarCurva(arquivo_excel, co_column, ref_column,tipo_transicao_n):
    """
    Primeiro script: Lê o Excel e gera o gráfico inicial.
    """
    df = pd.read_excel(arquivo_excel)
    
    # Limpa espaços em branco dos nomes das colunas
    df.columns = df.columns.str.strip()
    
    coluna_comprimento_onda = co_column     
    coluna_reflectancia_percent = ref_column
    
    # CONSTANTES FÍSICAS PRECISAS (Seu método longo)
    h = 6.62607015e-34       
    c = 299792458            
    ev_to_j = 1.602176634e-19 
    
    # CÁLCULOS
    df['R_fração'] = df[coluna_reflectancia_percent] / 100.0
    df['Alpha_FR'] = ((1.0 - df['R_fração']) ** 2) / (2.0 * df['R_fração'].replace(0, 1e-5))
    df['Energia_eV'] = (h * c) / (df[coluna_comprimento_onda] * 1e-9 * ev_to_j)
    df['Tauc_Indireto'] = (df['Alpha_FR'] * df['Energia_eV']) ** tipo_transicao_n

    df = df.sort_values(by='Energia_eV').reset_index(drop=True)
    
    # Cria a figura e o eixo corretamente
    fig, ax = ax = plt.subplots(figsize=(10, 6.5))
    ax = plt.gca()
    
    
    # Plota os dados usando o objeto 'ax'
    ax.plot(df['Energia_eV'], df['Tauc_Indireto'], 'o-', color='black', linewidth=1.5, label='Espectro Bruto')

    ax.set_title('Script 1: Visualização do Espectro de Tauc para Ajuste de Limites', fontsize=12, fontweight='bold')
    ax.set_xlabel('Energia (eV)', fontsize=11)
    if tipo_transicao_n == 2:
    	ax.set_ylabel(r'Fator de Tauc $(F(R) \cdot h\nu)^{2}$', fontsize=11)
    else:
    	ax.set_ylabel(r'Fator de Tauc $(F(R) \cdot h\nu)^{0.5}$', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    
    # 1. Configura as marcas principais (Major) para irem de 1 em 1
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1.0))

    # 2. Configura as marcas secundárias (Minor) para aparecerem a cada 0.5
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))

    # 3. Personaliza o tamanho visual de cada tipo de tracinho
    ax.tick_params(axis='x', which='major', length=10, width=2, labelsize=12)
    ax.tick_params(axis='x', which='minor', length=6, width=1.5)

    return fig, df


def calcularGap(df, valor_min, valor_max):
    """
    Segundo script: Recebe o DataFrame e os limites mínimo e máximo.
    """    
    # ==========================================
    # 3. AJUSTE ROBUSTO POR REGRESSÃO LINEAR (MÍNIMOS QUADRADOS)
    # ==========================================
    # Filtra os dados na janela limpa que você mapeou
    df_janela = df[(df['Energia_eV'] >= valor_min) & (df['Energia_eV'] <= valor_max)].copy()
    if len(df_janela) < 2:
    	raise ValueError(f"Poucos pontos experimentais encontrados entre {valor_min} eV e {valor_max} eV.")
    
    # np.polyfit calcula a reta média (y = m*x + b) que melhor passa por TODOS os pontos da janela
    m, b = np.polyfit(df_janela['Energia_eV'], df_janela['Tauc_Indireto'], 1)
    
    # Interseção com o eixo X (onde y = 0) -> x = -b/m
    band_gap_calculado = -b / m

    fig, ax = plt.subplots(figsize=(10, 6.5))
    
    # Exemplo de uso dos valores para filtrar a coluna calculada no Script 1:
    # df_filtrado = df[(df['Energia_eV'] >= valor_min) & (df['Energia_eV'] <= valor_max)]
    
    ax.plot(df['Energia_eV'], df['Tauc_Indireto'], 'o-', color='gray', alpha=0.4, label='Espectro Completo')
    # Projeta a reta da regressão linear estendida até o chão (Eixo X)
    x_tangente = np.linspace(band_gap_calculado - 0.1, valor_max + 0.1, 100)
    y_tangente = m * x_tangente + b
    y_tangente_plot = np.where(y_tangente >= 0, y_tangente, np.nan) # Esconde valores abaixo de zero

    # Configurações de layout
    ax.set_title(f'Determinação de Band Gap por Regressão Robusta', fontsize=12, fontweight='bold')
    ax.set_xlabel('Energia (eV)', fontsize=11)
    ax.set_ylabel(r'Fator de Tauc $(F(R) \cdot h\nu)^{0.5}$', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Destaca os pontos da janela ajustada que contém o micro-ombro
    ax.plot(df_janela['Energia_eV'], df_janela['Tauc_Indireto'], 'o', color='darkblue', markersize=6, label='Pontos da Janela Ajustada')
    
    ax.plot(x_tangente, y_tangente_plot, '--', color='red', linewidth=2, label=f'Ajuste Linear (Gap = {band_gap_calculado:.2f} eV)')
    ax.plot(band_gap_calculado, 0, 'ro', markersize=8, label='Interseção Calculada')
    
    # Foca o zoom ao redor do Band Gap calculado
    ax.set_xlim(band_gap_calculado - 0.4, valor_max + 0.6)
    ax.set_ylim(0, max(df_janela['Tauc_Indireto']) * 2.0)
    ax.legend(fontsize=10, loc='upper left')
    
    return fig


# --- 🌐 INTERFACE WEB ---

st.set_page_config(page_title="Analisador de Gráficos", layout="centered")
st.title("📊 Calculando a energia da gap de banda")
# Pegar os valores das colunas na planilha
st.write("⚙️ Entre com o nome das colunas comprimento de onda(nm) e a Reflectância (%) existente na planilha")
col3, col4 = st.columns(2)
with col3:
  COMPRIMENTO_DE_ONDA_COLUMN = st.text_input("Comprimento de Onda:", "nm")
with col4:
  REFLECTANCIA_COLUMN = st.text_input("Reflectância:", "Ref")

st.write("⚙️ Tipo de transição eletrônica do material:")
col5,col6 = st.columns(2)
with col5:
  opcoes = [0.5, 2]
  tipo_transicao_n = st.selectbox("0.5 - Transição indireta, 2 - Transição direta:", options=opcoes)   
     
st.write("⚙️ Inserindo a planilha excel")
# Step 1: Upload do arquivo .xlsx

if ehCelular():
    st.warning("\U0001F4F1. Como está no celular use o formato .csv ao invés de planilhas grandes do excel")
    arquivo_carregado = st.file_uploader("Escolha o arquivo CSV (.csv)", type=["scv"])
else:
    arquivo_carregado =  st.file_uploader("Carregue seu arquivo Excel (.xlsx)", type=["xlsx"])

if arquivo_carregado is not None:
    st.success("Arquivo carregado com sucesso!")
    
    # Executa o Script 1
    figura_1, dados = exibirAnalisarCurva(arquivo_carregado,COMPRIMENTO_DE_ONDA_COLUMN,REFLECTANCIA_COLUMN,tipo_transicao_n)
    
    st.subheader("📈 Primeiro Gráfico (Dados Originais)")
    st.pyplot(figura_1)
    
    st.divider() # Linha divisória na tela
    
    # Step 2: Inputs de Mínimo e Máximo para o próximo script
    st.subheader("⚙️ Configurar Limites para o Próximo Script")
    
    # Pega valores reais da tabela para sugerir nos campos de input do Streamlit
    min_real = float(dados['Energia_eV'].min())
    max_real = float(dados['Energia_eV'].max())
    
    col1, col2 = st.columns(2)
    with col1:
        LIMITE_MIN = st.number_input("Defina o valor MÍNIMO:", value=min_real, step=0.1)
    with col2:
        LIMITE_MAX = st.number_input("Defina o valor MÁXIMO:", value=max_real, step=0.1)
          
    # Validação simples na tela
    if LIMITE_MIN > LIMITE_MAX:
        st.error("Atenção: O valor mínimo não pode ser maior que o valor máximo!")
    
    # Step 3: Botão que dispara o segundo script
    else:
        if st.button("Executar Próximo Script e Gerar Gráfico", type="primary"):
            st.subheader("📉 Segundo Gráfico (Processado com Sucesso)")
            
            # Executa o Script 2 passando as variáveis de mínimo e máximo
            figura_2 = calcularGap(dados, LIMITE_MIN, LIMITE_MAX)
            
            # Mostra o novo gráfico na tela
            st.pyplot(figura_2)

# Adiciona um botão de reset
if st.button("Resetar Tela / Limpar Dados", type="secondary"):
    st.rerun()

# author
st.write("")
st.write("")
st.write("Software desenvolvido by Luiz Carlos Fernandes")
st.write("email: lzcsfs@gmail.com")
