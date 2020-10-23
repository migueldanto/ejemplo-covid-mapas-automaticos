#!/usr/bin/env python
# coding: utf-8

# # Hacer mapas automatizados

# In[ ]:


#descargando los datos de covid de mexico
import requests
import zipfile,io
save_path="data/"
chunk_size=128
res=requests.get("http://datosabiertos.salud.gob.mx/gobmx/salud/datos_abiertos/datos_abiertos_covid19.zip",stream=True)
print(res.status_code)
if(res.status_code==200):
    z = zipfile.ZipFile(io.BytesIO(res.content))
    z.extractall(save_path)


# In[ ]:


#obteniendo el ultimo archivo, en caso de que en el directorio haya mas
import glob
import os

list_of_files = glob.glob(save_path+"*COVID19MEXICO.csv")
latest_file = max(list_of_files, key=os.path.getctime)
print(latest_file)


# In[ ]:


#leyendo los datos en un pandas dataframe
import pandas as pd
covid_df=pd.read_csv(latest_file,encoding="iso-8859-1",dtype={"ENTIDAD_RES":object,"MUNICIPIO_RES":object})
covid_df["CVEGEOMUN"]=covid_df["ENTIDAD_RES"]+covid_df["MUNICIPIO_RES"]
covid_df["caso"]=1
covid_df


# In[ ]:


#filtrando solo los casos confirmados
casos_confirmados=covid_df[(covid_df["CLASIFICACION_FINAL"]==1)|(covid_df["CLASIFICACION_FINAL"]==2)|(covid_df["CLASIFICACION_FINAL"]==3)]
casos_confirmados


# In[ ]:


#agrupando los casos confirmados por estado
confirmados_x_estado=casos_confirmados[["ENTIDAD_RES","CLASIFICACION_FINAL"]].groupby(by="ENTIDAD_RES").count().reset_index()
confirmados_x_estado.rename(columns={"CLASIFICACION_FINAL":"confirmados"},inplace=True)
#leyendo el shapefile y haciendo el join
import geopandas as geopd
estados=geopd.GeoDataFrame.from_file("capas_base/estados_inegi_2019/estados_inegi_2019.shp")
estados_confirmados=estados.merge(confirmados_x_estado,left_on="cvegeo",right_on="ENTIDAD_RES",how="inner")
estados_confirmados.head()


# In[ ]:


#obtener la fecha para ponerla en el mapa
import locale
locale.setlocale(locale.LC_TIME, '')
from datetime import date
today = date.today()
fecha_actual=today.strftime("%d de {} del %Y").format(today.strftime("%B").title())
fecha_para_archivos=today.strftime("%d-%m-%Y")
print(fecha_para_archivos)
fecha_actual


# ### Ahora si a hacer el mapa

# In[ ]:


import matplotlib.pyplot as plt

fig1, ax1 = plt.subplots(figsize=(10,7),dpi=150)
estados_confirmados.plot(ax=ax1,column="confirmados",cmap="OrRd",
                         legend=True,scheme="quantiles",edgecolor="lightgray",
                         legend_kwds={"title":"Casos confirmados"})
ax1.set_title("Casos confirmados de coronavirus en México\n"+fecha_actual)
ax1.axis('off')

ax1.text(0.0, 0.0, 'Fuente: Secretaria de Salud. DGE.', horizontalalignment='left',verticalalignment='center',
         transform=ax1.transAxes,fontsize=9)

fig1.savefig("salidas/"+fecha_para_archivos+"-NACIONAL.jpg",format="jpg")
plt.show()


# ### ahora a hacer uno por cada estado

# In[ ]:


#agrupando los casos confirmados por municipio
confirmados_x_municipio=casos_confirmados[["CVEGEOMUN","CLASIFICACION_FINAL"]].groupby(by="CVEGEOMUN").count().reset_index()
confirmados_x_municipio.rename(columns={"CLASIFICACION_FINAL":"confirmados"},inplace=True)
#leyendo el shapefile y haciendo el join
municipios=geopd.GeoDataFrame.from_file("capas_base/municipios_inegi_2019/municipios_inegi_2019.shp")
municipios["cve_ent"]=municipios["cvegeo"].apply(lambda x:x[:2])
municipios_confirmados=municipios.merge(confirmados_x_municipio,left_on="cvegeo",right_on="CVEGEOMUN",how="inner")
municipios_confirmados.head()


# In[ ]:


def mapea1estado(cve_edo):
    filtro_mun=municipios_confirmados[municipios_confirmados["cve_ent"]==cve_edo]
    nom_edo=filtro_mun.iloc[0]["nom_ent"]
    fig2, ax2 = plt.subplots(figsize=(10,7),dpi=150)
    filtro_mun.plot(ax=ax2,column="confirmados",cmap="OrRd",
                         legend=True,scheme="quantiles",edgecolor="lightgray",
                         legend_kwds={"fontsize":6})
    ax2.set_title("Casos confirmados de coronavirus en "+nom_edo+"\n"+fecha_actual)
    
    ax2.axis('off')

    ax2.text(0.0, 0.0, 'Fuente: Secretaria de Salud. DGE.', horizontalalignment='left',verticalalignment='center',
         transform=ax2.transAxes,fontsize=9)

    fig2.savefig("salidas/"+fecha_para_archivos+"-estado"+cve_edo+".jpg",format="jpg")
    plt.close()
    
#mapea1estado("15")
for i in range(1,33):
    clave_edo="{:02}".format(i)
    print(clave_edo+", mapa terminado")
    mapea1estado(clave_edo)


# ### un ejemplo mas... informacion de los 10 muns mas altos 

# In[ ]:


lista_top10=municipios_confirmados.sort_values(by="confirmados",ascending=False)[["geometry","cvegeo","nom_ent","nom_mun","confirmados"]].head(10)
lista_top10


# In[ ]:


import matplotlib.dates as mdates
#%matplotlib inline
import seaborn as sns
sns.set_style("whitegrid")

def ficha_municipio(row,idx=0):
    fig3, ax3 = plt.subplots(2,2,figsize=(10,7),dpi=150)
    data_mun=covid_df[ (covid_df["CVEGEOMUN"]==row["cvegeo"]) & ( (covid_df["CLASIFICACION_FINAL"]==1)|(covid_df["CLASIFICACION_FINAL"]==2)|(covid_df["CLASIFICACION_FINAL"]==3) ) ]
    #el municipio
    municipios_confirmados.plot(ax=ax3[0][0],column="confirmados",cmap="OrRd")
    minx, miny, maxx, maxy = row.geometry.bounds
    ax3[0][0].set_xlim(minx,maxx)
    ax3[0][0].set_ylim(miny,maxy)
    
    ax3[0][0].set_aspect(aspect="equal",adjustable="box",anchor="C")
    ax3[0][0].axis('off')
    ax3[0][0].set_title(row["nom_mun"]+", "+row["nom_ent"])
    
    #rgafica de hombres y mujeres en ese municipio
    data_mun["Sexo"]=data_mun["SEXO"].apply(lambda x:"Hombre" if x==2 else "Mujer")
    sns.countplot(data=data_mun,x="Sexo",
                ax=ax3[0][1])
    ax3[0][1].set_title("Casos confirmados por sexo")
    ax3[0][1].set_xlabel("")
    
    #grafica de avance de dias
    avance=data_mun[["FECHA_INGRESO","caso"]].groupby("FECHA_INGRESO").count().reset_index().sort_values(by="FECHA_INGRESO")
    avance["fecha"]=pd.to_datetime(avance["FECHA_INGRESO"])
    avance["acum"]=avance["caso"].cumsum()
    sns.lineplot(data=avance,x="fecha",y="caso",ax=ax3[1][0],color="#ad0909")
    
    locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
    formatter = mdates.ConciseDateFormatter(locator)
    ax3[1][0].xaxis.set_major_locator(locator)
    ax3[1][0].xaxis.set_major_formatter(formatter)
    
    ax3[1][0].set_title("Casos confirmados por fecha de ingreso")
    
    #grafica de avance de dias acumulado
    
    sns.lineplot(data=avance,x="fecha",y="acum",ax=ax3[1][1],color="#ad0909")
    
    ax3[1][1].xaxis.set_major_locator(locator)
    ax3[1][1].xaxis.set_major_formatter(formatter)
    ax3[1][1].set_title("Casos confirmados acumulados por fecha de ingreso")
    
    fig3.suptitle("Casos confirmados de Coronavirus en "+row["nom_mun"]+"\n"+"{:,}".format(row["confirmados"]))
    fig3.savefig("salidas/"+fecha_para_archivos+"-topmunicipal-"+str(idx)+"-"+row["cvegeo"]+".jpg",format="jpg")
    plt.close()

c=1
for i,row in lista_top10.iterrows():
    print("generando ficha "+row["nom_mun"])
    ficha_municipio(row,c)
    c=c+1
#ficha_municipio(lista_top10.iloc[1])


# In[ ]:




