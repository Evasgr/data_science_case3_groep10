import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import requests
import folium
from streamlit_folium import st_folium
#import geopandas as gpd

######################################################################################################################################################

#Titel van het dashboard
st.title("Laadpalen en elektrische auto's")

#sidebar met tabs
st.sidebar.title("Inhoud")
selected_tab = st.sidebar.radio("Kies een onderwerp", ["Laadpalen in Washington D.C.", "Verloop aantal auto's per brandstofsoort", 
                                                       "Laadpalen en elektrische auto's", "Auto's aan laadpaal"])

######################################################################################################################################################
# Inhoud tab 1
@st.cache_data  # Dit zal de data cachen
def load_and_prepare_data_tab_1():
    # API-aanroep om de data te laden
    response = requests.get("https://api.openchargemap.io/v3/poi/?output=json&countrycode=US&maxresults=9999999&compact=false&verbose=false&key=93b912b5-9d70-4b1f-960b-fb80a4c9c017")
    responsejson  = response.json()
    df = pd.DataFrame(responsejson)
    df2 = pd.json_normalize(df.AddressInfo)
    df = pd.merge(df, df2).drop(columns=['AddressInfo']) # Hier worden waardes verwijderd
    
    df['DateCreated'] = pd.to_datetime(df['DateCreated'])
    df['DateCreated_date'] = df['DateCreated'].dt.date
    df['DateCreated_year'] = df['DateCreated'].dt.year
    df['DateCreated_year_color'] = df['DateCreated_year'].copy()
    
    df = df.replace({'DateCreated_year_color':{
        2010: '#FF0000',  # Red
        2011: '#0000FF',  # Blue
        2012: '#FFFF00',  # Yellow
        2013: '#00FF00',  # Green
        2014: '#FF00FF',  # Magenta
        2015: '#00FFFF',  # Cyan
        2016: '#800000',  # Maroon
        2017: '#FFA500',  # Orange
        2018: '#800080',  # Purple
        2019: '#008080',  # Teal
        2020: '#808000',  # Olive
        2021: '#A52A2A',  # Brown
        2022: '#000000',  # Black
        2023: '#808080',  # Gray
        2024: '#FF6347'   # Tomato
    }})
    return df
# Laad de data
df = load_and_prepare_data_tab_1()

# Titel en tekst
if selected_tab == "Laadpalen in Washington D.C.":
    st.header("Locaties laadpalen en jaar van plaatsen in Washington D.C.")
    st.markdown("___")

# Map maken en plotten 
# Functie voor het maken van een aangepaste legenda met cirkelvormige markers
# Map maken en plotten 
    # Create the map
    stad = 'Washington'
    df3 = df[df['Town'] == stad]
    m = folium.Map(location=(38.889805, -77.009056), zoom_start=14)
    
    for i in df3.index:
        marker = folium.RegularPolygonMarker(location=[df3['Latitude'][i], df3['Longitude'][i]],
                                            radius=5,
                                            color=df['DateCreated_year_color'][i],
                                            fill=True,
                                            fill_color=df['DateCreated_year_color'][i],
                                            number_of_sides=5)
        marker.add_to(m)
    
    folium.TileLayer('Cartodb Positron').add_to(m)
    
    # Display the map using folium_static in Streamlit
    st_folium(m)
    
    # Create a custom legend using Streamlit's markdown functionality
    years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    colors = [
        '#FF0000',  # Red
        '#0000FF',  # Blue
        '#FFFF00',  # Yellow
        '#00FF00',  # Green
        '#FF00FF',  # Magenta
        '#00FFFF',  # Cyan
        '#800000',  # Maroon
        '#FFA500',  # Orange
        '#800080',  # Purple
        '#008080',  # Teal
        '#808000',  # Olive
        '#A52A2A',  # Brown
        '#000000',  # Black
        '#808080',  # Gray
        '#FF6347'   # Tomato
    ]
    
    # Create HTML for the legend with CSS to float it to the right and make it smaller
    legend_html = """
    <div style='position: fixed; top: 10%; right: 18%; width: 120px; padding: 10px; background-color: #fff; border: 2px solid #bbb; border-radius: 5px; font-size: 12px; z-index: 9999;'>
    <h4 style='font-size: 14px; margin-bottom: 10px;'>Charging Points</h4>
    <ul style='list-style: none; padding-left: 0;'>
    """
    
    for year, color in zip(years, colors):
        legend_html += f"<li style='margin-bottom: 5px;'><span style='background:{color};width:12px;height:12px;display:inline-block;margin-right:10px;'></span>{year}</li>"
    
    legend_html += "</ul></div>"
    
    # Display the legend on the right using st.markdown
    st.markdown(legend_html, unsafe_allow_html=True)


######################################################################################################################################################
# Inhoud tab 2
# Inladen/prepareren data en opslaan in geheugen
@st.cache_data
def load_and_prepare_data_tab_2():
    # Laad de datasets
    df_auto_br = pd.read_csv('Open_Data_RDW__Gekentekende_voertuigen_brandstof_20241009.csv')
    df_auto_da = pd.read_csv('Open_Data_RDW__Gekentekende_voertuigen_20241010.csv')

    # Controleer of de datumkolom correct is
    df_auto_da['Datum tenaamstelling DT'] = pd.to_datetime(df_auto_da['Datum tenaamstelling DT'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')

    # Merge de datasets op basis van de 'Kenteken'-kolom
    combined_df = pd.merge(df_auto_br, df_auto_da, on='Kenteken', how='left')

    # Maak een extra kolom voor de jaar-maand weergave van de tenaamstellingsdatum
    combined_df['Tenaamstelling maand'] = combined_df['Datum tenaamstelling DT'].dt.to_period('M')

    # Groepeer de data op 'Tenaamstelling maand' en 'Brandstof omschrijving', en tel het aantal voertuigen per maand
    result = combined_df.groupby(['Tenaamstelling maand', 'Brandstof omschrijving']).size().reset_index(name='Aantal voertuigen')

    # Zet de 'Tenaamstelling maand' om naar een timestamp
    result['Tenaamstelling maand'] = result['Tenaamstelling maand'].dt.to_timestamp()

    return result
# Laad en bereid de data voor met caching
result_filtered = load_and_prepare_data_tab_2()


# Titel en tekst
if selected_tab == "Verloop aantal auto's per brandstofsoort":
    st.header("Het verloop van het aantal auto's per brandstofsoort")
    st.markdown("""Deze grafiek laat het aantal geregistreerde auto's per brandstofcategorie zien, gemeten vanaf januari 2015.
                Er is een duidelijke groei te zien in de elektrische auto's en auto's op benzine, terwijl auto's op diesel een 
                dalende trend laten zien. De auto's op andere brandstoffen lijken stabiel te blijven met relatief kleine aantallen.""")
    st.markdown("""
    **Opmerking:** Let op de scherpe daling in januari 2024. Dit komt waarschijnlijk doordat de data voor deze maand nog niet volledig is verwerkt. 
    De gegevens voor januari 2024 zullen naar verwachting worden bijgewerkt, aan het eind van de maaand, zodra meer registraties beschikbaar zijn.
    """)
    st.markdown("""
    #### Betekenissen van brandstofcategorieën:
    - **Alcohol**: Voertuigen die gebruikmaken van alcohol (zoals bio-ethanol) als brandstof.
    - **Benzine**: Voertuigen die rijden op benzine, de meest gangbare brandstof voor personenauto's.
    - **CNG**: Compressed Natural Gas, een schoner alternatief voor benzine of diesel.
    - **Diesel**: Voertuigen die rijden op dieselbrandstof, vaak gekozen voor zwaardere voertuigen.
    - **Elektriciteit**: Elektrische voertuigen aangedreven door een batterij en elektromotor.
    - **LPG**: Liquefied Petroleum Gas, een alternatieve brandstof, vaak goedkoper en milieuvriendelijker dan benzine.
    - **Waterstof**: Voertuigen die rijden op waterstofbrandstofcellen, met alleen waterdamp als uitstoot.
    - **LNG**: Liquefied Natural Gas, een vorm van aardgas in vloeibare vorm, gebruikt voor vrachtwagens en bussen.
    """)
    st.markdown("""Met de slider hieronder kunt u een begin- en einddatum selecteren die worden gebruikt om het aantal 
                geregistreerde voertuigen per brandstofcategorie binnen de gekozen periode te bekijken.""" )


# Grafiek maken en plotten
    # Bepaal de minimum en maximum datums voor de slider
    min_date = result_filtered['Tenaamstelling maand'].min()
    max_date = result_filtered['Tenaamstelling maand'].max()

    # Maak de slider voor het datumbereik
    date_range = st.slider(
        'Selecteer een datumbereik',
        min_value=min_date.to_pydatetime(),  # Zorg voor datetime-indeling
        max_value=max_date.to_pydatetime(),  # Zorg voor datetime-indeling
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),  # Standaardwaarde
        format='MMM YYYY')

    # Filter de data op basis van de geselecteerde datums
    filtered_data = result_filtered[
        (result_filtered['Tenaamstelling maand'] >= pd.to_datetime(date_range[0])) &
        (result_filtered['Tenaamstelling maand'] <= pd.to_datetime(date_range[1]))]

    # Maak het lijndiagram opnieuw met de gefilterde data
    fig = px.line(filtered_data, 
                  x='Tenaamstelling maand', 
                  y='Aantal voertuigen', 
                  color='Brandstof omschrijving', 
                  title='Aantal voertuigen per maand per brandstofcategorie (van januari 2015 tot januari 2024)')

    # Pas de layout van de grafiek aan
    fig.update_layout(
        xaxis_title="Maand",
        yaxis_title="Aantal voertuigen",
        xaxis_tickformat='%Y-%m',  # Formatteer als jaar-maand
        xaxis_tickangle=-45)

    # Laat de grafiek zien in het Streamlit dashboard
    st.plotly_chart(fig)


######################################################################################################################################################
# Inhoud tab 3
if selected_tab == "Laadpalen en elektrische auto's":
# Titel en tekst
    st.header("Verband en groei aantal elektrische laadpalen en volledige elektrische auto's per provincie")
    st.markdown("""
    Hieronder is een interactieve lijngrafiek te zien van het aantal elektrische laadpalen en volledig elektrische auto's per provincie.
    Over de jaren heen is het aantal elektrische laadpalen alleen maar toegenomen, wat ook duidelijk te zien is in de grafiek hieronder.
    Het aantal volledig elektrische auto's is over de jaren heen ook alleen maar toegenomen.
    """)
    st.markdown("""
    Links is een checkbox te zien waarin u verschillende provincies kan selecteren die in de grafiek getoond worden. 
    De gestippelde lijnen zijn voor het aantal volledig elektrische auto's en de doorgetrokken lijnen zijn voor het aantal laadpalen. 
    Met de dropbox hieronder kunt u selecteren welke data er in de grafiek wordt weergegeven.
    """)

# Datasets inladen en preparen 
    #Dataset aantal laadpalen Nederland
    maanden = {
        'Januari': '1/',
        'Februari': '2/',
        'Maart': '3/',
        'April': '4/',
        'Mei': '5/',
        'Juni': '6/',
        'Juli': '7/',
        'Augustus': '8/',
        'September': '9/',
        'Oktober': '10/',
        'November': '11/',
        'December': '12/'}

    df = pd.read_csv('aantal laadpunten nederland provincies.csv', sep=';')
    #df.isna().sum()
    df.columns = df.columns.str.split('|').str[-1].str.strip()
    value_vars = df.columns[1::2]
    df_long = pd.melt(df, id_vars='Provincies', value_vars=value_vars,
                    var_name='Datum', value_name='Aantal')
    df_long = df_long.drop(df_long[df_long['Provincies'] == 'Provincie onbekend'].index)
    df_long['Provincies'] = np.where(df_long['Provincies'] == 'Fryslân', 'Friesland', df_long['Provincies'])
    df_long['Datum'] = df_long['Datum'].replace(maanden, regex=True)
    df_long['Datum'] = df_long['Datum'].apply(lambda x: x.replace(' ', ''))
    df_long['Datum'] = pd.to_datetime(df_long['Datum'], format='%m/%Y')
    df_long = df_long.dropna(subset=['Aantal'])

    #Datasets voor aantal volledige elektrische autos
    df_2023 = pd.read_excel("provincie_verdeling_elektrische_auto_1-1-2023.xlsx", sheet_name='Tabel 1', skiprows=9)
    df_2023 = df_2023[['Unnamed: 0', 'Unnamed: 2']].rename(columns={'Unnamed: 0': 'Provincies', 'Unnamed: 2': 'Aantal'})

    df_2020 = pd.read_excel("provincie-verdeling-auto-1-1-2020.xlsx", sheet_name='Tabel 2', skiprows=9)
    df_2020 = df_2020[['Unnamed: 0', 'Unnamed: 2']].rename(columns={'Unnamed: 0': 'Provincies', 'Unnamed: 2': 'Aantal'})

    df_2021 = pd.read_excel("provincie-verdeling-elektrische-auto-2022-2021.xlsx", sheet_name='Tabel 3', skiprows=9)
    df_2021 = df_2021[['Unnamed: 0', 'Unnamed: 2']].rename(columns={'Unnamed: 0': 'Provincies', 'Unnamed: 2': 'Aantal'})

    df_2022 = pd.read_excel("provincie-verdeling-elektrische-auto-2022-2021.xlsx", sheet_name='Tabel 1', skiprows=9)
    df_2022 = df_2022[['Unnamed: 0', 'Unnamed: 2']].rename(columns={'Unnamed: 0': 'Provincies', 'Unnamed: 2': 'Aantal'})

    #Datasets voor anatal volledige elektrische autos combineren
    merged_df = df_2020.merge(df_2021, on='Provincies', suffixes=('_2020', '_2021')) \
                        .merge(df_2022, on='Provincies', suffixes=('', '_2022')) \
                        .merge(df_2023, on='Provincies', suffixes=('', '_2023'))
    merged_df.rename(columns={'Aantal': 'Aantal_2022'}, inplace=True)
    merged_df.rename(columns={'Aantal_2020': '2020-01-01', 'Aantal_2021': '2021-01-01', 'Aantal_2022': '2022-01-01', 'Aantal_2023': '2023-01-01'}, inplace=True)
    merged_df = merged_df[~merged_df['Provincies'].isin([None, 'Bron: CBS.'])]
    merged_df = merged_df.reset_index(drop=True).dropna()

    df_long_twee = pd.melt(merged_df, id_vars=['Provincies'], var_name='Datum', value_name='Aantal_twee')
    df_long_twee['Datum'] = pd.to_datetime(df_long_twee['Datum'], errors='coerce')

    #Aantal laadpalen dataset combineren met aantal volledige elektrische autos
    df_merged = pd.merge(df_long, df_long_twee, on=['Provincies', 'Datum'], how='left')  

#Grafiek maken en plotten
    #Checkbox voor provincies
    provincies = df_merged['Provincies'].unique()
    
    gekozen_provincies = []
    st.sidebar.header("Selecteer hier de provinvies:")
    for provincie in provincies:
        if st.sidebar.checkbox(provincie, value=True):
            gekozen_provincies.append(provincie)
    
    # Filtert data op gekozen provincies
    df_filtered = df_merged[df_merged['Provincies'].isin(gekozen_provincies)]
    
    # Dropdown box
    data_keuze = st.selectbox("Selecteer hieronder welke data u wilt zien:", options=["Elektrische Laadpalen", "Volledige elektrische autos", "Beide"])
    
    #Lijn plot
    color_map = {
        'Groningen': 'blue',
        'Friesland': 'green',
        'Drenthe': 'orange',
        'Overijssel': 'red',
        'Flevoland': 'purple',
        'Gelderland': 'teal',
        'Utrecht': 'darkblue',
        'Noord-Holland': 'brown',
        'Zuid-Holland': 'pink',
        'Zeeland': 'lightblue',
        'Noord-Brabant': 'darkgreen',
        'Limburg': 'yellow'
    }
    
    fig = go.Figure(layout=dict(height=600, width=1000))
    
    
    if data_keuze == "Elektrische Laadpalen" or data_keuze == "Beide":
        for provincie in gekozen_provincies:
            provincie_data = df_filtered[df_filtered['Provincies'] == provincie]
            fig.add_trace(
                go.Scatter(
                    x=provincie_data['Datum'],
                    y=provincie_data['Aantal'],
                    mode='lines+markers',
                    name=f'{provincie} (Laadpalen)',
                    line=dict(color=color_map[provincie], width = 1),
                    marker=dict(size=4),
                    connectgaps=True))
    
    if data_keuze == "Volledige elektrische autos" or data_keuze == "Beide":
        for provincie in gekozen_provincies:
            provincie_data = df_filtered[df_filtered['Provincies'] == provincie]
            fig.add_trace(
                go.Scatter(
                    x=provincie_data['Datum'],
                    y=provincie_data['Aantal_twee'],
                    mode='lines+markers',
                    name=f'{provincie} (Autos)',
                    line=dict(dash='dash', color=color_map[provincie], width = 1),
                    marker=dict(size=4),
                    connectgaps=True))
    
    #past titel aan, aan de hand van data keuze
    if data_keuze == "Elektrische Laadpalen":
        plot_title = 'Aantal Elektrische Laadpalen per Provincie'
    elif data_keuze == "Volledige elektrische autos":
        plot_title = 'Aantal Volledige Elektrische Autos per Provincie'
    else:
        plot_title = 'Aantal Laadpalen en Volledige Elektrische Autos per Provincie'
    
    min_datum = pd.Timestamp('2019-07-01')
    max_datum = pd.Timestamp('2024-12-30')
    
    fig.update_layout(
        title=plot_title,
        xaxis_title='Datum',
        yaxis_title='Aantal',
        hovermode='x unified',
        showlegend= False,
        xaxis=dict(
            range=[min_datum, max_datum]  # Set the range for the x-axis
        ))
    
    #legenda aan de hand van annotations
    annotations = []
    for i, provincie in enumerate(gekozen_provincies):
        annotations.append(
            dict(
                xref="paper", yref="paper",
                x=1.00, y=1 - (i * 0.04),  
                text=f"<span style='color:{color_map[provincie]}'>{provincie}</span>",
                showarrow=False,
                font=dict(size=12),
                align="left"))
    
    fig.update_layout(
        annotations=annotations)
    
    st.plotly_chart(fig)
    
######################################################################################################################################################
# Inhoud tab 4
if selected_tab == "Auto's aan laadpaal":
# Titel en tekst 
    st.header("Relatie Begintijd laadsessie, Oplaadtijd en Aangesloten tijd")
    
    st.markdown("""De tijd van de dag waarop een laadsessie wordt gestart heeft een sterke invloed op de gemiddelde duur
            en de gemiddelde aangesloten tijd van de sessie. In de onderstaande visualistie, gebaseerd op data
            van ruim 10.000 laadsessies, zijn de uren van de dag (starttijd van de sessie) weergegeven
            gerelateerd aan hun gemiddelde oplaadtijd en verbonden tijd aan de laadpaal.""")
    
    st.markdown("""De laadsessies die diep in de nacht worden gestart duren relatief kort, maar hebben vaak een lange aangesloten tijd.
            Deze trent houdt aan tot in de ochtend, tot de uren dat de werkdagen beginnen. Werknemers die tijdens het werk de auto aan de lader leggen
            zorgen voor zowel een langere laadtijd als aangesloten tijd. Overdag is een standaard trent te zien, hoewel de aangesloten tijd blijft stijgen
            naarmate het later wordt. Vanaf 17.00/18.00, wanneer de werkdag is afgelopen, worden veel auto's langer aan de lader gelegd en is er een
            stijgende trent te zien in oplaadtijd. De aangesloten tijd van meer dan 10 uur in de avonduren is natuurlijk te verklaren door de vele auto's
            die de gehele nacht aan de laadpaal blijven staan.""")

# Data inladen en prepareren
    df = pd.read_csv('laadpaaldata.csv')
    #df.isna().sum()
    df['Started'] = pd.to_datetime(df['Started'],format="%Y-%m-%d %H:%M:%S", errors='coerce')
    df['Startuur'] = df['Started'].dt.hour #Nieuwe kolom met startuur
    
    df = df[(df['ChargeTime'] >= 0.1) & (df['ConnectedTime'] >= 0.1)]
    Gemiddelden = df.groupby('Startuur')[['ChargeTime','ConnectedTime']].mean()
    df_new = pd.DataFrame(Gemiddelden)
    df_new.loc[df_new['ConnectedTime'] >= 10, 'ConnectedTime'] = 10

# Grafiek maken en plotten 
    dropdown = st.selectbox('Kies een variabele:', ['Oplaadtijd', 'Aangesloten Tijd','Gecombineerd'])
    
    fig = go.Figure()
    
    if dropdown == 'Oplaadtijd':
        fig.add_trace(go.Bar(x=df_new.index, y=df_new['ChargeTime'], name='Oplaadtijd', opacity=1))
    elif dropdown == 'Aangesloten Tijd':
        fig.add_trace(go.Scatter(x=df_new.index, y=df_new['ConnectedTime'], name='Aangesloten Tijd', mode='lines+markers'))
    elif dropdown == 'Gecombineerd':
        fig.add_trace(go.Bar(x=df_new.index, y=df_new['ChargeTime'], name='Oplaadtijd', opacity=1))
        fig.add_trace(go.Scatter(x=df_new.index, y=df_new['ConnectedTime'], name='Aangesloten Tijd', mode='lines+markers'))
    
    fig.update_xaxes(tickmode = 'linear', range = [-0.5, 23.5])
    fig.update_yaxes(tickvals=[0, 2, 4, 6, 8, 10], ticktext=['0', '2', '4', '6', '8', '10+'])
    fig.update_layout(title = 'Verband tussen beginuur laadsessie en variabelen', xaxis_title = 'Beginuur laadsessie',
                    yaxis_title = 'Gemiddelde tijd (uren)')
    st.plotly_chart(fig)
