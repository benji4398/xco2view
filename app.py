import streamlit as st
import pandas as pd
import numpy as np

import netCDF4
import datetime
import glob


st.set_page_config(page_title="XCO2 View", page_icon="🌍")

st.title('Carbon Dioxide Dry Column-Averaged Mixing Ratios from Karlsruhe')

st.markdown("""
 * Use the menu at left to select data and set plot parameters
""")


DATE_COLUMN = 'time'
XCO2_COLUMN = 'xco2'

@st.cache
def get_filelist():
    filelist = glob.glob("data/*.nc")
    return filelist

@st.cache
def load_data(datafile):
    nc = netCDF4.Dataset(datafile)
    data = df = pd.DataFrame(nc[XCO2_COLUMN][...],
                  columns=[XCO2_COLUMN],
                  index=list(map(datetime.datetime.fromtimestamp,nc[DATE_COLUMN][...].data)))
    return data

filelist = get_filelist()

st.sidebar.markdown("## Select Data")

chosen_file = st.sidebar.selectbox('Select File', filelist)

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')
# Load data into the dataframe.
data = load_data(chosen_file)
# Notify the reader that the data was successfully loaded.
data_load_state.text('Loading data...done!')

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

# -- Create sidebar for plot controls
st.sidebar.markdown('## Set Plot Parameters')

time_min_value = data.index[0].to_pydatetime()
time_max_value = data.index[-1].to_pydatetime()
timerange = st.sidebar.slider('Time range', min_value=time_min_value,
                              max_value=time_max_value, value=(time_min_value,time_max_value))

mask = (data.index >= timerange[0]) & (data.index <= timerange[-1])
st.line_chart(data.loc[mask])