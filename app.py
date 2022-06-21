import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

import netCDF4
import datetime
import glob


st.set_page_config(page_title="XCO2 View", page_icon="🌍")

st.title('Carbon Dioxide Dry Column-Averaged Mixing Ratios from Karlsruhe')

st.markdown("""
 * Use the menu at left to select data and set plot parameters
""")


DATE_COLUMN = 'time'
XCO2_COLUMN = 'xco2_ppm'

def serial_date_to_string(srl_no):
    new_date = datetime.datetime(1970,1,1,0,0) + datetime.timedelta(srl_no - 1)
    return new_date.strftime("%Y-%m-%d")

@st.cache
def get_filelist():
    filelist = glob.glob("data/*.nc")
    return filelist

@st.cache
def load_data(datafile):
    nc = netCDF4.Dataset(datafile)
    # data =  pd.DataFrame(nc[XCO2_COLUMN][...],
    #     columns=[XCO2_COLUMN],
    #     index=list(map(datetime.datetime.fromtimestamp,nc[DATE_COLUMN][...].data)))
    data = pd.DataFrame(nc[XCO2_COLUMN][...],columns=["Karlsruhe"],
                        index=pd.to_datetime(list(map(serial_date_to_string,nc[DATE_COLUMN][...]))))
    nc.close()

    daily = data.groupby(pd.Grouper(freq='1D')).mean()

    mauna = pd.read_table('data/co2_mlo_surface-insitu_1_ccgg_DailyData.txt',sep=" ",comment="#")
    df_mauna = pd.DataFrame({"date": pd.to_datetime(mauna[["year","month","day"]]), "xco2": mauna["value"]})
    df_mauna.index = df_mauna.date
    df_mauna.drop(columns="date",inplace=True)
    df_mauna[df_mauna.xco2 < 0] = np.nan
    
    daily["Mauna Loa"] = df_mauna["2010-04-18":"2020-11-29"]
    return data, daily

filelist = get_filelist()

st.sidebar.markdown("## Select Data")

chosen_file = st.sidebar.selectbox('Select File', filelist)

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')
# Load data into the dataframe.
data, daily = load_data(chosen_file)
# Notify the reader that the data was successfully loaded.
data_load_state.text('Loading data...done!')

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

# -- Create sidebar for plot controls
st.sidebar.markdown('## Set Plot Parameters')

time_min_value = daily.index[0].to_pydatetime()
time_max_value = daily.index[-1].to_pydatetime()
timerange = st.sidebar.slider('Time range', min_value=time_min_value,
                              max_value=time_max_value, value=(time_min_value,time_max_value),
                              step=datetime.timedelta(days = 1 ))

mask = (daily.index >= timerange[0]) & (daily.index <= timerange[-1])

karlsruhe = st.sidebar.checkbox("Karlsruhe",value=True)
mauna_loa = st.sidebar.checkbox("Mauna Loa",value=True)

st.markdown("""
## XCO2 Data
""")
# st.line_chart(daily.loc[mask])
source = daily.loc[mask].reset_index().melt("index",var_name="location",value_name="xco2")
if not karlsruhe:
    source = source[source.location != "Karlsruhe"]
if not mauna_loa:
    source = source[source.location != "Mauna Loa"]

nearest = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['index'], empty='none')

c = alt.Chart(source).mark_line().encode(
    x=alt.X("index", axis=alt.Axis(title="date")),
    y=alt.Y("xco2", axis=alt.Axis(title="xco2 [ppm]"), scale=alt.Scale(zero=False)),
    color=alt.Color("location", legend=alt.Legend(title="Location"),
        scale=alt.Scale(scheme='dark2')
    ),
)
selectors = alt.Chart(source).mark_point().encode(
    x='index',
    opacity=alt.value(0),
).add_selection(
    nearest
)

points = c.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)
text = c.mark_text(align='left', dx=5, dy=-30).encode(
    text=alt.condition(nearest, 'xco2', alt.value(' '))
)
rules = alt.Chart(source).mark_rule(color='lightgray').encode(
    x='index',
).transform_filter(
    nearest
)


st.altair_chart((
    c+selectors+points+rules+text
    ).configure_mark(
        opacity=0.7
    ).interactive(), use_container_width=True)

#st.write(source)

# data_re = data.copy()
# data_re.loc[data_re['xco2'] <= 0] = np.NaN
# series = data_re['xco2'].resample('2min').mean().to_frame()

# st.markdown("""
# ## XCO2 Resampled Data
# """)
# st.line_chart(series[timerange[0]:timerange[-1]])
