import streamlit as st
import pandas as pd
import numpy as np
from requests import Session
import json
# import helpers
import plotly.express as px
import altair as alt
from datetime import timedelta
import datetime


class helpers:
    @staticmethod
    def time_in_utc_530():
        utc_time = datetime.datetime.now(datetime.timezone.utc)
        offset = datetime.timedelta(hours=5, minutes=30)
        time_ = utc_time.astimezone(datetime.timezone(offset))
        return time_.strftime("%H:%M:%S %d-%m-%Y")

    @staticmethod
    def get_session(ncfa):
        new_session = Session()
        new_session.cookies.set("_ncfa", ncfa, domain="www.geoguessr.com")
        return new_session

    @staticmethod
    def get_duel_tokens(session):
        BASE_URL_V4 = "https://www.geoguessr.com/api/v4"
        # only get competitive duels tokens
        game_tokens = []
        pagination_token = None

        def get_token_from_payload(payload):
            try:
                if payload['gameMode'] == 'Duels' and 'competitiveGameMode' in payload:
                    return True
                return False
            except Exception as e:
                return False

        while True:
            response = session.get(
                f"{BASE_URL_V4}/feed/private", params={'paginationToken': pagination_token})
            pagination_token = response.json()['paginationToken']
            entries = response.json()['entries']
            for entry in entries:
                game_date = entry['time']
                game_date = datetime.datetime.fromisoformat(game_date).date()
                start_date = datetime.datetime.strptime(
                    "2024-07-01", "%Y-%m-%d").date()
                if (game_date < start_date):
                    return game_tokens

                payload_json = json.loads(entry['payload'])
                # cleaner way would be to check if payload_json is a dict, if yes
                # then do payload_json=[payload_json]
                # But it's working fine now, after many changes
                # I don't want to change anything lol
                if type(payload_json) is dict:
                    if get_token_from_payload(payload_json):
                        game_tokens.append(payload_json['gameId'])
                else:
                    for payload in payload_json:
                        if (get_token_from_payload(payload['payload'])):
                            game_tokens.append(payload['payload']['gameId'])

            if not pagination_token:
                break
        return game_tokens

    @staticmethod
    def get_player_data(session):
        BASE_URL_V4 = "https://www.geoguessr.com/api/v4"
        try:
            player_data = session.get(
                f"{BASE_URL_V4}/feed/private").json()['entries'][0]['user']
        except:
            return {}
        return {'id': player_data['id'],
                'nick': player_data['nick']}

    @staticmethod
    def get_duels(session, duel_tokens, my_player_Id, loading_bar):
        # add everything to dictionarym then make a dataframe
        data_dict = dict({'Date': [],
                         'Game Id': [],
                          'Round Number': [],
                          'Country': [],
                          'Latitude': [],
                          'Longitude': [],
                          'Damage Multiplier': [],
                          'Opponent Id': [],
                          'Opponent Country': [],
                          'Your Latitude': [],
                          'Your Longitude': [],
                          'Opponent Latitude': [],
                          'Opponent Longitude': [],
                          'Your Distance': [],
                          'Opponent Distance': [],
                          'Your Score': [],
                          'Opponent Score': [],
                          'Map Name': [],
                          'Game Mode': [],
                          'Moving': [],
                          'Zooming': [],
                          'Rotating': [],
                          'Your Rating': [],
                          'Opponent Rating': [],
                          'Score Difference': [],
                          'Win Percentage': []
                          })

        BASE_URL_V3 = "https://game-server.geoguessr.com/api/duels"
        count_ = 0
        for token in duel_tokens:
            count_ += 1
            loading_bar.progress(count_/len(duel_tokens))
            response = session.get(f"{BASE_URL_V3}/{token}")
            if response.status_code == 200:
                game = response.json()
                st.write(game)

st.title('Welcome to Duels Analyzer')
st.text('I created this tool to analyse my rated duel games on Geoguessr. I hope you find it helpful.')
st.text('It needs your _ncfa token to get your games history and data. Your token is not sent anywhere neither it is saved anywhere. You can check the source code, it is open source.')
with st.expander("For any questions/suggestions, message me here"):
    st.page_link("http://a-azeem.bsky.social", label='Bluesky')
    st.page_link('http://reddit.com/u/brartheonnerd', label='Reddit')
    st.page_link("http://twitter.com/azeemstweet", label="Twitter")
with st.form('input_token'):
    _ncfa = st.text_input("Enter _ncfa token:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button('How to get your _ncfa token',
                       "https://github.com/SafwanSipai/geo-insight?tab=readme-ov-file#getting-your-_ncfa-cookie")
    with col3:
        submitted_token = st.form_submit_button("Enter")

if 'submitted_token' not in st.session_state:
    st.session_state['submitted_token'] = False

if (submitted_token or st.session_state['submitted_token']) and _ncfa:
    st.session_state['submitted_token'] = True
    geoguessr_session = helpers.get_session(_ncfa)
    player_data = helpers.get_player_data(geoguessr_session)
    if player_data != {}:
        my_player_Id = player_data['id']
        st.write(
            f"Hello {player_data['nick']} (id {player_data['id']}), extracting your game tokens...")
        print(helpers.time_in_utc_530(),
              player_data['nick'], player_data['id'])
    if 'duel_tokens' not in st.session_state:
        st.session_state['duel_tokens'] = []
        with st.spinner("", show_time=True):
            duel_tokens = helpers.get_duel_tokens(geoguessr_session)
        st.session_state['duel_tokens'] = duel_tokens
    else:
        duel_tokens = st.session_state['duel_tokens']
    st.write(f"Found {len(duel_tokens)} rated duels.")

    st.write(
        f"To retrive all {len(duel_tokens)} games, it will take around {60*len(duel_tokens)/500} seconds.")
    st.markdown('I recommend you choose **All**, it will take some time but after that, you can analyse your games withouth any loading.')
    retrieval_option = st.radio(
        "Retrieval Option:",
        # ("Retrieve All", "Retrieve Recent", "Retrieve by Date"),
        ("Retrieve All", "Retrieve Recent"),
        horizontal=False,
        label_visibility="collapsed",
    )
    with st.form("retrieval_form", border=False):
        if retrieval_option == "Retrieve Recent":
            recent_count = st.slider("Recent Games:", 1, len(
                duel_tokens), round(len(duel_tokens)/2))
        # elif retrieval_option == "Retrieve by Date":
        #     today = datetime.date.today()
        #     start_date = today - datetime.timedelta(days=7)
        #     date_range = st.date_input("Select a date range", (start_date, today),format="DD/MM/YYYY")
        else:
            recent_count = None
            date_range = None
        submitted_1 = st.form_submit_button("Retrieve")
    if 'submitted_1' not in st.session_state:
        st.session_state['submitted_1'] = False
    if st.session_state['submitted_1'] or submitted_1:
        st.session_state['submitted_1'] = True
        if retrieval_option == "Retrieve All":
            st.write("Retrieving all games' data...")
        elif retrieval_option == "Retrieve Recent":
            st.write(f"Retrieving {recent_count} recent games...")
            duel_tokens = duel_tokens[:recent_count]
        # else:
            # st.write(f"Retrieving games between {date_range[0]} and {date_range[1]}...")
            # to do the whole retrival  by date thing
        data_dict = {}
        geoguessr_session_2 = Session()
        geoguessr_session_2.cookies.set(
            "_ncfa", _ncfa, domain=".geoguessr.com")
        if len(duel_tokens) > 0:
            if 'data_dict' not in st.session_state:
                st.session_state['data_dict'] = {}
                loading_bar = st.progress(0)
                data_dict = helpers.get_duels(
                    geoguessr_session_2, duel_tokens, my_player_Id, loading_bar)
                st.success('Done')
                st.session_state['data_dict'] = data_dict
            else:
                data_dict = st.session_state['data_dict']
                st.success('Done')
        df = pd.DataFrame()
        df = pd.DataFrame(data_dict)
        if not df.empty:
            df = helpers.datetime_processing(df)
        # st.write(df)
        submitted = False