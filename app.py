from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from resume_v4.config import Config
from resume_v4.services.documentos import LeitorDocumentos
from resume_v4.workflow import SistemaV4

st.set_page_config(page_title='Analisador Multiagente V4',page_icon='🧠',layout='wide')

@st.cache_resource(show_spinner='Carregando o sistema multiagente...')
def carregar_sistema() -> SistemaV4:
    return SistemaV4(Config())

@st.cache_resource
def carregar_leitor() -> LeitorDocumentos:
    return LeitorDocumentos(Config())

sistema=carregar_sistema(); leitor=carregar_leitor()

st.title('🧠 Analisador Multiagente de Currículos e Vagas — V4')
st.caption('Sistema local, multilíngue e explicável com LangGraph, ESCO, BGE-M3, reranqueamento, privacidade e auditoria.')

with st.sidebar:
    st.header('Configuração')
    modo=st.radio('Forma de entrada',['Colar textos','Enviar arquivos'],index=0)
    rigor=st.select_slider('Rigor da comparação',options=['Flexível','Equilibrado','Conservador'],value='Equilibrado')
    st.info('No modo completo, os modelos são baixados na primeira execução. Sem eles, o sistema usa TF-IDF + RapidFuzz automaticamente.')
    if st.button('Limpar análise atual',use_container_width=True):
        st.session_state.pop('resultado_v4',None); st.rerun()

curriculo=''; vaga=''
if modo=='Colar textos':
    c1,c2=st.columns(2)
    with c1:
        curriculo=st.text_area('Currículo',height=360,key='curriculo_texto',placeholder='Cole o currículo em português ou inglês...')
    with c2:
        vaga=st.text_area('Descrição da vaga',height=360,key='vaga_texto',placeholder='Cole a vaga em português ou inglês...')
else:
    c1,c2=st.columns(2)
    with c1:
        arq_curriculo=st.file_uploader('Currículo (PDF, DOCX, TXT ou MD)',type=['pdf','docx','txt','md'])
        if arq_curriculo:
            try:
                leitura=leitor.ler_upload(arq_curriculo,arq_curriculo.name); curriculo=leitura['texto']
                st.success(f"Currículo lido com {leitura['metodo']}.")
                with st.expander('Pré-visualizar currículo extraído'): st.text(curriculo[:5000])
            except Exception as erro: st.error(f'Não foi possível ler o currículo: {erro}')
    with c2:
        arq_vaga=st.file_uploader('Vaga (PDF, DOCX, TXT ou MD)',type=['pdf','docx','txt','md'])
        if arq_vaga:
            try:
                leitura=leitor.ler_upload(arq_vaga,arq_vaga.name); vaga=leitura['texto']
                st.success(f"Vaga lida com {leitura['metodo']}.")
                with st.expander('Pré-visualizar vaga extraída'): st.text(vaga[:5000])
            except Exception as erro: st.error(f'Não foi possível ler a vaga: {erro}')

if st.button('Executar análise multiagente',type='primary',use_container_width=True):
    if not curriculo.strip() or not vaga.strip():
        st.error('Informe o currículo e a descrição da vaga.')
    else:
        with st.spinner('Os agentes estão analisando, recuperando evidências e auditando o resultado...'):
            try:
                st.session_state['resultado_v4']=sistema.analisar(curriculo,vaga,rigor=rigor)
            except Exception as erro:
                st.exception(erro)

resultado=st.session_state.get('resultado_v4')
if resultado:
    pontuacao=resultado['pontuacao']; score=int(pontuacao.get('score_geral',0)); categorias=pontuacao.get('scores_categoria',{})
    m=st.columns(5)
    m[0].metric('Compatibilidade geral',f'{score}%',pontuacao.get('nivel','Baixa'))
    itens=list(categorias.items())[:3]
    for i in range(1,4):
        if i-1<len(itens): m[i].metric(itens[i-1][0],f'{itens[i-1][1]}%')
        else: m[i].metric('Categoria','—')
    m[4].metric('Ciclo de revisão','Executado' if resultado.get('revisoes',0)>0 else 'Não necessário')
    st.progress(score/100)

    abas=st.tabs(['Visão geral','Requisitos e evidências','Currículo','Vaga','Recomendações','Privacidade','Auditoria','Rastreio','Histórico','Downloads'])
    with abas[0]:
        st.subheader('Pontuação por categoria')
        if categorias:
            quadro=pd.DataFrame({'Categoria':list(categorias.keys()),'Pontuação':list(categorias.values())}).set_index('Categoria')
            st.bar_chart(quadro)
        cont=pontuacao.get('contagens',{}); c=st.columns(3)
        c[0].metric('Atendidos',cont.get('atendido',0)); c[1].metric('Parciais',cont.get('parcial',0)); c[2].metric('Ausentes',cont.get('ausente',0))
        st.write(resultado['revisao'].get('texto_final',''))
        status=resultado.get('status_motor',{})
        st.caption(f"Recuperação: {status.get('modelo_embeddings','fallback')} | Reranker: {status.get('modelo_reranker','fallback')}")

    with abas[1]:
        linhas=[]
        for item in pontuacao.get('resultados',[]):
            linhas.append({'Requisito':item.get('texto'),'Prioridade':item.get('prioridade'),'Categoria':item.get('categoria'),'Status':item.get('status'),'Pontuação':item.get('score_final'),'Evidência do currículo':item.get('evidencia') or 'Nenhuma evidência','Método':f"{item.get('metodo')} / {item.get('metodo_reranker')}"})
        df=pd.DataFrame(linhas)
        if not df.empty:
            filtros=st.multiselect('Filtrar status',['atendido','parcial','ausente'],default=['atendido','parcial','ausente'])
            st.dataframe(df[df['Status'].isin(filtros)],use_container_width=True,hide_index=True)
        else: st.warning('Nenhum requisito foi estruturado.')

    with abas[2]:
        perfil=resultado['perfil_curriculo']
        st.subheader(perfil.get('candidato','Candidato'))
        st.write('**Competências detectadas:**',', '.join(i['rotulo'] for i in perfil.get('competencias',[])) or 'Nenhuma')
        st.json({'formacao':perfil.get('formacao',[]),'experiencia':perfil.get('experiencia',[]),'projetos':perfil.get('projetos',[]),'anos_mencionados':perfil.get('anos_mencionados',[])})

    with abas[3]:
        perfil=resultado['perfil_vaga']; st.subheader(perfil.get('titulo','Vaga'))
        req=pd.DataFrame(perfil.get('requisitos',[]))
        if not req.empty:
            cols=[c for c in ['texto','prioridade','categoria','tipo','origem'] if c in req.columns]
            st.dataframe(req[cols],use_container_width=True,hide_index=True)

    with abas[4]:
        rec=pd.DataFrame(resultado.get('recomendacoes',[]))
        if not rec.empty: st.dataframe(rec,use_container_width=True,hide_index=True)

    with abas[5]:
        priv=resultado.get('privacidade',{})
        st.metric('Entidades pessoais removidas',len(priv.get('entidades',[])))
        st.write('**Método:**',priv.get('metodo'))
        st.dataframe(pd.DataFrame(priv.get('entidades',[])),use_container_width=True,hide_index=True)
        with st.expander('Texto anonimizado utilizado na comparação'): st.text(resultado.get('curriculo_anonimizado',''))

    with abas[6]:
        revisao=resultado.get('revisao',{})
        if revisao.get('decisao')=='aprovado': st.success(revisao.get('texto_final'))
        else: st.warning(revisao.get('texto_final'))
        for problema in revisao.get('problemas',[]): st.write(f'- {problema}')
        st.caption('A ferramenta não substitui recrutadores, entrevistas ou avaliação humana.')

    with abas[7]:
        st.dataframe(pd.DataFrame(resultado.get('rastreio',[])),use_container_width=True,hide_index=True)

    with abas[8]:
        hist=pd.DataFrame(sistema.historico.listar())
        if not hist.empty: st.dataframe(hist,use_container_width=True,hide_index=True)
        else: st.info('Nenhuma análise salva ainda.')

    with abas[9]:
        st.download_button('Baixar relatório Markdown',resultado.get('relatorio_markdown',''),'relatorio_curriculo_vaga.md','text/markdown',use_container_width=True)
        st.download_button('Baixar dados JSON',resultado.get('relatorio_json',json.dumps({},indent=2)),'analise_curriculo_vaga.json','application/json',use_container_width=True)
        csv=pd.DataFrame(pontuacao.get('resultados',[])).to_csv(index=False).encode('utf-8-sig')
        st.download_button('Baixar requisitos em CSV',csv,'requisitos_evidencias.csv','text/csv',use_container_width=True)
        st.subheader('Prévia do relatório'); st.markdown(resultado.get('relatorio_markdown',''))
