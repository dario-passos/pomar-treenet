import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

import influxdb_client
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
import numpy as np
import datetime

# import ssl
import urllib3
import certifi

# def custom_legend_name(new_names):
    # for i, new_name in enumerate(new_names):
        # fig.data[i].name = new_name




def read_data():
    org = "ceot"
    token = "HQuhjRudPv_fmY-tEvCvaPapbKL4paqydZUdxgTELMjWok3NHpDlpGDPzNgisAUz1nonYbg96ClO5CDgLS9HcQ=="
    # Store the URL of your InfluxDB instance
    url="https://23.88.101.43:8086"

    #### SECÇÃO DEDICADA A ULTRAPASSAR A CERTIFICAÇÃO DO HTTPS
    http = urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED",
        ca_certs=certifi.where()
    )
    resp = http.request('GET', 'https://us-west-2-1.aws.cloud2.influxdata.com/ping')
    #####


    client = influxdb_client.InfluxDBClient(
       url=url,
       token=token,
       org=org,
       ssl_ca_cert=certifi.where(), ### NO HTTPS
       verify_ssl=False             ### NO HTTPS
       )


    # _start = int(datetime.datetime(2022,3,12,7,30,0, tzinfo=None).timestamp())
    # _stop = int(datetime.datetime(2022,3,12,16,40,0, tzinfo=None).timestamp())
    
    
    ## query trees sensor data
    query = f'''from(bucket:"Arvores")
      |> range(start:-5d)
      |> filter(fn: (r) => r._measurement == "device_frmpayload_data_Hum_SHT" or 
                r._measurement == "device_frmpayload_data_ILL_lux" or 
                r._measurement == "device_frmpayload_data_TempC_SHT")
      |> filter(fn: (r) => r._field == "value")
      '''
    
    ## query trees ensor data for last hour
    query_now = f'''from(bucket:"Arvores")
      |> range(start:-30m)
      |> filter(fn: (r) => r._measurement == "device_frmpayload_data_Hum_SHT" or 
                r._measurement == "device_frmpayload_data_ILL_lux" or 
                r._measurement == "device_frmpayload_data_TempC_SHT")
      |> filter(fn: (r) => r._field == "value")
      '''  
      
    # ## query soil sensors
    # query_solo = f'''from(bucket:"Solo")
    #   |> range(start:{_start})
    #   |> filter(fn: (r) => r._measurement == "device_frmpayload_data_water_SOIL" or 
    #                      r._measurement == "device_frmpayload_data_conduct_SOIL" or 
    #                      r._measurement == "device_frmpayload_data_tem_SOIL")
    #   |> filter(fn: (r) => r._field == "value")
    # '''
    
    ## query soil sensors for last hour
    query_solo_now = f'''from(bucket:"Solo")
      |> range(start:-30m)
      |> filter(fn: (r) => r._measurement == "device_frmpayload_data_water_SOIL" or 
                r._measurement == "device_frmpayload_data_conduct_SOIL" or 
                r._measurement == "device_frmpayload_data_temp_SOIL")
      |> filter(fn: (r) => r._field == "value")
    '''
      
    query_meteo_now =  f'''from(bucket: "Weather-Station")
        |> range(start: -15m)
        |> filter(fn: (r) => r._measurement == "device_frmpayload_data_DAYRAIN" or 
                  r._measurement == "device_frmpayload_data_OUTSIDETEMPERATURE" or 
                  r._measurement == "device_frmpayload_data_OUTSIDEHUMIDITY" or 
                  r._measurement == "device_frmpayload_data_PRESSURE" or 
                  r._measurement == "device_frmpayload_data_SOLARADIATION" or
                  r._measurement == "device_frmpayload_data_TENMINUTESAVGWINDSPEED" or 
                  r._measurement == "device_frmpayload_data_WINDDIRECTION" or 
                  r._measurement == "device_frmpayload_data_WINDSPEED")
        |> filter(fn: (r) => r._field == "value")
        '''
    ## Query the data -------------------------------------------------------------
    query_api = client.query_api()
    
    ## Make the query and retrieve data into dataframe
    df = client.query_api().query_data_frame(org=org, query=query)
    df_now = client.query_api().query_data_frame(org=org, query=query_now)
    # df_solo = client.query_api().query_data_frame(org=org, query=query_solo)
    df_solo_now = client.query_api().query_data_frame(org=org, query=query_solo_now)
    df_meteo_now = client.query_api().query_data_frame(org=org, query=query_meteo_now)
    
    return df, df_now, df_solo_now, df_meteo_now


##################### Create the Dash app #####################################
app = dash.Dash(__name__)
server = app.server


## Set up the app layout ------------------------------------------------------

## Writing the layout like this allows for the app to refresh values at page load
def serve_layout():
    return  html.Div([
                html.Div(children=[
                    html.Img(src=app.get_asset_url('ceot-logo2.png'),
                             style={'width':'445', 'height':'62'}),
                    html.H2(children='Experimental Tree Orange Sensor Network (Paderne)')
                    ]),
                html.Div(className='top row',
                         children=[
                             html.Div(className='6 columns div sensors',
                                      children=[
                                          html.H3(children='Valores médios agora'),
                                          html.P(id='texto_tree_time', children=[]),
                                          html.P(id='texto_temp',children=[]),
                                          html.P(id='texto_hum',children=[]),
                                          html.P(id='texto_lum',children=[]),
                                          html.P(id='texto_soil_water',children=[]),
                                          html.P(id='texto_soil_temp',children=[])
                                       ],
                                      style={
                                      'margin-left':'10px',
                                      'width':'30%',
                                      'vertical-align':'text-top',
                                      'text-align':'left',
                                      'font-family': 'sans-serif',
                                      'display':'inline-block',
                                      'border-width':'0px',
                                      'border-style':'solid',
                                      'border-color':'black'
                                      }),
                             html.Div(className='6 columns div meteo',
                                      children=[
                                          html.H3(children='Condições meteorológicas agora'),
                                          html.P(id='texto_meteo_time',children=[]),
                                          html.P(id='texto_meteo_temp',children=[]),
                                          html.P(id='texto_meteo_hum',children=[]),
                                          html.P(id='texto_meteo_lum',children=[]),  
                                          html.P(id='texto_meteo_press',children=[]),
                                          html.P(id='texto_meteo_rain',children=[]),
                                          html.P(id='texto_meteo_wind',children=[]),
                                          html.P(id='texto_meteo_wind_dir',children=[]),
                                          html.P(id='texto_meteo_wind_10min',children=[])
                                          ],style={
                                          'margin-left':'30px',
                                          'width':'60%',
                                          'vertical-align':'text-top',
                                          'font-family': 'sans-serif',
                                          'text-align':'left',
                                          'display':'inline-block',
                                          'border-width':'0px',
                                          'border-style':'solid',
                                          'border-color':'black'
                                          }),
                                html.Br()
                             ]),
                 html.Div([html.Hr(),
                         html.Div(className='left div',
                                  children=[
                                      html.Br(),
                                      dcc.Dropdown(id='select_sensor',
                                                   options=[{'label':i, 'value':i}
                                                            for i in ['L1','L2','L3','L4','L5','L6','L7','L8',
                                                                      'L9','L10','L11','L12','L13','L14','L15',
                                                                      'L16','L17','L18','L19','L20','L21','L22',
                                                                      'L23','L24','L25']],
                                                   value='L1')
                                      ],style={
                                      'margin-left':'10px',
                                      'width':'10%',
                                      'font-family': 'sans-serif',
                                      'vertical-align':'text-top',
                                      'text-align':'left',
                                      'display':'inline-block'
                                      }),
                         html.Div(className='right div',
                                  children=[
                                      # html.H1(children='Temperatura (ºC)', style={'text-align': 'center '}),
                                      dcc.Graph(id='Temperatura-graph', figure={}, style={'height':'40vh', 'width':'70vw'}),
                                      # html.H1(children='Humidade relativa do ar (RH%)', style={'text-align': 'center '}),
                                      dcc.Graph(id='Humidade-graph', figure={},style={'height':'40vh', 'width':'70vw'}),
                                      # html.H1(children='Luminosidade (lux)', style={'text-align': 'center '}),
                                      dcc.Graph(id='Luminosidade-graph', figure={},style={'height':'40vh', 'width':'70vw'})
                                      ],
                                  style={
                                      'margin-left':'10px',
                                      'width':'75%',
                                      'font-family': 'sans-serif',
                                      'vertical-align':'text-top',
                                      'text-align':'left',
                                      'display':'inline-block'
                                      })
                                  ])
                 ]
        )
                   
# df, df_now, df_solo_now, df_meteo_now = read_data()    

app.layout = serve_layout()

## setup the callback function
@app.callback(
    [Output(component_id = 'texto_tree_time', component_property='children'),
     Output(component_id = 'texto_temp', component_property='children'),
     Output(component_id = 'texto_hum', component_property='children'),
     Output(component_id = 'texto_lum', component_property='children'),
     Output(component_id = 'texto_soil_water', component_property='children'),
     Output(component_id = 'texto_soil_temp', component_property='children'),
     Output(component_id = 'texto_meteo_time', component_property='children'),
     Output(component_id = 'texto_meteo_temp', component_property='children'),
     Output(component_id = 'texto_meteo_hum', component_property='children'),
     Output(component_id = 'texto_meteo_lum', component_property='children'),
     Output(component_id = 'texto_meteo_press', component_property='children'),
     Output(component_id = 'texto_meteo_rain', component_property='children'),
     Output(component_id = 'texto_meteo_wind', component_property='children'),
     Output(component_id = 'texto_meteo_wind_dir', component_property='children'),
     Output(component_id = 'texto_meteo_wind_10min', component_property='children'),    
     Output(component_id = 'Temperatura-graph', component_property='figure'),
     Output(component_id = 'Humidade-graph', component_property='figure'),
     Output(component_id = 'Luminosidade-graph', component_property='figure')],
    [Input(component_id = 'select_sensor', component_property = 'value')]
)




def update_output(device_name):
    
    ## Make the query and retrieve data into dataframe  
    df, df_now, df_solo_now, df_meteo_now = read_data()
    
    filtered_device_temp = df[(df['device_name'] == device_name) & 
                              (df['_measurement']=='device_frmpayload_data_TempC_SHT')]
    filtered_device_mean_temp = df[(df['device_name'] == device_name) & 
                              (df['_measurement']=='device_frmpayload_data_TempC_SHT')]
    
    fig_temperatura = px.area(filtered_device_temp,
                       x='_time', y='_value',
                       color='device_name',
                       title=f'Temperatura: {device_name}',
                       markers=True,
                       labels={'_time':'Time','_value':'Temperatura (ºC)'},
                       line_shape='spline',
                       template="none",
                       width=900,
                       height=400)

    
    filtered_device_hum = df[(df['device_name'] == device_name) & 
                             (df['_measurement']=='device_frmpayload_data_Hum_SHT')]
    fig_humidade = px.area(filtered_device_hum,
                       x='_time', y='_value',
                       color='device_name',
                       title=f'Humidade: {device_name}',
                       labels={'_time':'Time','_value':'Humidade (%RH)'},
                       markers=True,
                       line_shape='spline',
                       template="none",
                       width=900,
                       height=400)
    
    filtered_device_lum = df[(df['device_name'] == device_name) & 
                             (df['_measurement']=='device_frmpayload_data_ILL_lux')]
    fig_luminosidade = px.area(filtered_device_lum,
                       x='_time', y='_value',
                       color='device_name',
                       title=f'Luminosidade: {device_name}',
                       labels={'_time':'Time','_value':'Luminosidade (lux)'},
                       markers=True,
                       line_shape='spline',
                       log_y=False,
                       template="none",
                       width=900,
                       height=400)
    ## Calcular as
    last_tree_time = df_now['_time'].max()
    temp_media = df_now[df_now['_measurement']=='device_frmpayload_data_TempC_SHT']['_value'].mean()
    hum_media = df_now[df_now['_measurement']=='device_frmpayload_data_Hum_SHT']['_value'].mean()
    lum_media = df_now[df_now['_measurement']=='device_frmpayload_data_ILL_lux']['_value'].mean()
    
    soil_water_media = df_solo_now[df_solo_now['_measurement']=='device_frmpayload_data_water_SOIL']['_value'].mean()
    soil_temp_media = df_solo_now[df_solo_now['_measurement']=='device_frmpayload_data_temp_SOIL']['_value'].mean()
    
    meteo_time = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_OUTSIDETEMPERATURE']['_time'].values[0]
    meteo_temp = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_OUTSIDETEMPERATURE']['_value'].values[0]
    meteo_hum = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_OUTSIDEHUMIDITY']['_value'].values[0]
    meteo_lum = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_SOLARADIATION']['_value'].values[0]
    meteo_press = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_PRESSURE']['_value'].values[0]
    meteo_rain = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_DAYRAIN']['_value'].values[0]
    meteo_wind = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_WINDSPEED']['_value'].values[0]
    meteo_wind_dir = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_WINDDIRECTION']['_value'].values[0]
    meteo_wind_10min = df_meteo_now[df_meteo_now['_measurement']=='device_frmpayload_data_TENMINUTESAVGWINDSPEED']['_value'].values[0]
    
    text_tree_time = 'Hora da última medida: {}, {}'.format(str(last_tree_time.date())[:10], 
                                               str(last_tree_time.time())[:8])
    text_temp = 'Temperatura media: {:.2f} ºC'.format(temp_media)
    text_hum = ' Humidade media: {:.2f} %RH '.format(hum_media)
    text_lum = 'Luminosidade media: {:.2f} lux'.format(lum_media)
    text_water_soil = 'Humidade media do solo: {:.2f} %'.format(soil_water_media)
    text_temp_soil = 'Temperatura media do solo (a 15 cm) prof.: {:.2f} ºC'.format(soil_temp_media)
    text_meteo_time = 'Dia/hora: {}, {}'.format(np.datetime_as_string(meteo_time, unit='D'), 
                                               np.datetime_as_string(meteo_time, unit='s')[11:])
    text_meteo_temp = 'Temperatura: {:.2f} ºC'.format(meteo_temp)
    text_meteo_hum = 'Humidade: {:.2f} %'.format(meteo_hum)
    text_meteo_lum = 'Radiação solar: {:.2f} W/m^2'.format(meteo_lum)
    text_meteo_press = 'Pressão atmosférica: {:.2f} hPa'.format(meteo_press)
    text_meteo_rain = 'Precipitação: {:.2f} mm/h'.format(meteo_rain)
    text_meteo_wind = 'Velocidade do vento: {:.2f} m/s'.format(meteo_wind)
    text_meteo_wind_dir = 'Direção do vento: {:.2f} º (360=N, 270=W, 180=S, 90=E) '.format(meteo_wind_dir)
    text_meteo_wind_10min = 'Velocidade média do vento (10 min): {:.2f} m/s'.format(meteo_wind_10min)
    
    
    
    return text_tree_time, text_temp, text_hum, text_lum, text_water_soil, text_temp_soil,\
           text_meteo_time, text_meteo_temp, text_meteo_hum, text_meteo_lum, text_meteo_press,\
           text_meteo_rain, text_meteo_wind, text_meteo_wind_dir, text_meteo_wind_10min,\
           fig_temperatura, fig_humidade, fig_luminosidade



# Run local server
if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(debug=True)
















  