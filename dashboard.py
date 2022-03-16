import geopandas
import streamlit as st
import pandas    as pd
import numpy     as np
import folium
import plotly.express as px
from datetime import datetime
from streamlit_folium import folium_static
from folium.plugins   import MarkerCluster


pd.set_option('display.float_format', lambda x: '%.f' % x)

st.set_page_config( layout='wide' )

c1, c2 = st.beta_columns((2,1))
# image
# with c1:
    # photo = Image.open('house.png')
    # st.image(photo,width=300)

#headers
with c1:

    st.write('')
    HR_format = '<p style="font-family:sans-serif;' \
                   'font-size: 48px;' \
                   'font-weight: bold;' \
                   'text-align: center;' \
                   '">House Rocket Company Analysis </p>'

    st.markdown(HR_format, unsafe_allow_html=True)


st.write('## Welcome to House Rocket Streamlit App!')

st.write('')
st.write("Here you can find some interactive information about House Rocket's business project. Feel free to change the filters and check out the variety of houses and its business opportunities.")

st.write("For further information, check out the project in "
                         "[GitHub](https://github.com/leassis91/Portfolio-Projects/tree/master/HouseRocketEDA)")
# st.write("Made by **Leandro Destefani**"
#                  " \n\n"
#                  "Social media: [LinkedIn](https://www.linkedin.com/in/leandrodestefani) "
#                  "  [Mail](leassis.destefani@gmail.com)")                         






@st.cache( allow_output_mutation=True )
def get_data(path):
    data = pd.read_csv(path)
    return data


@st.cache( allow_output_mutation=True )
def get_geofile( url ):
    geofile = geopandas.read_file( url )

    return geofile

def transform_data(data):

    # Transformando em formato de data
    data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')  

    # Removendo os ID que estão duplicados
    data = data.drop_duplicates(subset='id', keep='last')

    # removendo o imóveis que possui 33 quartos por ser um outlier
    data.drop(data.loc[data['bedrooms'] == 33].index, inplace=True)
    return data



def set_feature(data):
    # add new features

    # column for H2. 
    data['yr_old'] = data['yr_built'].apply(lambda x: '> 1955' if x > 1955 else '< 1955')

    # column for h3        
    data['basement'] = data['sqft_basement'].apply(lambda x: 'no' if x == 0 else 'yes')      

    # coluna for h4
    data['year'] = pd.to_datetime(data['date']).dt.year

    # coluna for h5
    data['describe_bathrooms'] = data['bathrooms'].apply(lambda x: '> 3' if x >= 3.0
                                                                    else '< 3')


     # Waterfront
    data['waterfront_'] = data['waterfront'].apply(lambda x: 'yes' if x == '1'
    else 'no')
    
    # creating seasons
    data['month'] = pd.to_datetime(data['date']).dt.month
    data['season'] = data['month'].apply(lambda x: 'summer' if (x > 5) & (x < 8) else
                                            'spring' if (x > 2) & (x < 5) else
                                            'fall' if (x > 8) & (x < 12) else
                                            'winter')

    data['condition_name'] = data['condition'].apply(lambda x:   'worn-out' if x == 1 else
                                                            'fair' if x == 2 else
                                                            'average'if x == 3 else
                                                            'good' if x == 4 else
                                                            'excellent')

    data['grade_name'] = data['grade'].apply(lambda x: 'low-quality' if (x <= 3) else
                                            'simple' if (x > 3) & (x <= 6) else
                                            'fair' if (x > 6) & (x < 10) else
                                            'high-quality')

    return data



def over_data(data):
    st.title("Data Overview")

    if st.checkbox('Show dataset'):
        st.write(data.head(10))

    return None



def portfolio_density(data, geofile):
    # =======================
    # Densidade de Portfolio
    # =======================
    st.title( 'Region Overview' )

    if st.checkbox('Show Density Maps'):

        # portfolio_density = st.beta_expander("Expand to check Portfolio Density", expanded = False)
        # with portfolio_density:
            # st.subheader("Portfolio Density")
        c1, c2 = st.beta_columns((2, 2))
        # c1.header('Portfolio Density')


        df = data


        # Base Map - Folium 
        density_map = folium.Map(location=[data['lat'].mean(), 
                                data['long'].mean() ],
                                default_zoom_start=15 ) 

        marker_cluster = MarkerCluster().add_to(density_map)
        for name, row in df.iterrows():
            folium.Marker( [row['lat'], row['long'] ], 
                popup='Sold R${0} on: {1}. Features: {2} sqft, {3} bedrooms, {4} bathrooms, year built: {5}'.format(row['price'],
                                            row['date'],
                                            row['sqft_living'],
                                            row['bedrooms'],
                                            row['bathrooms'],
                                            row['yr_built'] ) ).add_to( marker_cluster )


        with c1:
            st.header('Portfolio Density')
            folium_static(density_map, width=600)


        # Region Price Map
        # c2.header( 'Price Density' )

        df = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()
        df.columns = ['ZIP', 'PRICE']


        geofile = geofile[geofile['ZIP'].isin( df['ZIP'].tolist())]

        region_price_map = folium.Map( location=[data['lat'].mean(), 
                                    data['long'].mean() ],
                                    default_zoom_start=15 ) 


        region_price_map.choropleth( data = df,
                                    geo_data = geofile,
                                    columns=['ZIP', 'PRICE'],
                                    key_on='feature.properties.ZIP',
                                    fill_color='YlOrRd',
                                    fill_opacity = 0.7,
                                    line_opacity = 0.2,
                                    legend_name='AVG PRICE' )

        with c2:
            st.header('Price Density')
            folium_static(region_price_map, width=600)

    return None


def buy_houses(data,geofile):

    st.sidebar.title('House Hocket Interactive App')
    st.sidebar.subheader('Project made by [Leandro Destefani](https://github.com/leassis91)')
    st.sidebar.write('     ')
    # st.sidebar.write('Filtros para seleção dos imóveis sugeridos para compra e seus respectivos cenários de venda pós-compra')
    st.title('Properties worth buying')
    st.write('Properties below region`s median price')

    # Agrupar os imóveis por região ( zipcode ).Encontrar a mediana do preço do imóvel.
    df1 = data[['zipcode', 'price']].groupby('zipcode').median().reset_index()
    df1 = df1.rename(columns={'price': 'price_median'})

    # Merge
    data = pd.merge(df1, data, on='zipcode', how='inner')

    # status
    for i in range(len(data)):
        if (data.loc[i, 'price'] < data.loc[i, 'price_median']) & (data.loc[i, 'condition'] >= 3):
            data.loc[i, 'status'] = 'worth'
        else:
            data.loc[i, 'status'] = 'not worth'

    # Seleção dos imóveis
    buy_houses = data[data['status'] == 'worth'].sort_values(by=['condition_name', 'price'])

    f_condition = st.sidebar.multiselect('Enter Condition', buy_houses['condition_name'].unique()) # filtro condition
    f_zipcode = st.sidebar.multiselect('Enter Zipcode', buy_houses['zipcode'].unique()) # filtro zipcode

    if (f_zipcode != []) & (f_condition != []):
        buy_houses = buy_houses.loc[(buy_houses['zipcode'].isin(f_zipcode)) & (buy_houses['condition_name'].isin(f_condition)), :]
    elif (f_zipcode != []) & (f_condition == []):
        buy_houses = buy_houses.loc[data['zipcode'].isin(f_zipcode), :]
    elif (f_zipcode == []) & (f_condition != []):
        buy_houses = buy_houses.loc[buy_houses['condition_name'].isin(f_condition), :]
    else:
        buy_houses = buy_houses.copy()

    st.dataframe(buy_houses[['id','zipcode', 'price', 'price_median', 'condition_name']])
    st.sidebar.write('We found that {} properties are worth purchasing'.format(len(buy_houses)))

    st.title('Properties Evaluation')
    # st.write('Condição: a) Se o preço da compra for maior que a mediana da região + sazonalidade. O preço da venda será igual ao preço da compra + 10% ')
    # st.write('Condição: b) Se o preço da compra for menor que a mediana da região + sazonalidade. O preço da venda será igual ao preço da compra + 30% ')

    # Agrupar os imóveis por região ( coluna zipcode ) e por sazonalidade(season)
    # Dentro de cada região/season encontrar a mediana do preço do imóvel.

    df2 = data[['zipcode', 'season', 'price']].groupby(['zipcode', 'season']).median().reset_index()
    df2 = df2.rename(columns={'price': 'price_median_season'})

    # unir df2 com df
    buy_houses = pd.merge(buy_houses, df2, how='inner', on=['zipcode', 'season'])

    for i in range(len(buy_houses)):
        if buy_houses.loc[i, 'price'] <= buy_houses.loc[i, 'price_median_season']:
            buy_houses.loc[i, 'sale_price'] = buy_houses.loc[i, 'price'] * 1.30
        elif buy_houses.loc[i, 'price'] > buy_houses.loc[i, 'price_median_season']:
            buy_houses.loc[i, 'sale_price'] = buy_houses.loc[i, 'price'] * 1.10
        else:
            pass

    buy_houses['profit'] = buy_houses['sale_price'] - buy_houses['price']
    st.dataframe(buy_houses[['id','zipcode', 'price','season', 'price_median_season', 'condition_name', 'sale_price' , 'profit']])
    st.sidebar.write('Total profit of the company will be: S$ {:,.2f} '.format(buy_houses['profit'].sum()))

    # Mapa de localização
    if st.checkbox('\n\nShow Selected Properties'):

        st.title('Properties Overview')

        st.header('Location')

        # Base Map - Folium
        density_map = folium.Map(location=[buy_houses['lat'].mean(), buy_houses['long'].mean()], default_zoom_start=15)
        marker_cluster = MarkerCluster().add_to(density_map)

        for name, row in buy_houses.iterrows():
            folium.Marker([row['lat'], row['long']],
                          popup='Buy price U${0} |Sell Price US$ {1} with profit of US$ {2}. Features: {3} sqft, {4} bedrooms, {5} bathrooms, year built: {6}'.format(
                              row['price'],
                              row['sale_price'],
                              row['profit'],
                              row['sqft_living'],
                              row['bedrooms'],
                              row['bathrooms'],
                              row['yr_built'])).add_to(marker_cluster)

        folium_static(density_map)

        # Mapa de densidade
        st.header('Profit Density')
        df4 = buy_houses[['profit', 'zipcode']].groupby('zipcode').mean().reset_index()
        df4.columns = ['ZIP', 'PROFIT']
        geofile = geofile[geofile['ZIP'].isin(df4['ZIP'].tolist())]
        region_price_map = folium.Map(location=[buy_houses['lat'].mean(), buy_houses['long'].mean()], default_zoom_start=15)
        region_price_map.choropleth(data=df4,
                                    geo_data=geofile,
                                    columns=['ZIP', 'PROFIT'],
                                    key_on='feature.properties.ZIP',
                                    fill_color='YlOrRd',
                                    fill_opacity=0.7,
                                    line_opacity=0.2,
                                    legend_name='AVG PROFIT')

        folium_static(region_price_map)

    # ---- Insights - Imóveis selecionados --------- #

    st.title('Some Panels of the Most Profitable Properties')
    df = buy_houses[['zipcode', 'bedrooms', 'bathrooms', 'season',
                     'condition_name']]

    # st.subheader("Os atributos abaixo fornecem uma lucratividade maior dentre a seleção dos imóveis acima:")

    conditions = []
    for i in df.columns:
        ins = buy_houses[['profit', i]].groupby(i).sum().reset_index()

        plot = px.bar(ins, x=i, y='profit', color=i, labels={i:i,"profit": "Profit"},
                      template='simple_white')
        plot.update_layout(showlegend=False)
        st.plotly_chart(plot, use_container_width=True)
        ins2 = ins[ins['profit'] == ins['profit'].max()]
        conditions.append(ins2.iloc[0, 0])
        st.write('Most Profitable Properties where: {} = {}'.format(i, ins2.iloc[0, 0]))

    # Tabela com resumo
    st.subheader("Best Attributes Distribution")
    dx = pd.DataFrame(columns=['attribute', 'condition', 'properties_total', 'profit'])
    dx['attribute'] = ['zipcode', 'bedrooms', 'bathrooms', 'season',
                      'condition_name']
    dx['condition'] = conditions

    for i in range(len(dx)):
        dx.loc[i, 'properties_total'] = buy_houses['id'][buy_houses[dx.loc[i, 'attribute']] == dx.loc[i, 'condition']].count()
        # dx.loc[i, '%_imoveis'] = float(dx.loc[i, 'total_imoveis'] / buy_houses['id'].count() * 100)
        dx.loc[i, 'profit'] = buy_houses['profit'][buy_houses[dx.loc[i, 'attribute']] == dx.loc[i, 'condition']].sum()
        # dx.loc[i, '%_lucro'] = float(dx.loc[i, 'lucro_total'] / buy_houses['profit'].sum() * 100)

    dx["condition"] = dx["condition"].astype(str)
    st.dataframe(dx)

    return None






# def commercial_distribution(data):
#     # =================================================
#     # Distruibção dos imóveis por categorias comerciais
#     # =================================================
#     st.sidebar.title("Commercial Options")
#     st.title("Commercial Attributes")

#     #  Average Price per Year

#     data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

#     # filters
#     min_year_built = int(data['yr_built'].min())
#     max_year_built = int(data['yr_built'].max())

#     st.sidebar.subheader('Select Max Year Built')
#     f_year_built = st.sidebar.slider('Year Built', min_year_built,
#                                     max_year_built,
#                                     min_year_built)

#     st.header('Average Price per Year built')

#     # data selection
#     df = data.loc[data['yr_built'] < f_year_built]
#     df = df[['yr_built', 'price']].groupby('yr_built').mean().reset_index()

#     # plot
#     fig = px.line (df, x='yr_built', y='price')
#     st.plotly_chart(fig, use_container_width=True)


#     # --------- Average Price per Day

#     st.header('Average Price per Day')
#     st.sidebar.subheader('Select Max Date')

#     # filters
#     min_date = datetime.strptime(data['date'].min(), '%Y-%m-%d')
#     max_date = datetime.strptime(data['date'].max(), '%Y-%m-%d')



#     f_date = st.sidebar.slider('Date', min_date, max_date, min_date)


#     # data filtering 

#     data['date'] = pd.to_datetime(data['date'])
#     df = data.loc[data['date'] < f_date]
#     df = df[['date', 'price']].groupby('date').mean().reset_index()

#     # plot
#     fig = px.line(df, x='date', y='price')
#     st.plotly_chart(fig, use_container_width=True)


#     # Histograma
#     st.header('Price Distribution')
#     st.sidebar.subheader('Select Max Price')

#     # filters
    
#     min_price = int(data['price'].min())
#     max_price = int(data['price'].max())
#     avg_price = int(data['price'].mean())

#     # data filtering
#     f_price = st.sidebar.slider('Price', min_price, max_price, avg_price)
#     df = data.loc[data['price'] < f_price]

#     # data plot
#     fig = px.histogram(df, x='price', nbins=50)
#     st.plotly_chart(fig, use_container_width=True)
 
#     return None


# def attributes_distribution(data):
    
#     # Distribuição dos imoveis por categorias fisicas
#     st.sidebar.title('Attributes Options')
#     st.title('House Attributes')

#     # filters
#     f_bedrooms = st.sidebar.selectbox('Max number of bedrooms', sorted(set(data['bedrooms'].unique())))
#     f_bathrooms = st.sidebar.selectbox('Max number of bathrooms', sorted(set(data['bathrooms'].unique())))

#     c1, c2 = st.beta_columns(2)

#     # House per bedrooms
#     c1.header("Houses per bedrooms")
#     df = data[data['bedrooms'] < f_bedrooms]
#     fig = px.histogram (df, x='bedrooms', nbins=19)
#     c1.plotly_chart(fig, use_container_width=True)

#     # House per bathrooms
#     c2.header('Houses per bathrooms')
#     df = data[data['bathrooms'] < f_bathrooms]
#     fig = px.histogram (data, x='bathrooms', nbins=19)
#     c2.plotly_chart(fig, use_container_width=True)



#     # filters
#     f_floors = st.sidebar.selectbox('Max number of floor', sorted(set(data['floors'].unique())))
#     f_waterview = st.sidebar.checkbox('Only houses with Water View')

#     c1, c2 = st.beta_columns(2)

#     # House per floors
#     c1.header('Houses per floor')
#     df = data[data['floors'] < f_floors]

#     # plot
#     fig = px.histogram (df, x='floors', nbins=19)
#     c1.plotly_chart(fig, use_container_width=True)

#     # House per waterfront
#     if f_waterview:
#         df = data[data['waterfront'] == 1]
#     else:
#         df = data.copy()

#     fig = px.histogram(df, x='waterfront', nbins=10)
#     c2.plotly_chart(fig, use_container_width=True)

#     return None




###################################
######## INÍCIO DO CÓDIGO #########
###################################



if __name__ == '__main__':
    # ETL
    # data extraction
    path = 'kc_house_data.csv'
    data = get_data(path)
    url = 'https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'
    geofile = get_geofile( url )


    # transformation
    data = transform_data(data)
    data = set_feature(data)
    # overview_data(data)
    over_data(data)
    portfolio_density(data, geofile)
    buy_houses(data, geofile)
    # commercial_distribution(data)
    # attributes_distribution(data)

    # loading