#
# 키워드로 뉴스를 검색해서 워드 클라우드 시각화해주는 앱을 만들어 본다.
#

# 먼저 커맨드라인에서 다음과 같이 라이브러리 설치 필요.
# pip install streamlit
# pip install streamlit-lottie
# pip install requests
# pip install pandas
# pip install numpy
# pip install matplotlib
# pip install beautifulsoup4
# pip install wordcloud
# pip install soynlp
# pip install pillow

# 필요한 라이브러리를 불러온다.
import json
from PIL import Image
import bs4                      # 파싱.
import re                       # 정규표현식.
import requests as rq           # HTTP/API 자료 요청.
import pandas as pd
import numpy as np
import pickle
import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from streamlit_lottie import st_lottie

# JSON을 읽어 들이는 함수.
def loadJSON(path):
    f = open(path, 'r')
    res = json.load(f)
    f.close()
    return res

# 뉴스 검색 결과를 반환해 주는 함수.
def getRequest(keyword, display, start):
    # 다음 사이트를 참고해 본다.
    # https://developers.naver.com/docs/serviceapi/search/news/news.md#%EB%89%B4%EC%8A%A4
    url = f'https://openapi.naver.com/v1/search/news.json?query={keyword}&display={display}&start={start}'
    # 헤더에 Client ID와 Client Secret를 태워서 보낸다.
    headers = {'X-Naver-Client-Id':st.session_state['client_id'] , 'X-Naver-Client-Secret':st.session_state['client_secret']}
    # 데이터를 요청하고 상태를 본다.
    res = rq.get(url, headers=headers)
    # JSON으로 내려받은 정보를 parsing한다.
    my_json = json.loads(res.text)
    # 'items' 항목들을 반환한다.
    return my_json['items']

# 텍스트 데이터를 정제해 주는 함수.
# 주로 정규 표현식을 사용한다.
@st.cache_data
def cleanText(text):
    text = re.sub(r'\d|[a-zA-Z]|\W',' ', text)   # 수치, 알파벳, 특수문자 제거.
    text = re.sub(r'\s+',' ', text)              # 잉여 공백 1개로 줄임.
    return text

# 사전 트레이닝된 토크나이저를 불러오는 함수.
@st.cache_resource
def getTokenizer():
    f = open('./models/my_tokenizer1.model','rb')
    tokenizer = pickle.load(f)
    f.close()
    return tokenizer

# 토큰화된 텍스트를 도수표로 정리해서 딕셔너리 형태로 변환해 주는 함수.
def makeTable(tokens, nmin=2, nmax=5, ncut=1):
    tokens_new = []
    # 조건에 맞는 토큰만 가져옴.
    for token in tokens:
        if len(token) >= nmin and len(token) <= nmax:         
            tokens_new.append(token)
    # Pandas 시리즈로 테이블화.
    ser = pd.Series(tokens_new)
    ser = ser.value_counts()
    ser = ser[ser >= ncut]                          # 최소 횟수 이상만.
    return dict(ser.sort_values(ascending=False))   # 내림차순 정렬해서 반환.

# 워드 클라우드 시각화 함수.
def plotChart(count_dict, back_mask, max_words_, container):
    # 백그라운드 마스크 이미지.
    if back_mask == '타원':
        img = Image.open('./resources/background_1.png')                    # 타원형.
    elif back_mask == '말풍선':
        img = Image.open('./resources/background_2.png')                    # 말풍선.
    elif back_mask == '하트':
        img = Image.open('./resources/background_3.png')                    # 하트.
    else:
        img = Image.open('./resources/background_0.png')
    my_mask=np.array(img)                                                   # 워드 클라우드의 요구사항.
    # 워드 클라우드 객체.
    wc = WordCloud(font_path='./resources/NanumSquareR.ttf',                # 한글글꼴 파일 경로.
                    background_color='white',
                    contour_color='grey',
                    contour_width=3,
                    max_words=max_words_,
                    mask=my_mask)   
    # 토큰 (단어)의 도수표 (dict)를 사용해서 생성.
    wc.generate_from_frequencies(count_dict)
    fig = plt.figure(figsize=(10,10))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")                                                         # 가로/세로 축을 꺼줌.
    container.pyplot(fig)

# 로고 Lotti와 타이틀 출력.
col1, col2 = st.columns([1,2])
with col1:
    lottie = loadJSON('./resources/lottie-full-movie-experience-including-music-news-video-weather-and-lots-of-entertainment.json')
    st_lottie(lottie, speed=1, loop=True, width=200, height=200)
with col2:
    ''
    ''
    ''
    st.title('뉴스 키워드 시각화')

# 세션 상태를 초기화 한다.
if 'client_id' not in st.session_state:
    st.session_state['client_id'] = ''                  # 각자 본인의 것으로 설정 가능.

if 'client_secret' not in st.session_state:
    st.session_state['client_secret'] = ''              # 각자 본인의 것으로 설정 가능.

#  Sidebar 에서 Client ID 와 Client Secret을 입렵 받는다.
with st.sidebar.form(key="client_settings", clear_on_submit=False):
    st.header('API 설정')
    client_id = st.text_input('Client ID:', value= st.session_state['client_id'] )
    client_secret = st.text_input('Client Secret:', type='password', value=st.session_state['client_secret'])    # 비밀번호 같이 가려둔다.
    if st.form_submit_button(label="OK"):
        st.session_state['client_id'] = client_id
        st.session_state['client_secret'] = client_secret
        st.experimental_rerun()

# 워드 클라우드 차트가 출력될 위치.
chart_container = st.empty()

# 입력 폼 (메인).
with st.form('search', clear_on_submit=False):
     search_keyword = st.selectbox('분야:', ['경제', '정치', '사회', '국제', '연예', 'IT', '문화'])
     data_amount = st.slider('분량:',min_value=1, max_value=5, step=1, value=1)
     back_mask = st.radio('백마스크:',['없음', '타원', '말풍선', '하트',],horizontal=True)
     if st.form_submit_button('OK'):
        chart_container.info(':red[데이터 가져오는 중...]')
        corpus = ''                                                         # 말뭉치 초기화.
        items = []
        for i in range(data_amount):
            items.extend( getRequest(search_keyword, 100, 100*i + 1 ) )     # API로 데이터 가져옴.
        for item in items:
            if 'n.news.naver' in item['link']:                              # 네이버 뉴스 링크만 가져온다. 
                news_url = item['link']
                res = rq.get(news_url, headers={'User-Agent':'Mozilla'})    # 헤더에 User-Agent 정보를 넣어서 차단을 피한다.
                soup = bs4.BeautifulSoup(res.text, 'html.parser')           # 파싱 진행.
                news_tag = soup.select_one('#dic_area')                     # 뉴스 본문을 품고있는 태그에 접근.
                if news_tag:                                                # 뉴스 태그를 제대로 가져온 경우.
                    corpus += news_tag.text+ '/n'

        if len(corpus) > 100:                                               # 말뭉치에 최소 100개 이상의 문자가 들어있는 경우.
            chart_container.info(':red[이미지 생성 중...]')
            corpus = cleanText(corpus)
            my_tokenizer = getTokenizer()
            tokens = my_tokenizer.tokenize(corpus, flatten=True)
            count_dict = makeTable(tokens)
            plotChart(count_dict, back_mask, 70, chart_container)
        else:
            chart_container.error(':red[데이터 불충분 오류!]')
