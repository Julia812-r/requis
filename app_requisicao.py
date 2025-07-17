import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Só inicializa uma vez
if not firebase_admin._apps:
    import json

    # Carregar a chave do secrets
    firebase_config = dict(st.secrets["firebase"])

    cred = credentials.Certificate(firebase_config)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

db = firestore.client()

# Caminho dos arquivos
REQ_FILE = "requisicoes.csv"
ALMOX_FILE = "almox.csv"

st.set_page_config(page_title="Sistema de Requisições", layout="wide")

# CSS customizado para layout
st.markdown("""
    <style>
    .titulo-principal {
        font-size: 48px;
        font-weight: 700;
        color: black;
        text-align: center;
        margin-bottom: 20px;
        font-family: 'Arial Black', Gadget, sans-serif;
    }
    section[data-testid="stSidebar"] div[role="listbox"] > div {
        color: white !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #2f2f2f !important;
    }
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] .css-1v0mbdj.etr89bj1,
    section[data-testid="stSidebar"] .st-cf {
        color: white !important;
    }
    h2, h3 {
        color: black !important;
        font-weight: 600 !important;
    }
    .stButton>button {
        background-color: #0047AB;
        color: white;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #003580;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

def gerar_numero():
    return f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def gerar_link_download(caminho_arquivo):
    caminho_arquivo = str(caminho_arquivo) if not pd.isna(caminho_arquivo) else ""
    if caminho_arquivo and os.path.exists(caminho_arquivo) and os.path.isfile(caminho_arquivo):
        with open(caminho_arquivo, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(caminho_arquivo)}">📥 Baixar Orçamento</a>'
        return href
    else:
        return "Nenhum arquivo anexado"

# Verificação inicial dos arquivos
if not os.path.exists(REQ_FILE):
    pd.DataFrame(columns=[
        'Número Solicitação', 'Nome do Solicitante', 'Métier', 'Tipo', 'Itens',
        'Linha de Projeto', 'Produto Novo ou Previsto', 'Demanda Nova ou Prevista', 
        'Valor Total', 'Caminho Orçamento', 'Comentários', 'Riscos', 'Status', 
        'Data Solicitação', 'Tipo de Compra'
    ]).to_csv(REQ_FILE, index=False)

if not os.path.exists(ALMOX_FILE):
    pd.DataFrame(columns=[
        'Nome do Solicitante', 'MABEC', 'Descrição do Produto', 'Quantidade', 'Data Solicitação'
    ]).to_csv(ALMOX_FILE, index=False)

if 'df_requisicoes' not in st.session_state:
    st.session_state.df_requisicoes = pd.read_csv(REQ_FILE)

if 'df_almox' not in st.session_state:
    st.session_state.df_almox = pd.read_csv(ALMOX_FILE)

if 'itens' not in st.session_state:
    st.session_state.itens = []

# Título principal
st.markdown('<div class="titulo-principal">RENAULT</div>', unsafe_allow_html=True)

abas = [
    "Nova Solicitação de Requisição",
    "Conferir Status de Solicitação",
    "Solicitação Almox",
    "Histórico (Acesso Restrito)"
]
aba = st.sidebar.selectbox("Selecione a aba", abas)

# ---- ABA NOVA REQUISIÇÃO ----
if aba == "Nova Solicitação de Requisição":
    st.title("Nova Solicitação de Requisição")

    nome = st.text_input("Nome do Solicitante")
    metier = st.text_input("Métier")
    tipo = st.radio("É serviço ou produto?", ["Serviço", "Produto"])
    novo_previsto = st.selectbox("É produto novo ou backup?", ["", "Novo", "Backup"], index=0)
    demanda_tipo = st.radio("É uma demanda nova ou prevista?", ["Nova", "Prevista"])
    projeto = st.text_input("Linha de Projeto")
    tipo_compra = st.radio("A compra é:", [
        "Ordinária (papelaria, limpeza, etc.)",
        "Emergenciais (situações imprevistas)",
        "Projetos (itens específicos para ações pontuais)",
        "Serviços (transporte, manutenção, calibração, etc.)"
    ])
    riscos = st.text_area("Riscos envolvidos na não execução desta demanda", height=150)
    comentarios = st.text_area("Comentários", height=150)
    orcamento = st.file_uploader("Anexar Orçamento (opcional)", type=["pdf", "jpg", "jpeg", "png", "doc", "docx"])

    st.subheader("Adicionar Itens da Solicitação")
    with st.form(key='item_form', clear_on_submit=True):
        descricao = st.text_input("Descrição do Item")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        valor_unitario = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")
        adicionar = st.form_submit_button("Adicionar Item")
        if adicionar:
            st.session_state.itens.append({
                "Descrição": descricao,
                "Quantidade": quantidade,
                "Valor Unitário": valor_unitario,
                "Subtotal": quantidade * valor_unitario
            })

    if st.session_state.itens:
        st.write("Itens adicionados:")
        for i, item in enumerate(st.session_state.itens):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"{i+1}. {item['Descrição']} — {item['Quantidade']}× R$ {item['Valor Unitário']:.2f} = R$ {item['Subtotal']:.2f}")
            with col2:
                if st.button("🗑️ Remover", key=f"remover_{i}"):
                    st.session_state.itens.pop(i)
                    st.rerun()


        valor_total = sum(item["Subtotal"] for item in st.session_state.itens)
        st.markdown(f"### Valor Total: R$ {valor_total:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
    else:
        valor_total = 0.0

    confirmar_envio = st.checkbox("Confirmo que revisei todas as informações e desejo enviar a solicitação.")
    enviar = st.button("Enviar Solicitação")
    if enviar:

        if not st.session_state.itens:
            st.warning("Adicione ao menos um item antes de enviar.")
        elif not confirmar_envio:
            st.warning("Marque a caixa de confirmação antes de enviar a solicitação.")
        else:
            numero = gerar_numero()
            caminho_arquivo = ""

            if orcamento:
                os.makedirs("uploads", exist_ok=True)
                caminho_arquivo = os.path.join("uploads", f"{numero}_{orcamento.name}")
                with open(caminho_arquivo, "wb") as f:
                    f.write(orcamento.read())

            nova_linha = pd.DataFrame([{
                'Número Solicitação': numero,
                'Nome do Solicitante': nome,
                'Métier': metier,
                'Tipo': tipo,
                'Itens': str(st.session_state.itens),
                'Linha de Projeto': projeto,
                'Produto Novo ou Previsto': novo_previsto,
                'Demanda Nova ou Prevista': demanda_tipo,
                'Valor Total': valor_total,
                'Caminho Orçamento': caminho_arquivo,
                'Comentários': comentarios,
                'Riscos': riscos,
                'Status': 'Aprovação Comitê de Compras',
                'Data Solicitação': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Tipo de Compra': tipo_compra
            }])

            db.collection("requisicoes").add(nova_linha.to_dict(orient='records')[0])
            st.session_state.itens = []
            st.success(f"Solicitação enviada com sucesso! Número: {numero}")

# ---- ABA STATUS ----
elif aba == "Conferir Status de Solicitação":
    st.title("Consultar Status da Solicitação")
    filtro_nome = st.text_input("Filtrar por Nome")
    filtro_numero = st.text_input("Filtrar por Número da Solicitação")
    docs = db.collection("requisicoes").stream()
    df_data = [doc.to_dict() for doc in docs]
    df = pd.DataFrame(df_data)

    if filtro_nome:
        df = df[df['Nome do Solicitante'].str.lower().str.contains(filtro_nome.lower())]
    if filtro_numero:
        df = df[df['Número Solicitação'].str.upper() == filtro_numero.upper()]

    if df.empty:
        st.info("Nenhuma solicitação encontrada.")
    else:
        st.dataframe(df[['Número Solicitação', 'Nome do Solicitante', 'Status', 'Itens', 'Data Solicitação']], use_container_width=True)

# ---- ABA ALMOX ----
elif aba == "Solicitação Almox":
    st.title("Solicitação para o Almoxarifado")
    st.subheader("PRAZO ESTIMADO DE TRATAMENTO - 2 DIAS")
    
    nome = st.text_input("Nome do Solicitante")

    if 'almox_itens' not in st.session_state:
        st.session_state.almox_itens = []

    with st.form(key="form_almox", clear_on_submit=True):
        mabec = st.text_input("MABEC")
        descricao = st.text_input("Descrição do Produto")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        add_item = st.form_submit_button("Adicionar Item")

        if add_item:
            if not nome.strip():
                st.warning("Informe o nome do solicitante antes de adicionar itens.")
            elif not mabec.strip():
                st.warning("Informe o MABEC.")
            elif not descricao.strip():
                st.warning("Informe a descrição do produto.")
            else:
                st.session_state.almox_itens.append({
                    'Nome do Solicitante': nome.strip(),
                    'MABEC': mabec.strip(),
                    'Descrição do Produto': descricao.strip(),
                    'Quantidade': quantidade,
                    'Data Solicitação': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    if st.session_state.almox_itens:
        st.write("Itens para enviar:")
        for i, item in enumerate(st.session_state.almox_itens):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"{i+1}. MABEC: {item['MABEC']} — {item['Descrição do Produto']} (Qtd: {item['Quantidade']})")
            with col2:
                if st.button("🗑️ Remover", key=f"remover_almox_{i}"):
                    st.session_state.almox_itens.pop(i)
                    st.experimental_rerun()

        confirmar_envio_almox = st.checkbox("Confirmo que revisei todas as informações e desejo enviar a solicitação.")
        if st.button("Enviar Solicitação de Almoxarifado"):
            if not confirmar_envio_almox:
                st.warning("Marque a caixa de confirmação antes de enviar.")
            else:
                # Enviar cada item para o Firestore na coleção 'almoxarifado'
                for item in st.session_state.almox_itens:
                    db.collection("almoxarifado").add(item)
                
                st.session_state.almox_itens = []
                st.success("Solicitação de almoxarifado enviada com sucesso!")

# ---- ABA HISTÓRICO ----
elif aba == "Histórico (Acesso Restrito)":
    st.title("Histórico de Solicitações - Acesso Restrito")
    senha = st.text_input("Digite a senha de administrador", type="password")

    if senha == "admin123":
        docs = db.collection("requisicoes").stream()
        df_data = [doc.to_dict() for doc in docs]
        df = pd.DataFrame(df_data)

        filtro_nome = st.text_input("Filtrar por nome (opcional)").strip()
        if filtro_nome:
            df = df[df['Nome do Solicitante'].str.lower().str.contains(filtro_nome.lower())]

        filtro_numero = st.text_input("Filtrar por número da solicitação (opcional)").strip()
        if filtro_numero:
            df = df[df['Número Solicitação'].str.upper() == filtro_numero.upper()]

        # Separar as solicitações ainda não tratadas e tratadas
        nao_tratadas = df[df['Status'] == "Aprovação Comitê de Compras"]
        tratadas = df[df['Status'] != "Aprovação Comitê de Compras"]

        st.subheader("Solicitações Ainda Não Tratadas")
        if nao_tratadas.empty:
            st.info("Não há solicitações pendentes para aprovação do Comitê de Compras.")

        else:
            import ast
            for i, row in nao_tratadas.iterrows():
                with st.expander(f"Solicitação: {row['Número Solicitação']} — {row['Nome do Solicitante']}"):
                    st.write(f"**Número Solicitação:** {row['Número Solicitação']}")
                    st.write(f"**Data Solicitação:** {row['Data Solicitação']}")
                    st.write(f"**Nome do Solicitante:** {row['Nome do Solicitante']}")
                    st.write(f"**Métier:** {row['Métier']}")
                    st.write(f"**Tipo:** {row['Tipo']}")
                    st.write(f"**Produto Novo ou Previsto:** {row['Produto Novo ou Previsto']}")
                    st.write(f"**Demanda Nova ou Prevista:** {row['Demanda Nova ou Prevista']}")
                    st.write(f"**Linha de Projeto:** {row['Linha de Projeto']}")
                    st.write(f"**Tipo de Compra:** {row['Tipo de Compra']}")
                    

        st.subheader("Histórico de Requisições")
        import ast  # importa no topo do seu código (ou aqui, se preferir)

        for i, row in df.iterrows():
            with st.expander(f"Solicitação: {row['Número Solicitação']} — {row['Nome do Solicitante']}"):
                st.write(f"**Número Solicitação:** {row['Número Solicitação']}")
                st.write(f"**Data Solicitação:** {row['Data Solicitação']}")
                st.write(f"**Nome do Solicitante:** {row['Nome do Solicitante']}")
                st.write(f"**Métier:** {row['Métier']}")
                st.write(f"**Tipo:** {row['Tipo']}")
                st.write(f"**Produto Novo ou Previsto:** {row['Produto Novo ou Previsto']}")
                st.write(f"**Demanda Nova ou Prevista:** {row['Demanda Nova ou Prevista']}")
                st.write(f"**Linha de Projeto:** {row['Linha de Projeto']}")
                st.write(f"**Tipo de Compra:** {row['Tipo de Compra']}")
        
                # Formatar itens bonitinho
                try:
                    itens_lista = ast.literal_eval(row['Itens'])
                    if isinstance(itens_lista, list):
                        st.write("**Itens:**")
                        for idx, item in enumerate(itens_lista, start=1):
                            st.markdown(
                                f"{idx}. **Descrição:** {item['Descrição']} | "
                                f"**Qtd:** {item['Quantidade']} | "
                                f"**Unitário:** R$ {item['Valor Unitário']:.2f} | "
                                f"**Subtotal:** R$ {item['Subtotal']:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
                           )
                    else:
                        st.write(f"**Itens:** {row['Itens']}")
                except:
                    st.write(f"**Itens:** {row['Itens']}")

                st.write(f"**Valor Total:** R$ {row['Valor Total']:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
                st.write(f"**Riscos:** {row['Riscos']}")
                st.write(f"**Comentários:** {row['Comentários']}")
                st.write(f"**Status:** {row['Status']}")
                st.markdown(gerar_link_download(row['Caminho Orçamento']), unsafe_allow_html=True)
                st.markdown("---")

        st.subheader("Solicitações Tratadas")
        if tratadas.empty:
            st.info("Não há solicitações com status diferente de 'Aprovação Comitê de Compras'.")
        else:
            import ast
            for i, row in tratadas.iterrows():
                with st.expander(f"Solicitação: {row['Número Solicitação']} — {row['Nome do Solicitante']}"):
                    st.write(f"**Número Solicitação:** {row['Número Solicitação']}")
                    st.write(f"**Data Solicitação:** {row['Data Solicitação']}")
                    st.write(f"**Nome do Solicitante:** {row['Nome do Solicitante']}")
                    st.write(f"**Métier:** {row['Métier']}")
                    st.write(f"**Tipo:** {row['Tipo']}")
                    st.write(f"**Produto Novo ou Previsto:** {row['Produto Novo ou Previsto']}")
                    st.write(f"**Demanda Nova ou Prevista:** {row['Demanda Nova ou Prevista']}")
                    st.write(f"**Linha de Projeto:** {row['Linha de Projeto']}")
                    st.write(f"**Tipo de Compra:** {row['Tipo de Compra']}")
                    try:
                        itens_lista = ast.literal_eval(row['Itens'])
                        if isinstance(itens_lista, list):
                            st.write("**Itens:**")
                            for idx, item in enumerate(itens_lista, start=1):
                                st.markdown(
                                    f"{idx}. **Descrição:** {item['Descrição']} | "
                                    f"**Qtd:** {item['Quantidade']} | "
                                    f"**Unitário:** R$ {item['Valor Unitário']:.2f} | "
                                    f"**Subtotal:** R$ {item['Subtotal']:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
                                )
                        else:
                            st.write(f"**Itens:** {row['Itens']}")
                        except:
                            st.write(f"**Itens:** {row['Itens']}")
                        st.write(f"**Valor Total:** R$ {row['Valor Total']:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
                        st.write(f"**Riscos:** {row['Riscos']}")
                        st.write(f"**Comentários:** {row['Comentários']}")
                        st.write(f"**Status:** {row['Status']}")
                        st.markdown(gerar_link_download(row['Caminho Orçamento']), unsafe_allow_html=True)
                        st.markdown("---")
                
        st.subheader("Atualizar Status")
        numero_req_atualizar = st.text_input("Digite o número da solicitação para atualizar status")
        novo_status = st.selectbox("Novo status", [
            "Aprovação Comitê de Compras", "Criação da RC", "Aprovação Fabio Silva",
            "Aprovação Federico Mateos", "Criação Pedido de Compra", "Aguardando Nota fiscal",
            "Aguardando entrega", "Entregue", "Serviço realizado", "Pago",
            "Solicitação Recusada", "Cancelado"
        ])
        if st.button("Atualizar Status"):
            docs = list(db.collection("requisicoes").where("`Número Solicitação`", "==", numero_req_atualizar).stream())
            if docs:
                for doc in docs:
                    db.collection("requisicoes").document(doc.id).update({"Status": novo_status})
                st.success("Status atualizado com sucesso!")
            else:
                st.error("Número da solicitação não encontrado.")

        st.subheader("Excluir Solicitação")
        excluir_numero = st.text_input("Digite o número da solicitação para excluir")
        if excluir_numero:
            docs = list(db.collection("requisicoes").where("`Número Solicitação`", "==", excluir_numero).stream())
            if docs:
                for doc in docs:
                    db.collection("requisicoes").document(doc.id).delete()
                st.success(f"Solicitação {excluir_numero} excluída com sucesso!")
            else:
                st.error("Número de solicitação não encontrado.")

        # Histórico de Solicitações ao Almoxarifado
        st.subheader("Histórico de Solicitações ao Almoxarifado")
        docs_almox = list(db.collection("almoxarifado").stream())
        if not docs_almox:
            st.info("Nenhuma solicitação de almoxarifado encontrada.")
        else:
            df_almox = pd.DataFrame([doc.to_dict() for doc in docs_almox])
            st.dataframe(df_almox, use_container_width=True)

            st.subheader("Excluir Solicitação do Almoxarifado")
            # Mostrar índice + algum dado para facilitar identificação
            st.dataframe(df_almox[['Nome do Solicitante', 'MABEC', 'Descrição do Produto', 'Quantidade', 'Data Solicitação']], use_container_width=True)

            index_almox = st.number_input(
                "Digite o índice da solicitação de almoxarifado a excluir",
                min_value=0,
                max_value=len(docs_almox) - 1,
                step=1
            )
            if st.button("Excluir Solicitação do Almoxarifado"):
                doc_id = docs_almox[index_almox].id
                db.collection("almoxarifado").document(doc_id).delete()
                st.success(f"Solicitação do almoxarifado de índice {index_almox} excluída com sucesso!")

    elif senha != "":
        st.error("Senha incorreta.")                          
