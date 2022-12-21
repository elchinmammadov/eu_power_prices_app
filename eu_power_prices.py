# Code to download data from https://ember-climate.org/app/uploads/2022/09/european_wholesale_electricity_price_data_daily-4.csv

import pandas as pd
import plotly_express as px
import streamlit as st

def time_series_data_func(df, country_list): # returns time series DataFrame (for charting) as well as geographical DataFrame and 'df_ISO_codes' DataFrame (for mapping) of daily/monthly/yearly prices either for all countries or for some . 
    # save ISO3 country codes per country in a DataFrame. ISO3 codes will be used later to create geographical map chart
    country_names  = list(df['Country'].unique()) # assign unique country names to country_names list
    country_codes = list(df['ISO3 Code'].unique()) # assign unique ISO3 country codes to country_codes list
    df_ISO_codes = pd.DataFrame({'Country': country_names, 'ISO3 Code': country_codes}) # create 'df_ISO_codes' DataFrame to host country names and their ISO3 codes
    if country_coverage == 2: # filters time series data only for certain countries that were selected in 'country_list' variable
        df = df[df['Country'].isin(country_list)]
    if data_frequency == 1: # returns time series data (for charting) as well as geographical data (for mapping) of all daily prices either for all countries or for some. 
        df_geo = geo_data_func(df, df_ISO_codes) # formats data that will be used later to create geographical map chart
        return df, df_geo, df_ISO_codes
    elif data_frequency == 2 or data_frequency == 3: # returns time series data (for charting) as well as geographical data (for mapping) of average monthly/yearly prices either for all countries or for some. 
        # calculate monthly average prices by country
        df = df.pivot(index='Date', columns='Country', values='Price (EUR/MWhe)') # move country names to columns
        if data_frequency == 2:
            df = df.groupby(pd.PeriodIndex(df.index, freq="M")).mean() # calculate monthly average values per country
        elif data_frequency == 3:
            df = df.groupby(pd.PeriodIndex(df.index, freq="Y")).mean() # calculate monthly average values per country
        df = df.reset_index() # move 'Date' column from being index into a separate column
        df = df.melt(id_vars=['Date'], value_vars=list(df.columns)[1:], var_name='Country', value_name='Price (EUR/MWhe)') # move individual country columns into a single 'Country' column
        df['Date'] = df['Date'].dt.to_timestamp() # convert DataFrame periods (e.g. 2015-01) to datetime/timestamp (e.g. 2015-01-01T00:00:00)
        df['Date'] = pd.to_datetime(df['Date']).dt.date # converts datetime/timestamp format (e.g. 2015-01-01T00:00:00) into date only format (e.g. 2015-01-01) so that it's easier to look at the date values when exported to CSV
        df_geo = geo_data_func(df, df_ISO_codes) # formats data that will be used later to create geographical map chart
        return df, df_geo, df_ISO_codes

def pct_chg_data_func(df, df_ISO_codes): # returns time series data (for charting) as YoY % change figures depending on which frequency (daily/monthly/yearly) has been selected by user previously in 'data_frequency' variable. Also returns df_ISO_codes, which is needed for creating geographic map. As input, this function uses DataFrame from 'time_series_data_func()' function.
    if data_frequency == 1:
        periods = 365
    elif data_frequency == 2:
        periods = 12
    elif data_frequency == 3:
        periods = 1
    df = df.pivot(index='Date', columns='Country', values='Price (EUR/MWhe)') # move country names to columns
    df = df.pct_change(periods)*100 # calculate YoY percentage change
    df = df[periods:].reset_index() # remove first X rows (where x = value in 'periods' variable) with NaN values and move 'Date' variable from being index to an individual 'Date' column
    df = df.melt(id_vars=['Date'], value_vars=list(df.columns)[1:], var_name='Country', value_name='Price (EUR/MWhe)') # move individual country columns into a single 'Country' column
    df_geo = geo_data_func(df, df_ISO_codes)
    if data_frequency == 1:
        df_geo = pd.merge(df_geo, df_ISO_codes, on ='Country', how ='left').dropna() # add 'ISO3 Code' column to 'df_geo' DataFrame. This will be used later to create a geographic map chart. Also, uses 'dropna()' function to remove NaN values to prevent geographic chart from showing wrong colours due to NaN values.
    return df, df_geo

def geo_data_func(df, df_ISO_codes): # formats data that will be used later to create geographical map chart
    if data_frequency == 1:
        df_geo = df
    elif data_frequency == 2 or data_frequency == 3:
        df_geo = pd.merge(df, df_ISO_codes, on ='Country', how ='left').dropna() # add 'ISO3 Code' column to 'df_geo' DataFrame. This will be used later to create a geographic map chart. Also, uses 'dropna()' function to remove NaN values to prevent geographic chart from showing wrong colours due to NaN values.
    df_geo = df_geo.sort_values('Date').groupby('Country').tail(1) # filter to show the latest (by 'Date' column) value per country
    df_geo = df_geo.sort_values('Price (EUR/MWhe)') # sort by values
    return df_geo


def line_chart_func(df, title): # creates chart of the latest daily or latest average monthly/yearly prices by country
    fig = px.line(df, 
        x=df['Date'],
        y=df['Price (EUR/MWhe)'],
        color=df['Country'],
        title=title,
        height=500, 
        width=900,
        template='plotly_dark'
        )  # charts the data
    fig.update_layout(yaxis=dict(title='')) # replace default title with a custom title in 'title' variable
    #fig.show() # I disabled it and replaced it with 'st.plotly_chart(fig)' below. Otherwise, charts would open in new browser tabs rather than being shown within the Streamlit page
    st.plotly_chart(fig)

# create geographic map of the latest daily or latest average monthly/yearly prices by country
def geo_map_func(df, title):
    fig = px.choropleth(df,
                            locations='ISO3 Code',
                            projection='orthographic',
                            color='Price (EUR/MWhe)',
                            title=title,
                            height=500, 
                            width=900,
                            color_continuous_scale=['green', 'white', 'red'],
                            #color_continuous_scale=px.colors.sequential.Viridis,
                            #color_continuous_scale='Bluered_r',
                            scope='europe', # limit the map to showing European countries only
                            hover_name='Country',
                            hover_data=['Country', 'Price (EUR/MWhe)']
    )
    #fig.show() # I disabled it and replaced it with 'st.plotly_chart(fig)' below. Otherwise, charts would open in new browser tabs rather than being shown within the Streamlit page
    st.plotly_chart(fig)

def download_or_view_data_func(df, unique_key): # creates . Uses 'unique_key' as input in order to avoid error in Streamlit.
    col1, col2 = st.columns([3,1])
    with col1: # creates button to view data as a table if button is pressed
        if st.button("View data as table", key=unique_key):
            st.dataframe(df)
    with col2: # creates button to export data to CSV
        st.download_button('Export to CSV', 
                            df.to_csv(),
                            file_name='output_table.csv',
                            mime='text/csv'
                            )


# downloads source data from CSV into DataFrame
df = pd.read_csv('european_wholesale_electricity_price_data_daily-4.csv') # copy CSV file downloaded from https://ember-climate.org/app/uploads/2022/09/european_wholesale_electricity_price_data_daily-4.csv into 'df' DataFrame into the same directory as this python file


# Streamlit script to turn this python script into wewb app
# instructions here: https://www.youtube.com/watch?v=Sb0A9i6d320

st.set_page_config(page_title='European spot power prices (EUR/MWh)', 
                    page_icon=":bar_chart:", 
                    layout='wide'
) # creates page config file for streamlit web app

# Select data to chart
st.sidebar.header('Change settings here:') # creates sidebar to select which measures to display, with default selection being 'temp', 'wind_speed', 'precipitation'
select_frequency = st.sidebar.radio('Select frequency',
                                options=('Daily', 'Monthly', 'Yearly'),
                                )
select_region = st.sidebar.radio('Select countries',
                                options=('All countries', 'Selected countries')
                                )
select_countries = []
if select_region == 'Selected countries':
    select_countries = st.sidebar.multiselect("Which countries?",
                                            options=df['Country'].unique(),
                                            default=['Germany', 'France', 'Italy']
                                            )



# Assigns values to 'data_frequency' and 'country_coverage' variables based on streamlit selection. Also updates initial 'country_list' variably based on streamlit selection

if select_frequency == 'Yearly':
    data_frequency = 3 # Enter 1 (daily prices), 2 (monthly average prices), 3 (yearly average prices)
elif select_frequency == 'Monthly':
    data_frequency = 2 # Enter 1 (daily prices), 2 (monthly average prices), 3 (yearly average prices)
elif select_frequency == 'Daily':
    data_frequency = 1 # Enter 1 (daily prices), 2 (monthly average prices), 3 (yearly average prices)
if select_region == 'All countries':
    country_coverage = 1 # Enter 1 (all countries), 2 (specific countries that need to be listed in 'country_list' variable below)
elif select_region == 'Selected countries':
    country_coverage = 2 # Enter 1 (all countries), 2 (specific countries that need to be listed in 'country_list' variable below)
country_list = select_countries # for use when user wants to import data for certain countries (i.e. option 2 in 'country_coverage')



# Runs functions to format & chart data

time_series_data = time_series_data_func(df, country_list)
time_series_chart = line_chart_func(time_series_data[0], 'Spot power prices (EUR/MWh)')
download_or_view_data = download_or_view_data_func(time_series_data[0], 1)
geo_map= geo_map_func(time_series_data[1], 'Spot power prices (EUR/MWh)')
download_or_view_data = download_or_view_data_func(time_series_data[1], 2)
pct_chg_data = pct_chg_data_func(time_series_data[0], time_series_data[2])
pct_chg_data_chart = line_chart_func(pct_chg_data[0], 'Spot power prices (YoY % Change)')
download_or_view_data = download_or_view_data_func(pct_chg_data[0], 3)
pct_geo_map= geo_map_func(pct_chg_data[1], 'Spot power prices (YoY % Change)')
download_or_view_data = download_or_view_data_func(pct_chg_data[1], 4)



st.markdown('---') # to draw solid line on streamlit page
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_st_style, unsafe_allow_html=True) # hides streamlit icons and logo from our web app