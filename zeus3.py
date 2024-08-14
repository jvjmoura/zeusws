import streamlit as st
from pathlib import Path
from openai import OpenAI
import pydub
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv, find_dotenv
import os

_ = load_dotenv(find_dotenv())

PASTA_TEMP = Path(__file__).parent / 'temp'
PASTA_TEMP.mkdir(exist_ok=True)
ARQUIVO_AUDIO_TEMP = PASTA_TEMP / 'audio.mp3'
ARQUIVO_VIDEO_TEMP = PASTA_TEMP / 'video.mp4'

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcreve_audio(caminho_audio):
    with open(caminho_audio, 'rb') as arquivo_audio:
        transcricao = client.audio.transcriptions.create(
            model='whisper-1',
            language='pt',
            response_format='text',
            file=arquivo_audio,
        )
        return transcricao

def analisa_transcricao(transcricao):
    prompt = f"""
    Com base nas informações contidas na seguinte transcrição, crie uma tabela Markdown com as seguintes colunas:

    1. 'Tipo de Áudio': Identifique o tipo geral de áudio (ex: entrevista, palestra, conversa informal, etc.).
    2. 'Interlocutor': Identifique quem está falando, se possível. Se não for possível identificar especificamente, use "Interlocutor 1", "Interlocutor 2", etc., para diferentes vozes.
    3. 'Conteúdo': Resuma o conteúdo apresentado por cada interlocutor, sem fazer juízos de valor. Priorize informações como datas, nomes e eventos principais.
    4. 'Detalhes': Inclua quaisquer detalhes ou informações adicionais mencionados.
    5. 'Contexto/Tom': Capture o clima geral da conversa ou emoções expressas.
    6. 'Elementos não-verbais': Note pausas significativas, interrupções, sobreposições de fala ou outros elementos relevantes.
    7. 'Observações': Anote ambiguidades, contradições, ou informações que precisem de esclarecimento.

    Regras adicionais:
    - Se não for possível distinguir interlocutores diferentes, use "Narrador" como interlocutor.
    - Se houver uma mudança clara de tópico ou uma nova informação sendo introduzida, crie uma nova linha na tabela, mesmo que seja o mesmo interlocutor.
    - Foque em apresentar o conteúdo de forma neutra, sem interpretar ou avaliar as informações.
    - Mantenha cada ponto conciso, mas informativo.
    - Se alguma informação não estiver clara ou não for mencionada, indique como "Não especificado".
    - Para transcrições longas, foque nas informações mais relevantes e significativas.
    - Consolide informações repetidas, mencionando a frequência da repetição se relevante.
    - Destaque e explique brevemente termos técnicos ou jargões específicos.
    - Marque informações potencialmente sensíveis ou confidenciais, resumindo-as de forma ética.

    Após a tabela, adicione uma seção "Resumo" que deve apresentar, de forma objetiva e sem interpretações:
    - Tipo e duração aproximada do áudio
    - Endereços citados
    - Quando ocorreram os fatos
    - O que aconteceu
    - Horário, dia e mês dos eventos mencionados
    - Um resumo geral dos principais fatos narrados
    - Quaisquer termos técnicos ou jargões frequentes, com breves explicações

    Importante: 
    - No resumo, não crie nenhuma informação nova. Restrinja-se estritamente ao conteúdo da transcrição. 
    - Se alguma dessas informações não estiver presente na transcrição, indique como "Não mencionado na transcrição".
    - Adapte a extensão e o nível de detalhe do resumo de acordo com a duração do áudio.
    - Se houver informações contraditórias ou ambíguas, mencione-as claramente no resumo.

    Transcrição:
    {transcricao}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um assistente especializado em analisar e resumir transcrições de áudio de forma detalhada e estruturada."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def exibe_resultado(transcricao):
    st.subheader("Transcrição Original")
    st.write(transcricao)

    st.subheader("Análise Detalhada da Transcrição")
    with st.spinner("Analisando a transcrição..."):
        analise = analisa_transcricao(transcricao)
    st.markdown(analise)

def _salva_audio_do_video(video_bytes):
    with open(ARQUIVO_VIDEO_TEMP, mode='wb') as video_f:
        video_f.write(video_bytes.read())
    moviepy_video = VideoFileClip(str(ARQUIVO_VIDEO_TEMP))
    moviepy_video.audio.write_audiofile(str(ARQUIVO_AUDIO_TEMP))

def transcreve_tab_video():
    arquivo_video = st.file_uploader('Adicione um arquivo de vídeo .mp4', type=['mp4'])
    if arquivo_video is not None:
        with st.spinner("Processando o vídeo..."):
            _salva_audio_do_video(arquivo_video)
            transcricao = transcreve_audio(ARQUIVO_AUDIO_TEMP)
        exibe_resultado(transcricao)

def transcreve_tab_audio():
    arquivo_audio = st.file_uploader('Adicione um arquivo de áudio .mp3 ou .m4a', type=['mp3', 'm4a'])
    if arquivo_audio is not None:
        with st.spinner("Transcrevendo o áudio..."):
            if arquivo_audio.type == 'audio/m4a':
                # Converter M4A para MP3
                audio = pydub.AudioSegment.from_file(arquivo_audio, format="m4a")
                audio.export(ARQUIVO_AUDIO_TEMP, format="mp3")
                arquivo_para_transcricao = ARQUIVO_AUDIO_TEMP
            else:
                arquivo_para_transcricao = arquivo_audio

            transcricao = client.audio.transcriptions.create(
                model='whisper-1',
                language='pt',
                response_format='text',
                file=arquivo_para_transcricao,
            )
        exibe_resultado(transcricao)

def sidebar_info():
    # Logotipo
    logo_url = "https://cdn.midjourney.com/143dff27-3598-4ca6-becb-e6387047a007/0_1.png"  # Substitua pela URL real do seu logotipo
    st.sidebar.image(logo_url, use_column_width=True, caption="Zeus Whisper")

    st.sidebar.title("Como usar o Zeus Whisper")
    st.sidebar.markdown("""
    1. Escolha entre as opções 'Vídeo' ou 'Áudio'.
    2. Faça upload do seu arquivo de vídeo (.mp4) ou áudio (.mp3 ou .m4a).
    3. Aguarde o processamento e a transcrição.
    4. Revise a transcrição e a análise detalhada gerada.
    """)
    
    st.sidebar.info("Lembre-se: A qualidade da transcrição depende da clareza do áudio original.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Informações sobre o Projeto")
    st.sidebar.markdown("**Status:** Em construção")
    st.sidebar.markdown("**Desenvolvedor:** João Valério")
    st.sidebar.markdown("**Cargo:** Juiz do TJPA")
    st.sidebar.markdown("Esta programação Python está atualmente em desenvolvimento.")

def main():
    st.set_page_config(page_title="Zeus Whisper", layout="wide")
    
    sidebar_info()
    
    st.title('Zeus Whisper 🎙️')
    st.markdown('#### Transcreva e analise áudio de vídeos e arquivos de áudio')
    
    tab_video, tab_audio = st.tabs(['Vídeo', 'Áudio'])
    
    with tab_video:
        st.header("Transcrição de Vídeo")
        transcreve_tab_video()
    
    with tab_audio:
        st.header("Transcrição de Áudio")
        transcreve_tab_audio()

if __name__ == '__main__':
    main()